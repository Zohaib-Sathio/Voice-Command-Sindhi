from fastapi import APIRouter, Request, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles

import json
import sys
import asyncio
import threading
from datetime import date, datetime, timezone
from typing import Annotated, Optional
from uuid import uuid4
import shutil
import time
import joblib
from pydantic import BaseModel

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.utils.response_models import CommandValidationResponse
from src.services.transcribe_audio import transcribe_audio, client
from src.services.amount_extraction import extract_amount_from_transcript
import os
from src.utils.helper_functions import sync_insert_transcription, sync_update_is_correct
from src.services.intent_classification import prediction_pipeline
from src.services.transliteration import get_prediction, check_if_urdu, check_if_sindhi
from src.utils.switch_pipeline import low_cost_priority
from src.services.s3_storage import upload_audio_file
from src.utils.logger import log, set_request_id, get_request_id
from src.utils.jwt import generate_jwt_token, validate_jwt_token, JWT_EXPIRATION_HOURS
from src.database.db_functions import get_user, create_user
from src.database.config import SessionLocal

router = APIRouter()


# ==================== Authentication Helper Functions ====================

def get_client_ip(request: Request) -> str:
    """
    Extracts client IP address from request.
    Checks X-Forwarded-For header for proxied requests.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded.split(",")[0].strip()
    # Fall back to direct client IP
    return request.client.host if request.client else "unknown"


# ==================== Pydantic Models ====================

class TokenRequest(BaseModel):
    """Request model for JWT token generation."""
    user_id: str  # Required user identifier


class TokenResponse(BaseModel):
    """Response model for JWT token generation."""
    success: bool
    token: str
    user_id: str
    expires_in: int  # Expiration time in seconds


class ValidateTokenResponse(BaseModel):
    """Response model for JWT token validation."""
    valid: bool
    user_id: Optional[str] = None
    message: str


# ==================== End of Authentication Helpers ====================


def background_upload_audio(file_content: bytes, file_key: str, content_type: str):
    """
    Wrapper function for uploading audio file to S3 in background.
    Ensures proper error handling and logging.
    This function is designed to run in FastAPI BackgroundTasks.
    """
    try:
        log(f"🚀 Background task started: Uploading {file_key} to S3", flush=True)
        sys.stdout.flush()
        result = upload_audio_file(file_content, file_key, content_type)
        if result:
            log(f"✅ Background task completed: Successfully uploaded {file_key}", flush=True)
        else:
            log(f"⚠️ Background task completed: Upload skipped (S3 not configured or failed)", flush=True)
        sys.stdout.flush()
    except Exception as e:
        log(f"❌ Background task failed: Error uploading {file_key} to S3: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        raise  # Re-raise to ensure FastAPI logs it

limiter = Limiter(key_func=get_remote_address, default_limits=["3/minute"])


templates = Jinja2Templates(directory="public")


# Global variables for loaded models
model = None
label_encoder = None
transliterations_model=None
trans_vectorizer=None
other_actions_model=None

# --- Load model once at startup ---
@router.on_event("startup")
def load_model():
    global model, label_encoder,transliterations_model,trans_vectorizer,other_actions_model
    # Startup logs don't need request ID
    print("🔄 Loading model and label encoder...")
    
    try:
        model = joblib.load("src/models/intent_classifier.pkl")
        print("✅ Intent classifier loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load intent classifier: {e}")
        model = None
    
    try:
        label_encoder = joblib.load("src/models/label_encoder.pkl")
        print("✅ Label encoder loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load label encoder: {e}")
        label_encoder = None
    
    try:
        transliterations_model = joblib.load("src/models/transliteration_classifier.pkl")
        print("✅ Transliteration classifier loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load transliteration classifier: {e}")
        transliterations_model = None
    
    try:
        trans_vectorizer = joblib.load("src/models/tfidf_vectorizer.pkl")
        print("✅ TF-IDF vectorizer loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load TF-IDF vectorizer: {e}")
        trans_vectorizer = None
    
    try:
        other_actions_model = joblib.load("src/models/xgboost_intent_model.joblib")
        print("✅other actions model loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load other actions model: {e}")
        other_actions_model = None
    
    # Check if all models loaded successfully
    if all([model, label_encoder, transliterations_model, trans_vectorizer, other_actions_model]):
        print("✅ All models loaded and ready for predictions!")
    else:
        print("⚠️ Some models failed to load. Application may not function properly.")



@router.get("/", response_class=HTMLResponse)
@limiter.limit("7/minute")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/v1/api/transcribe/command")
# @limiter.limit("6/minute")
async def validate_command(request: Request,
        background_tasks: BackgroundTasks,
        audio_file: UploadFile = File(...),
        beneficiary_list: str = Form(...),
        phone_number_list: str = Form(...),
        bills_type_list: str = Form(...),
        appId: str = Form(...),
        key: str = Form(...),
        packageName: str = Form(...),
        ):
    
    # Set request ID for this request context
    file_id = str(uuid4())
    set_request_id(file_id)
    
    file_extension = os.path.splitext(audio_file.filename)[1]
    log("File extension: ", file_extension)
    
    file_name = f"{file_id}{file_extension}"
    
    # Read file bytes to calculate size
    contents = await audio_file.read()
    size_kb = len(contents) / 1024
    log("File size:", round(size_kb, 2), "KB")

    if size_kb > 1500:
        raise HTTPException(status_code=400, detail="File size should be less than 1500 KB")

    # Rewind file handle so transcribe_audio can read it
    audio_file.file.seek(0)

    label=None
    detected_language="english"
    
    try:
        beneficiaries = json.loads(beneficiary_list)
        phone_contacts = json.loads(phone_number_list)  
        bill_types = json.loads(bills_type_list)
        # change the key from bankName to bank_name in beneficiaries
        for beneficiary in beneficiaries:
            beneficiary['bank_name'] = beneficiary.pop('bankName')
        log("Beneficiaries: ", beneficiaries)
        log("Phone contacts: ", phone_contacts)
        log("Bill types: ", bill_types)
        timer_1 = time.perf_counter()
        transcription = await transcribe_audio(audio_file)
        transcribed_text = transcription.text
        timer_2 = time.perf_counter()
        log("Time taken to transcribe audio: ", timer_2 - timer_1, "seconds")
        #labal =0 if transliteration ,1 if in urdu
        try:
            if check_if_sindhi(transcribed_text):
                detected_language = "urdu"
                log('Transcribed text is in Sindhi (treating as Urdu for processing).')
            elif check_if_urdu(transcribed_text):
                label= get_prediction(transliterations_model, trans_vectorizer, transcribed_text)
                detected_label= 'transliterations' if label == 0 else 'ur'
                log(f"Detected Label for Transliterations: {detected_label}")
                if label==0:
                    log('Transcribed text is in english transliteration in urdu.')
                    detected_language="english"
                else:
                    log('Transcribed text is in urdu.')
                    detected_language="urdu"
        except Exception as e:
            log(e)
        
        # Extract amount using intelligent multi-language converter
        log(f"Original transcription: {transcribed_text}")
        extraction_result = extract_amount_from_transcript(transcribed_text, detected_language)
        
        extracted_amount = extraction_result['amount']
        preprocessed_text = extraction_result['preprocessed_text']
        amount_source = extraction_result['source']
        language_mismatch = extraction_result['language_mismatch']
        actual_language = extraction_result['actual_language']
        
        if extracted_amount is not None:
            log(f"✓ Extracted amount: {extracted_amount} (source: {amount_source})")
            log(f"  Preprocessed text: {preprocessed_text}")
            
        else:
            log("✗ No amount found in transcript")
        
        # Use preprocessed text for GPT processing if needed
        # transcribed_text = preprocessed_text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
    

    try:
        log("Processing command validation with GPT...")

        
        log("Detected language in api endpoints: ", detected_language)
        data_dict = {
                "model": model,
                "label_encoder": label_encoder,
                "other_actions_model": other_actions_model,
                "file_name": file_name,
                "detected_language": detected_language,
                "transcribed_text": transcribed_text,
                "extracted_amount": extracted_amount,
                "preprocessed_text": preprocessed_text,
            }
            
        context_data = {
            "beneficiaries": beneficiaries,
            "phone_contacts": phone_contacts,
            "bill_types": bill_types,
        }
        log("Initial Extracted Amount: ", extracted_amount)

        primary_pipeline=True
        timer_3 = time.perf_counter()
        
        if primary_pipeline:
            
            response = await low_cost_priority(prediction_pipeline, data_dict, background_tasks, context_data)
            timer_4 = time.perf_counter()
            log("Time taken to get GPT response: ", timer_4 - timer_3, "seconds")
        

        
        try:
            command_data = json.loads(response)
            log("Final Extracted Amount: ", command_data["amount"])
            command_data['detected_language'] = detected_language
            
            # Ensure type is not empty - set to "unknown" if empty
            if not command_data.get("type") or command_data["type"].strip() == "":
                command_data["type"] = "unknown"
                log("⚠️ Empty type detected, setting to 'unknown'")
            
        
            log("Detected language: ", command_data["detected_language"])
            if command_data["type"] == "download_statement":
                if command_data['statement_period_month'] == "" and command_data['statement_period_year'] == "":
                    command_data['statement_period_month'] = str(datetime.now().strftime("%B"))
                    command_data['statement_period_year'] = str(datetime.now().year)
            
            log("Total time taken: ", timer_4 - timer_1, "seconds")
            
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}',response, re.DOTALL)
            if json_match:
                command_data = json.loads(json_match.group())
                command_data['detected_language'] = detected_language
                
                # Ensure type is not empty - set to "unknown" if empty
                if not command_data.get("type") or command_data["type"].strip() == "":
                    command_data["type"] = "unknown"
                    log("⚠️ Empty type detected, setting to 'unknown'")
                
               
                log("Detected language: ", command_data["detected_language"])
                if command_data["type"] == "download_statement":
                    if command_data['statement_period_month'] == "" and command_data['statement_period_year'] == "":
                        command_data['statement_period_month'] = str(datetime.now().strftime("%B"))
                        command_data['statement_period_year'] = str(datetime.now().year)
            else:
                raise HTTPException(
                    status_code=500,
                    detail="GPT returned invalid JSON format"
                )

        try:
            data_to_insert = {
                "file_id": file_name,
                "transcription_text": transcribed_text,
                "language": detected_language,
                "gpt_response": json.dumps(command_data),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            background_tasks.add_task(sync_insert_transcription, data_to_insert)
            
            # Upload to S3 in background (non-blocking)
            # Using asyncio.create_task since BackgroundTasks doesn't execute properly
            s3_key = f"audio_files/{file_name}"
            content_type = audio_file.content_type or "audio/webm"
            # Create a copy of contents to avoid closure issues - ensure bytes are copied
            file_contents = bytes(contents)  # Explicitly create a new bytes object
            log(f"📋 Scheduling background task for S3 upload: {s3_key} (size: {len(file_contents)} bytes)", flush=True)
            
            # Create async wrapper that runs the blocking upload in a thread pool
            async def fire_and_forget_upload():
                try:
                    # Small delay to ensure response is sent first
                    await asyncio.sleep(0.1)
                    await run_in_threadpool(background_upload_audio, file_contents, s3_key, content_type)
                except Exception as e:
                    log(f"❌ Fire-and-forget upload failed: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
            
            # Create task but don't await it (fire-and-forget)
            asyncio.create_task(fire_and_forget_upload())
            
            log(f"✅ Background task scheduled successfully", flush=True)
            
            log("Data inserted into MySQL database")
        except Exception as db_error:
            raise HTTPException(status_code=500, detail=f"Failed to save metadata to database: {db_error}")

        command_data["file_id"] = file_name
        
        # Ensure type is not empty - set to "unknown" if empty
        if not command_data.get("type") or command_data["type"].strip() == "":
            command_data["type"] = "unknown"
            log("⚠️ Empty type detected, setting to 'unknown'")
            
        if command_data["type"] == "download_statement" and command_data["type"] == "pay_bill" and command_data["amount"] is not None:
            command_data["amount"] = 0
            log(f"{command_data['type']} detected, setting amount to 0")
        
        if command_data.get("amount") is not None and command_data["amount"] < 0:
            command_data["amount"] = 0
            log("Amount is less than 0, setting to 0")
        if command_data.get("amount") is None:
            command_data["amount"] = 0
            log("Amount is None, setting to 0")
        log("Final Response: ", command_data)
        return CommandValidationResponse(**command_data)

    except Exception as processing_error:
        raise HTTPException(
            status_code=500,
            detail=f"Command processing failed: {str(processing_error)}"
        )
    
class TextCommandRequest(BaseModel):
    text: str
    beneficiary_list: list = []
    phone_number_list: list = []
    bills_type_list: list = []


@router.post("/v1/api/command/text")
# @limiter.limit("6/minute")
async def validate_text_command(request: Request, background_tasks: BackgroundTasks, body: TextCommandRequest):
    file_id = str(uuid4())
    set_request_id(file_id)
    file_name = f"{file_id}.txt"

    transcribed_text = body.text.strip()
    if not transcribed_text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    log(f"Text command received: {transcribed_text}")

    beneficiaries = body.beneficiary_list
    phone_contacts = body.phone_number_list
    bill_types = body.bills_type_list

    for beneficiary in beneficiaries:
        if "bankName" in beneficiary:
            beneficiary["bank_name"] = beneficiary.pop("bankName")

    detected_language = "english"

    try:
        if check_if_sindhi(transcribed_text):
            detected_language = "urdu"
            log("Text is in Sindhi (treating as Urdu for processing).")
        elif check_if_urdu(transcribed_text):
            label = get_prediction(transliterations_model, trans_vectorizer, transcribed_text)
            detected_label = "transliterations" if label == 0 else "ur"
            log(f"Detected Label for Transliterations: {detected_label}")
            if label == 0:
                detected_language = "english"
            else:
                detected_language = "urdu"
    except Exception as e:
        log(e)

    log(f"Original text: {transcribed_text}")
    extraction_result = extract_amount_from_transcript(transcribed_text, detected_language)

    extracted_amount = extraction_result["amount"]
    preprocessed_text = extraction_result["preprocessed_text"]
    amount_source = extraction_result["source"]

    if extracted_amount is not None:
        log(f"Extracted amount: {extracted_amount} (source: {amount_source})")
        log(f"  Preprocessed text: {preprocessed_text}")
    else:
        log("No amount found in text")

    try:
        log("Processing command validation with GPT...")
        log("Detected language: ", detected_language)

        data_dict = {
            "model": model,
            "label_encoder": label_encoder,
            "other_actions_model": other_actions_model,
            "file_name": file_name,
            "detected_language": detected_language,
            "transcribed_text": transcribed_text,
            "extracted_amount": extracted_amount,
            "preprocessed_text": preprocessed_text,
        }

        context_data = {
            "beneficiaries": beneficiaries,
            "phone_contacts": phone_contacts,
            "bill_types": bill_types,
        }
        log("Initial Extracted Amount: ", extracted_amount)

        timer_start = time.perf_counter()
        response = await low_cost_priority(prediction_pipeline, data_dict, background_tasks, context_data)
        timer_end = time.perf_counter()
        log("Time taken to get GPT response: ", timer_end - timer_start, "seconds")

        try:
            command_data = json.loads(response)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                command_data = json.loads(json_match.group())
            else:
                raise HTTPException(status_code=500, detail="GPT returned invalid JSON format")

        command_data["detected_language"] = detected_language
        command_data["file_id"] = file_name

        if not command_data.get("type") or command_data["type"].strip() == "":
            command_data["type"] = "unknown"
            log("Empty type detected, setting to 'unknown'")

        if command_data["type"] == "download_statement":
            if command_data["statement_period_month"] == "" and command_data["statement_period_year"] == "":
                command_data["statement_period_month"] = str(datetime.now().strftime("%B"))
                command_data["statement_period_year"] = str(datetime.now().year)

        if command_data.get("amount") is not None and command_data["amount"] < 0:
            command_data["amount"] = 0
            log("Amount is less than 0, setting to 0")
        if command_data.get("amount") is None:
            command_data["amount"] = 0
            log("Amount is None, setting to 0")

        try:
            data_to_insert = {
                "file_id": file_name,
                "transcription_text": transcribed_text,
                "language": detected_language,
                "gpt_response": json.dumps(command_data),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            background_tasks.add_task(sync_insert_transcription, data_to_insert)
        except Exception as db_error:
            log(f"Failed to save metadata to database: {db_error}")

        log("Final Response: ", command_data)
        return CommandValidationResponse(**command_data)

    except HTTPException:
        raise
    except Exception as processing_error:
        raise HTTPException(status_code=500, detail=f"Command processing failed: {str(processing_error)}")


@router.put("/update_record")
@limiter.limit("10/minute")
async def update_record(request: Request, file_id: str):
    try:
        result = await run_in_threadpool(sync_update_is_correct, file_id)
        return {"message": "Record updated successfully", "result": result}
    except Exception as supabase_error:
        raise HTTPException(status_code=500, detail=f"Failed to update the record: {supabase_error}")


@router.get("/health")
@limiter.limit("5/minute")
async def health_check(request: Request):
    try:
        _ = client.models.list()
        return {"status": "healthy", "openai_connection": "ok"}
    except Exception as e:
        return {"status": "failure", "openai_connection": "error", "error": str(e)}


# ==================== Authentication Endpoints ====================

@router.post("/v1/api/auth/generate-token", response_model=TokenResponse)
@limiter.limit("10/minute")
async def generate_token(request: Request, token_request: TokenRequest):
    """
    Generate JWT token for a user (internal endpoint).
    
    Flow:
    1. Extract user_id from request
    2. Check if user exists, create if not
    3. Generate JWT token
    4. Return token with expiration info
    """
    try:
        # Extract user_id from request
        user_id = token_request.user_id
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="user_id is required"
            )
        
        log(f"Token generation request for user: {user_id}")
        
        # Check if user exists, create if not
        db = SessionLocal()
        try:
            user = get_user(db, user_id)
            if user is None:
                # User doesn't exist, create new user
                result = create_user(db, user_id)
                if result.get("success"):
                    log(f"Created new user: {user_id}")
                else:
                    # User might have been created concurrently, check again
                    user = get_user(db, user_id)
                    if user is None:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to create user: {result.get('message', 'Unknown error')}"
                        )
            else:
                log(f"User already exists: {user_id}")
        finally:
            db.close()
        
        # Generate JWT token
        try:
            token = generate_jwt_token(user_id)
            expires_in_seconds = JWT_EXPIRATION_HOURS * 3600
            
            log(f"Successfully generated token for user: {user_id}")
            
            return TokenResponse(
                success=True,
                token=token,
                user_id=user_id,
                expires_in=expires_in_seconds
            )
        except Exception as e:
            log(f"Error generating JWT token: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate token: {str(e)}"
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        log(f"Unexpected error in generate_token: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/v1/api/auth/validate-token", response_model=ValidateTokenResponse)
@limiter.limit("20/minute")
async def validate_token(request: Request):
    """
    Public endpoint to validate a JWT token.
    
    Flow:
    1. Extract token from Authorization header
    2. Validate token using jwt.validate_jwt_token()
    3. Return validation result
    """
    try:
        # Extract token from Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            return ValidateTokenResponse(
                valid=False,
                user_id=None,
                message="Missing Authorization header"
            )
        
        if not authorization.startswith("Bearer "):
            return ValidateTokenResponse(
                valid=False,
                user_id=None,
                message="Invalid Authorization header format. Expected 'Bearer <token>'"
            )
        
        token = authorization.split(" ")[1] if len(authorization.split(" ")) > 1 else ""
        if not token:
            return ValidateTokenResponse(
                valid=False,
                user_id=None,
                message="Token not found in Authorization header"
            )
        
        # Validate token
        try:
            user_id = validate_jwt_token(token)
            return ValidateTokenResponse(
                valid=True,
                user_id=user_id,
                message="Token is valid"
            )
        except HTTPException as e:
            # Token validation failed (expired, invalid, etc.)
            return ValidateTokenResponse(
                valid=False,
                user_id=None,
                message=e.detail
            )
    
    except Exception as e:
        log(f"Unexpected error in validate_token: {e}")
        return ValidateTokenResponse(
            valid=False,
            user_id=None,
            message=f"Error validating token: {str(e)}"
        )


# ==================== End of Authentication Endpoints ====================

