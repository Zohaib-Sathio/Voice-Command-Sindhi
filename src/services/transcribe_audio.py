from src.utils.response_models import TranscriptionResponse, SUPPORTED_FORMATS
from fastapi.exceptions import HTTPException
from fastapi import UploadFile, File
from fastapi.concurrency import run_in_threadpool
import time

from openai import OpenAI

from dotenv import load_dotenv
import tempfile
import os

load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def transcribe_audio(
    audio_file: UploadFile = File(...),
    model: str = "gpt-4o-mini-transcribe",
):
    if audio_file.content_type not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail = f"Unsupported file format. Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )
    
    content = await audio_file.read()

    if len(content) > 1024 * 1024 * 2:
        raise HTTPException(
            status_code=400,
            detail="Audio file should be less than 2 MBs."
        )
    
    suffix = f".{audio_file.filename.split('.')[-1]}" if audio_file.filename else ".temp"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        def sync_transcribe():
            # Universal prompt for both Urdu and English
            prompt_text = (
                "If there is no speech in the audio, return empty text. "
                "CRITICAL: The audio may contain URDU or ENGLISH speech. "
                "Mentioned names are typically Pakistani names."
                "Transcribe the pakistani names in the audio correctly."
                "The audio is a financial command for sending/transferring money. "
                "Commands may include: money transfers, bill payments, mobile top-ups, or statement requests. "
                "Numbers and amounts may be spoken in either language — always convert them into numeric digits. "
                "Mentioned names are typically Pakistani names."
                "Focus on capturing beneficiary names, and bank names correctly. Ignore filler words."
            )

            print("🔄 Transcribing audio (supports Urdu + English)...")

            with open(temp_file_path, "rb") as audio:
                result = client.audio.transcriptions.create(
                    model=model,  
                    file=audio,
                    prompt=prompt_text,
                    temperature=0.0,
                    response_format="json",
                )

                return result

            
        timer_3 = time.perf_counter()
        transcript = await run_in_threadpool(sync_transcribe)
        timer_4 = time.perf_counter()
        print("Time taken to transcribe audio: ", timer_4 - timer_3, "seconds")

        # Validate transcription to prevent hallucinations on silent/empty audio
        transcribed_text = transcript.text.strip()
        
        # Check if transcription is empty or only contains punctuation
        if not transcribed_text or len(transcribed_text) < 3:
            raise HTTPException(
                status_code=400,
                detail="No speech detected in audio. Please speak clearly and try again."
            )
        
        # Check if transcription only contains punctuation/whitespace
        import string
        text_without_punctuation = transcribed_text.translate(str.maketrans('', '', string.punctuation)).strip()
        if not text_without_punctuation:
            raise HTTPException(
                status_code=400,
                detail="No meaningful speech detected. Please record a clear voice command."
            )

        return TranscriptionResponse(
            text = transcribed_text
        )


    except HTTPException:
        # Re-raise HTTPExceptions as-is (validation errors)
        raise
    except Exception as transcription_error:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {transcription_error}")

    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
