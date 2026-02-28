# from src.utils.helper_functions import ml_prediction_sync_supabase_insert
from src.services.transcribe_audio import client
from datetime import datetime, timezone
import json
import time
import asyncio
from fastapi.concurrency import run_in_threadpool
from src.services.amount_extraction import verify_amount_with_llm
from src.utils.logger import log


def check_negative_keywords(transcribed_text):
    """
    Check if transcription contains negative keywords that should trigger 'unknown' response.
    Returns True if negative keywords are found, False otherwise.
    """
    text_lower = transcribed_text.lower()
    
    negative_keywords = [
        # Other Payments
        "other payments",
        "دوسری ادائیگیاں",
        "doosri adaygiyan",
        "dusri adaygiyan",
        
        # Government & Taxes
        "government",
        "hakoomat",
        "hukumat",
        "حکومت",
        "taxes",
        "tax",
        "ٹیکس",
        "tex",
        "texes",
        
        
        # 1Bill / One Bill
        "1bill",
        "one bill",
        "wan bil",
        "wan bill",
        "ون بل",
        "وون بل",
        
        # Kuickpay / Quickpay
        "kuickpay",
        "quickpay",
        "quick pay",
        "کوئیک پے",
        "کوک پے",
        "kuick pay",
        "kuik pay",
        
        # UBL cards and loans
        "ubl cards",
        "ubl loans",
        "cards and loans",
        "ubl card",
        "ubl loan",
        "یو بی ایل",
        "یوبی ایل",
        "ubl",
        "قرضہ",
        "قرضے",
        "qarza",
        "karza",
        "loan",
        "loans",
        
        # Paypro
        "paypro",
        "pay pro",
        "pey pro",
        
        # Education
        "education",
        "تعلیم",
        "taleem",
        "talim",
        
        # Real estate
        "real estate",
        "realestate",
        "ریئل اسٹیٹ",
        "ریل اسٹیٹ",
        "real estat",
        
        # One load / OneLoad
        "one load",
        "oneload",
        "wan load",
        "وون لوڈ",
        "ون لوڈ",
        "one lod",
        
        # Internet service provider
        "internet service provider",
        "internet service",
        "isp",
        "انٹرنیٹ سروس",
        "انٹرنیٹ سروس پرووائیڈر",
        "internet sarvis",
        
        # Wiz top up
        "wiz top up",
        "wiz topup",
        "wiz top-up",
        "ویز ٹاپ اپ",
        "ویز ٹاپاپ",
        "wiz tap ap",
        
        # Mobile postpaid Bills
        "mobile postpaid",
        "postpaid bills",
        "postpaid bill",
        "postpaid",
        "موبائل پوسٹ پیڈ",
        "پوسٹ پیڈ",
        "پوسٹ پیڈ بل",
        "mobile post paid",
        "post paid",
        "mobile postpaid bill",
        
        # Mobile packages
        "mobile packages",
        "mobile package",
        "packages",
        "package",
        "موبائل پیکج",
        "پیکج",
        "پیکجز",
        "mobile pakage",
        "pakage",
        
        # --- Sindhi equivalents ---
        # Government & Taxes (Sindhi)
        "حڪومت",       # government
        "ٽيڪس",        # tax
        
        # UBL loans / cards (Sindhi)
        "قرض",         # loan/debt
        
        # Education (Sindhi)
        "تعليم",       # education
        
        # Real estate (Sindhi)
        "رئل اسٽيٽ",   # real estate
        
        # Internet service provider (Sindhi)
        "انٽرنيٽ سروس",  # internet service
        
        # Mobile postpaid / packages (Sindhi)
        "پوسٽ پيڊ",     # postpaid
        "پيڪيج",        # package
        "پيڪيجز",       # packages
        "موبائل پيڪيج", # mobile package
    ]
    
    # Check if any negative keyword is present in the transcription
    for keyword in negative_keywords:
        if keyword in text_lower:
            log(f"⚠️ Negative keyword detected: '{keyword}' - returning unknown type")
            return True
    
    return False


async def get_intent(transcribed_text):
    prompt = f"""
    send_money: The user wants to send money to a beneficiary.
    pay_bill: The user wants to pay a bill.
    mobile_topup: The user wants to top up their mobile.
    download_statement: The user wants to download a statement.
    check_balance: The user wants to check their balance.
    get_account_number_iban: The user wants to get their account number or IBAN.
    unknown: The intent is not clear.

    You are a helpful assistant that extracts the intent from the transcribed text.
    Transcribed text can be in Sindhi, Urdu, English, or a mix of these languages.
    The transcribed text is: {transcribed_text}
    Return the intent only in the following format: send_money, pay_bill, mobile_topup, download_statement, check_balance, get_account_number_iban, unknown.
    If the intent is not clear, return unknown.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            service_tier="priority",   
            messages=[{"role": "system", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        log(f"Error getting intent: {e}")
        return None


async def prediction_pipeline(data_dict, background_tasks, context_data=None):
    try:
        timer_1 = time.perf_counter()
        # Add a priority openai api call to get the intent from the transcribed text
        intent = await get_intent(data_dict["transcribed_text"])
        log(f"Detected Intent: {intent}")
        if intent == "send_money":
            text = data_dict["transcribed_text"].lower()
            keywords = [
                # English
                "balance", "recharge", "topup", "top-up", "top of",
                "mobile balance", "balance bhejo", "send balance",
                # Urdu
                "لوڈ", "ریچارج", "بیلنس", "بیلنس بھیجو", "موبائل بیلنس", "موبائل بیلنس بھیجو", "ٹاپ اپ", "ٹاپ اپ کرو",
                "ٹوپ اپ",
                # Sindhi
                "لوڊ", "ريچارج", "بيلنس", "موبائل بيلنس", "ٽاپ اپ", "بھیلنس"
            ]
            if any(keyword in text for keyword in keywords):
                log(f"Mobile topup detected, changing intent from {intent} to mobile_topup")
                intent = "mobile_topup"
        
        # Check for negative keywords in mobile_topup, pay_bill, and download_statement intents
        if intent in ["mobile_topup", "pay_bill", "download_statement"]:
            if check_negative_keywords(data_dict["transcribed_text"]):
                log(f"Negative keywords detected for {intent} intent - returning unknown type")
                gpt_result = {
                    "type": "unknown", 
                    "id": [], 
                    "name": [], 
                    "bank_name": [], 
                    "amount": 0, 
                    "bill_type": [], 
                    "bill_name": [], 
                    "mobile_number": [], 
                    "statement_period_month": '', 
                    "statement_period_year": '', 
                    "detected_language": data_dict.get("detected_language", ""),
                    "payee_name": '',
                    "payee_bank_name": '',
                    "payee_account_number": '',
                    "card_discount": False
                }
                return gpt_result
        if intent == "check_balance" or intent == "get_account_number_iban":
            return {
                "type": intent,
                "id": [],
                "name": [],
                "bank_name": [],
                "amount": 0,
                "bill_type": [],
                "bill_name": [],
                "mobile_number": [],
                "statement_period_month": '',
                "statement_period_year": '',
                "detected_language": data_dict.get("detected_language", ""),
                "payee_name": '',
                "payee_bank_name": '',
                "payee_account_number": '',
                "card_discount": False
            }
            
        
        
        # Use GPT function calls for specific intents (excluding unknown)
        gpt_result = None
        
        # Start amount verification task in parallel for send_money and mobile_topup
        verification_task = None
        if intent == "send_money" or intent == "mobile_topup":
            log(f"⏱️ Starting amount verification task for {intent}...")
            verification_task = run_in_threadpool(
                verify_amount_with_llm, 
                data_dict["transcribed_text"], 
                data_dict.get("extracted_amount"), 
                data_dict["detected_language"], 
                intent, 
                data_dict.get("preprocessed_text", "")
            )
        timer_2 = time.perf_counter()
        log("Time taken to determine intent: ", timer_2 - timer_1, "seconds")
        # Start GPT processing task
        gpt_task = None
        timer_3 = time.perf_counter()
        
        if intent == "send_money":
            gpt_task = run_in_threadpool(process_send_money_intent, data_dict, background_tasks, context_data)
        elif intent == "pay_bill":
            gpt_task = run_in_threadpool(process_pay_bill_intent, data_dict, background_tasks, context_data)
        elif intent == "mobile_topup":
            gpt_task = run_in_threadpool(process_mobile_topup_intent, data_dict, background_tasks, context_data)
        elif intent == "download_statement":
            gpt_task = run_in_threadpool(process_download_statement_intent, data_dict, background_tasks, context_data)
        
        # Await both tasks in parallel
        if gpt_task is not None:
            if verification_task is not None:
                
                # Both tasks run in parallel
                gpt_result, verification_result = await asyncio.gather(gpt_task, verification_task)
                
                # Process verification result
                verified_amount = verification_result.get("verified_amount")
                if verified_amount is not None:
                    if verified_amount != data_dict.get("extracted_amount"):
                        log(f"✨ Verified amount: {verified_amount} is different from extracted amount: {data_dict.get('extracted_amount')}")
                        data_dict["extracted_amount"] = verified_amount
            else:
                # Only GPT task
                gpt_result = await gpt_task
        timer_4 = time.perf_counter()
        log("Time taken to process GPT task: ", timer_4 - timer_3, "seconds")
        # Add extracted amount to GPT result if available
        if gpt_result and data_dict.get("extracted_amount") is not None:
            gpt_result["amount"] = data_dict["extracted_amount"]
        
        # Store ML prediction with GPT comparison data
        # data_to_insert = {
        #     "file_id": data_dict["file_name"],
        #     "intent": intent,
        #     "transcribed_text": data_dict["transcribed_text"],
        #     "detected_language": data_dict["detected_language"],
        #     "gpt_response": json.dumps(gpt_result) if gpt_result else None,
        #     "created_at": datetime.now(timezone.utc).isoformat(),
        # }
        # background_tasks.add_task(ml_prediction_sync_supabase_insert, data_to_insert)
        return gpt_result
    except Exception as e:
        log(f"Error predicting intent: {e}")
        return gpt_result


def process_send_money_intent(data_dict, background_tasks, context_data=None):
    """Process send money intent with focused GPT function call"""
    
    send_money_function = {
        "name": "process_send_money",
        "description": "Process send money command - return list of matched beneficiary IDs",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Return list of matched beneficiary IDs from the beneficiaries list. Return multiple IDs when name matches multiple beneficiaries and bank name cannot disambiguate. Return empty list [] when no name is mentioned or no match found."
                }
            }
        }
    }
    
    beneficiaries_data = context_data.get("beneficiaries", []) if context_data else []
    log("In send money: detected language is ", data_dict['detected_language'])
    
    # Create language-specific prompts for better matching
    if data_dict['detected_language'] == 'urdu':
        # Urdu/Sindhi prompt — handles both Urdu and Sindhi transcribed text
        prompt = f"""
        You are processing a SEND MONEY command in URDU or SINDHI. Your ONLY job is to identify which beneficiary from the list matches the name and bank name (if mentioned) in the transcript.
        
        Transcript: "{data_dict['transcribed_text']}"
        Language: {data_dict['detected_language']}
        Extracted Amount: {data_dict.get('extracted_amount', 'None')}
        
        YOUR TASK: Return ONLY the ID of the matched beneficiary from beneficiaries list.
        
        URDU / SINDHI NAME AND BANK NAME MATCHING INSTRUCTIONS:
        
        1. EXTRACT the name mentioned in the transcript
           - CRITICAL: If NO name is mentioned in the transcript, return id = []
           - Only proceed if a person's name is clearly mentioned
           - Amount-only transcripts like "سو روپے بھیجو" or "سؤ روپيا موڪل" (send 100 rupees) have NO name
        
        2. EXTRACT the bank name mentioned in the transcript (if any)
           - Look for bank names in Urdu script, Sindhi script, or English
           - Urdu bank name references:
             * "ایچ بی ایل" / "ایچ بی ایل بینک" → "HBL" / "Habib Bank"
             * "یو بی ایل" / "یو بی ایل بینک" → "UBL" / "United Bank"
             * "ایم سی بی" / "ایم سی بی بینک" → "MCB" / "MCB Bank"
             * "میضان" / "میضان بینک" → "Meezan" / "Meezan Bank"
             * "الفا" / "الفلاح" / "الفا بینک" → "Alfalah" / "Bank Alfalah"
             * "فیصل" / "فیصل بینک" → "Faysal" / "Faysal Bank"
             * "اسکری" / "اسکری بینک" → "Askari" / "Askari Bank"
             * "جے ایس بینک" → "JS Bank"
             * "اسٹینڈرڈ چارٹرڈ" → "Standard Chartered"
           - Sindhi bank name references (same banks, different spelling):
             * "ايڇ بي ايل" / "ايڇ بي ايل بينڪ" → "HBL" / "Habib Bank"
             * "يو بي ايل" / "يو بي ايل بينڪ" → "UBL" / "United Bank"
             * "ايم سي بي" / "ايم سي بي بينڪ" → "MCB" / "MCB Bank"
             * "ميزان" / "ميزان بينڪ" → "Meezan" / "Meezan Bank"
             * "الفلاح" / "الفلاح بينڪ" → "Alfalah" / "Bank Alfalah"
             * "فيصل" / "فيصل بينڪ" → "Faysal" / "Faysal Bank"
             * "اسڪري" / "اسڪري بينڪ" → "Askari" / "Askari Bank"
             * "جي ايس بينڪ" → "JS Bank"
             * "اسٽينڊرڊ چارٽرڊ" → "Standard Chartered"
        
        3. TRANSLITERATE the Urdu or Sindhi name to English (only if name exists):
           - Urdu examples:
             * "علی" → "Ali", "احمد" → "Ahmed", "حمزہ" → "Hamza"
             * "عمر" → "Omer" or "Umar" or "Omar"
             * "عثمان" → "Usman" or "Usama" or "Osama"
             * "حسن" → "Hassan" or "Hasan"
           - Sindhi examples (same Arabic-origin names, slight script differences):
             * "علي" → "Ali", "احمد" → "Ahmed", "حمزه" → "Hamza"
             * "محمد" → "Muhammad" or "Mohammad"
             * "عمر" → "Omer" or "Umar" or "Omar"
             * "عثمان" → "Usman", "حسن" → "Hassan" or "Hasan"
        
        4. MATCH against beneficiaries list:
           
           STEP A: Filter by name first
           - Check if transliterated name appears in beneficiary's full name
           - "عمر" / "عمر" → "Omer" → matches "MUHAMMAD OMER KHAN"
           - "علی" / "علي" → "Ali" → matches "Ali Raza" or "Mubashir Ali"
           - Prioritize first name matches
           - Allow similarity > 85% for fuzzy matching
           
           STEP B: If multiple beneficiaries match the name, filter by bank name
           - Check if there are multiple beneficiaries with the same name but different bankName
           - If bank name is mentioned in transcript, match it against the bankName field in beneficiaries
           - Match priority when bank name is mentioned:
             1. Exact bank name match (case-insensitive)
             2. Partial bank name match (e.g., "HBL" matches "Habib Bank")
             3. Bank acronym match (e.g., "یو بی ایل" / "يو بي ايل" matches "United Bank" or "UBL")
           - If bank name matches, return that beneficiary's ID
           - If bank name doesn't match or is not mentioned, return ALL matching IDs
        
        5. RETURN list of matched beneficiary IDs:
           - IF NAME MENTIONED AND SINGLE MATCH FOUND: Return id = [beneficiary_id]
           - IF NAME MENTIONED, MULTIPLE MATCHES, AND BANK NAME MATCHES ONE: Return id = [matched_beneficiary_id]
           - IF NAME MENTIONED, MULTIPLE MATCHES, AND BANK NAME NOT MENTIONED OR DOESN'T DISAMBIGUATE: Return id = [id1, id2, ...] (ALL matching IDs so user can pick)
           - IF NO NAME MENTIONED: Return id = [] (empty list)
           - IF NAME MENTIONED BUT NO MATCH: Return id = [] (empty list)
        
        AVAILABLE BENEFICIARIES:
        {json.dumps(beneficiaries_data)}
        
        Remember: When multiple beneficiaries share the same name and bank name is mentioned and matches one specifically, return only that one ID. If bank name is not mentioned or matches multiple, return ALL matching IDs as a list so the frontend can prompt the user to select. The backend will fill in name and bankName based on these IDs.
        """
    else:
        # English-specific prompt with name variation focus
        prompt = f"""
        You are processing a SEND MONEY command in ENGLISH. Your ONLY job is to identify which beneficiary from the list matches the English name and bank name (if mentioned) in the transcript.
        
        Transcript: "{data_dict['transcribed_text']}"
        Language: {data_dict['detected_language']}
        Extracted Amount: {data_dict.get('extracted_amount', 'None')}
        
        YOUR TASK: Return ONLY the ID of the matched beneficiary from beneficiaries list.
        
        ENGLISH NAME AND BANK NAME MATCHING INSTRUCTIONS:
        
        1. EXTRACT the English name mentioned in the transcript
           - CRITICAL: If NO name is mentioned in the transcript, return id = ""
           - Only proceed if a person's name is clearly mentioned
           - Amount-only transcripts like "send 100 rupees" or "send Rs. 500" have NO name
        
        2. EXTRACT the bank name mentioned in the transcript (if any)
           - Look for bank names in English
           - Common Pakistani bank names and their variations:
             * "HBL" / "Habib Bank" / "Habib Bank Limited"
             * "UBL" / "United Bank" / "United Bank Limited"
             * "MCB" / "MCB Bank" / "Muslim Commercial Bank"
             * "Meezan" / "Meezan Bank"
             * "Alfalah" / "Bank Alfalah" / "Alfalah Bank"
             * "Faysal" / "Faysal Bank"
             * "Askari" / "Askari Bank"
             * "JS Bank"
             * "Standard Chartered"
        
        3. RECOGNIZE Pakistani name variations (treat as same name, only if name exists):
           * Umar = Omer = Omar
           * Hassan = Hasan
           * Hussain = Husain = Hossain
        
        4. MATCH against beneficiaries list:
           
           STEP A: Filter by name first
           - PRIORITY 1: Exact name match (e.g., "Ali" = "ALI")
           - PRIORITY 2: Name variation match (e.g., "Umar" matches "OMER")
           - PRIORITY 3: Partial name match (e.g., "Ali" in "Mubashir Ali")
           - Check if mentioned name appears in beneficiary's full name
           - "Umar" matches "MUHAMMAD OMER KHAN" (Umar = Omer)
           - "Ali" matches "Ali Raza" or "Mubashir Ali"
           - "Ahmed" matches "Ahmed Faraz" or "Adnan Ahmed"
           - Allow similarity > 85% for fuzzy matching
           
           STEP B: If multiple beneficiaries match the name, filter by bank name
           - Check if there are multiple beneficiaries with the same name but different bankName
           - If bank name is mentioned in transcript, match it against the bankName field in beneficiaries
           - Match priority when bank name is mentioned:
             1. Exact bank name match (case-insensitive)
             2. Partial bank name match (e.g., "HBL" matches "Habib Bank")
             3. Bank acronym match (e.g., "UBL" matches "United Bank")
           - If bank name matches, return that beneficiary's ID
           - If bank name doesn't match or is not mentioned, return the first matching beneficiary's ID
        
        5. RETURN list of matched beneficiary IDs:
           - IF NAME MENTIONED AND SINGLE MATCH FOUND: Return id = [beneficiary_id]
           - IF NAME MENTIONED, MULTIPLE MATCHES, AND BANK NAME MATCHES ONE: Return id = [matched_beneficiary_id]
           - IF NAME MENTIONED, MULTIPLE MATCHES, AND BANK NAME NOT MENTIONED OR DOESN'T DISAMBIGUATE: Return id = [id1, id2, ...] (ALL matching IDs so user can pick)
           - IF NO NAME MENTIONED: Return id = [] (empty list)
           - IF NAME MENTIONED BUT NO MATCH: Return id = [] (empty list)
        
        AVAILABLE BENEFICIARIES:
        {json.dumps(beneficiaries_data)}
        
        Remember: When multiple beneficiaries share the same name and bank name is mentioned and matches one specifically, return only that one ID. If bank name is not mentioned or matches multiple, return ALL matching IDs as a list so the frontend can prompt the user to select. The backend will fill in name and bankName based on these IDs.
        """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Process this send money command: {data_dict['transcribed_text']}"}
            ],
            functions=[send_money_function],
            function_call={"name": "process_send_money"},
            temperature=0.0,
            service_tier="priority"
        )
        
        function_call = response.choices[0].message.function_call
        result = json.loads(function_call.arguments)
        result["type"] = "send_money"
        # Ensure id is always a list
        raw_id = result.get("id", [])
        if isinstance(raw_id, str):
            raw_id = [raw_id] if raw_id else []
        result["id"] = raw_id
        result["amount"] = data_dict.get("extracted_amount")
        result["detected_language"] = data_dict["detected_language"]
        
        # Fill in empty list fields
        result["name"] = []
        result["bank_name"] = []
        result["bill_type"] = []
        result["bill_name"] = []
        result["mobile_number"] = []
        result["statement_period_month"] = ""
        result["statement_period_year"] = ""
        result["payee_name"] = ""
        result["payee_bank_name"] = ""
        result["payee_account_number"] = ""
        result["card_discount"] = False
        
        # Lookup each matched beneficiary and build parallel lists
        if result["id"]:
            valid_ids = []
            names = []
            bank_names = []
            for bid in result["id"]:
                matched_beneficiary = next((b for b in beneficiaries_data if b['id'] == bid), None)
                if matched_beneficiary:
                    valid_ids.append(bid)
                    names.append(matched_beneficiary.get('name', ''))
                    bank_names.append(matched_beneficiary.get('bank_name', ''))
                    log(f"✅ Matched beneficiary by ID: {matched_beneficiary.get('name')} ({matched_beneficiary.get('bank_name', '')})")
                else:
                    log(f"⚠️ Beneficiary ID {bid} not found in beneficiaries_data")
            result["id"] = valid_ids
            result["name"] = names
            result["bank_name"] = bank_names
        
        return result
        
    except Exception as e:
        log(f"Error processing send money intent: {e}")
        return {"type": "send_money", "id": [], "name": [], "bank_name": [], "amount": None, "bill_type": [], "bill_name": [], "mobile_number": [], "statement_period_month": "", "statement_period_year": "", "detected_language": data_dict["detected_language"], "payee_name": "", "payee_bank_name": "", "payee_account_number": "", "card_discount": False}


def process_pay_bill_intent(data_dict, background_tasks, context_data=None):
    """Process pay bill intent with focused GPT function call - only matches bill types, no beneficiary matching needed"""
    
    pay_bill_function = {
        "name": "process_pay_bill",
        "description": "Process pay bill command - return list of matched bill IDs",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Return list of matched bill IDs from bills_type_list. Return multiple IDs when the transcript matches multiple bills with similar confidence. Return empty list [] when no confident match is found."
                }
            }
        }
    }
    
    bill_types_data = context_data.get("bill_types", []) if context_data else []
    
    prompt = f"""
    You are processing a PAY BILL command. Your ONLY job is to identify which bill from the list best matches the bill type and name mentioned in the transcript.
    
    Transcript: "{data_dict['transcribed_text']}"
    Language: {data_dict['detected_language']}
    Extracted Amount: {data_dict.get('extracted_amount', 'None')}
    
    YOUR TASK: Return ONLY the ID of the best matched bill from bills_type_list if there is a confident match.
    
    MATCHING INSTRUCTIONS:
    
    1. EXTRACT the bill type/provider and bill name (nickname) mentioned in the transcript
       - The transcript may be in Sindhi, Urdu, or English
       - For Urdu/Sindhi text: Transliterate to English before comparing
       - Focus on key identifiers: provider names, company names, or bill nicknames
    
    2. SEARCH through bills_type_list to find the best matching bill
       - Each bill has: id, type (provider), and name (bill nickname)
       - PRIORITY 1: Exact match on type (provider) AND name (nickname)
       - PRIORITY 2: Exact match on type (provider) OR name (nickname) with high confidence
       - PRIORITY 3: Partial/fuzzy match with similarity > 85%
       - If multiple bills have same type, use the name to pick the correct one
       - Use case-insensitive comparison
    
    3. VALIDATE the match quality:
       - ONLY include an ID if the match is confident and reasonable
       - If the mentioned bill type/provider does NOT exist in the available bills, return id = []
       - If the transcript is too vague or ambiguous, return id = []
       - Do NOT force a match when confidence is low
    
    4. RETURN list of matched bill IDs:
       - IF SINGLE CONFIDENT MATCH FOUND: Return id = [bill_id]
       - IF MULTIPLE BILLS MATCH WITH SIMILAR CONFIDENCE (e.g., same provider but different nicknames): Return id = [id1, id2, ...] (all matching IDs so user can pick)
       - IF NO CONFIDENT MATCH: Return id = [] (empty list)
       - IF AMBIGUOUS WITH NO REASONABLE MATCHES: Return id = [] (empty list)
    
    AVAILABLE BILLS:
    {json.dumps(bill_types_data)}
    
    Remember: Return a single-element list when only one bill matches confidently. Return multiple IDs when multiple bills plausibly match the transcript so the frontend can prompt the user to select. When in doubt and no bill matches, return an empty list.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Process this pay bill command: {data_dict['transcribed_text']}"}
            ],
            functions=[pay_bill_function],
            function_call={"name": "process_pay_bill"},
            temperature=0.0,
            service_tier="priority"
        )
        
        function_call = response.choices[0].message.function_call
        result = json.loads(function_call.arguments)
        result["type"] = "pay_bill"
        # Ensure id is always a list
        raw_id = result.get("id", [])
        if isinstance(raw_id, str):
            raw_id = [raw_id] if raw_id else []
        result["id"] = raw_id
        result["amount"] = data_dict.get("extracted_amount")
        result["detected_language"] = data_dict["detected_language"]
        
        # Fill in empty list fields
        result["name"] = []
        result["bank_name"] = []
        result["bill_type"] = []
        result["bill_name"] = []
        result["mobile_number"] = []
        result["statement_period_month"] = ""
        result["statement_period_year"] = ""
        result["payee_name"] = ""
        result["payee_bank_name"] = ""
        result["payee_account_number"] = ""
        result["card_discount"] = False
        
        # Lookup each matched bill and build parallel lists
        if result["id"]:
            valid_ids = []
            bill_types = []
            bill_names = []
            for bid in result["id"]:
                matched_bill = next((b for b in bill_types_data if b['id'] == bid), None)
                if matched_bill:
                    valid_ids.append(bid)
                    bill_types.append(matched_bill['type'])
                    bill_names.append(matched_bill['name'])
                    log(f"✅ Matched bill by ID: {matched_bill['type']} - {matched_bill['name']}")
                else:
                    log(f"⚠️ Bill ID {bid} not found in bill_types_data")
            result["id"] = valid_ids
            result["bill_type"] = bill_types
            result["bill_name"] = bill_names
        
        return result
        
    except Exception as e:
        log(f"Error processing pay bill intent: {e}")
        return {"type": "pay_bill", "id": [], "name": [], "bank_name": [], "amount": None, "bill_type": [], "bill_name": [], "mobile_number": [], "statement_period_month": "", "statement_period_year": "", "detected_language": data_dict["detected_language"], "payee_name": "", "payee_bank_name": "", "payee_account_number": "", "card_discount": False}


def process_mobile_topup_intent(data_dict, background_tasks, context_data=None):
    """Process mobile topup intent with focused GPT function call"""
    
    mobile_topup_function = {
        "name": "process_mobile_topup",
        "description": "Process mobile topup command - return list of matched contact IDs",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Return list of matched contact IDs from phone_number_list. Return multiple IDs when name matches multiple contacts and SIM provider cannot disambiguate. Return empty list [] when no name is mentioned or no match found."
                },
                "mobile_number": {
                    "type": "string",
                    "description": "Return extracted mobile number when user dictates digits directly; use empty string when not applicable"
                }
            }
        }
    }
    
    phone_contacts_data = context_data.get("phone_contacts", []) if context_data else []
    
    prompt = f"""
    You are processing a MOBILE TOPUP command. Your ONLY job is to identify which contact from the list matches the name/provider mentioned in the transcript.
    
    Transcript: "{data_dict['transcribed_text']}"
    Language: {data_dict['detected_language']}
    Extracted Amount: {data_dict.get('extracted_amount', 'None')}
    
    YOUR TASK: Return ONLY the ID of the matched contact from phone_number_list.
    
    IMPORTANT: Contact names in the list are concatenated with SIM providers (e.g., "Rafay operator TELENOR - TOPUP").
    You MUST match by NAME first, then use SIM provider ONLY if multiple contacts share the same name.
    
    MATCHING INSTRUCTIONS (FOLLOW THIS ORDER STRICTLY):
    
    STEP 1: EXTRACT the PERSON'S NAME from the transcript
       - Extract the name mentioned in the transcript (ignore SIM provider mentions for now)
       - The transcript may be in Sindhi, Urdu, or English
       - For Urdu/Sindhi names: Transliterate to English before comparing
         * "علی" / "علي" → "Ali", "احمد" → "Ahmed", "حمزہ" / "حمزه" → "Hamza", "رفیع" → "Rafay"
       - For English names: Use as-is (case-insensitive)
       - CRITICAL: If NO name is mentioned in the transcript, proceed to STEP 3
    
    STEP 2: MATCH CONTACTS BY NAME FIRST
       - Extract the name portion from each contact (the part before the SIM provider)
         * "Rafay operator TELENOR - TOPUP" → name portion is "Rafay operator"
         * "Rafay operator UFONE - PREPAID" → name portion is "Rafay operator"
         * "Rafay operator ZONG-TOPUP" → name portion is "Rafay operator"
       - Compare the extracted name from transcript against the name portion of contacts
       - Use case-insensitive comparison
       - Allow partial matches: "Rafay" can match "Rafay operator"
       - Allow similarity > 80% for fuzzy matching
       - Collect ALL contacts that match the name
    
    STEP 3: HANDLE MATCHING RESULTS
    
       CASE A: If name matches EXACTLY ONE contact:
         - Return that contact's ID in a list immediately
         - SIM provider matching is NOT needed
    
       CASE B: If name matches MULTIPLE contacts:
         - Extract SIM provider mentioned in transcript (if any)
           * Common providers: "Telenor", "TELENOR", "Ufone", "UFONE", "Zong", "ZONG", "Jazz", "JAZZ"
           * Urdu: "ٹیلی نار" → "Telenor", "زونگ" → "Zong", "یوفون" → "Ufone", "جاز" → "Jazz"
           * Sindhi: "ٽيلينار" → "Telenor", "زونگ" → "Zong", "يوفون" → "Ufone", "جاز" → "Jazz"
         - Match the SIM provider against the provider part in the matched contacts
         - If provider matches exactly ONE contact, return that contact's ID as a single-element list
         - If provider doesn't match or is not mentioned, return ALL matching contact IDs as a list so user can pick
    
       CASE C: If name does NOT match any contact:
         - DO NOT match based on SIM provider alone
         - Return id = [] (empty list)
         - Only exception: If user dictates mobile number directly, return id = [], mobileNumber = extracted_digits
    
       CASE D: If NO name mentioned in transcript:
         - DO NOT match based on SIM provider alone
         - Return id = [] (empty list)
         - Only exception: If user dictates mobile number directly, return id = [], mobileNumber = extracted_digits
    
    STEP 4: RETURN list of matched contact IDs:
       - IF NAME MATCHES AND SINGLE CONTACT FOUND: Return id = [contact_id]
       - IF NAME MATCHES MULTIPLE CONTACTS AND PROVIDER MATCHES ONE: Return id = [matched_contact_id]
       - IF NAME MATCHES MULTIPLE CONTACTS AND PROVIDER DOESN'T MATCH OR NOT MENTIONED: Return id = [id1, id2, ...] (ALL matching contact IDs so user can select)
       - IF NAME DOESN'T MATCH: Return id = [] (empty list)
       - IF MOBILE NUMBER SPOKEN DIRECTLY: Return id = [], mobileNumber = extracted_digits
    
    AVAILABLE PHONE CONTACTS:
    {json.dumps(phone_contacts_data)}
    
    Remember: NAME matching is PRIMARY. SIM provider matching is SECONDARY and ONLY used when multiple contacts share the same name. If name doesn't match, don't match based on provider alone. When multiple contacts share the same name and provider doesn't disambiguate, return ALL matching IDs as a list so the frontend can prompt the user to select.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Process this mobile topup command: {data_dict['transcribed_text']}"}
            ],
            functions=[mobile_topup_function],
            function_call={"name": "process_mobile_topup"},
            temperature=0.0,
            service_tier="priority"
        )
        
        function_call = response.choices[0].message.function_call
        result = json.loads(function_call.arguments)
        result["type"] = "mobile_topup"
        # Ensure id is always a list
        raw_id = result.get("id", [])
        if isinstance(raw_id, str):
            raw_id = [raw_id] if raw_id else []
        result["id"] = raw_id
        mobile_number = result.get("mobileNumber", result.get("mobile_number", ""))
        result["amount"] = data_dict.get("extracted_amount")
        result["detected_language"] = data_dict["detected_language"]
        
        # Fill in empty list fields
        result["name"] = []
        result["bank_name"] = []
        result["mobile_number"] = []
        result["bill_type"] = []
        result["bill_name"] = []
        result["statement_period_month"] = ""
        result["statement_period_year"] = ""
        result["payee_name"] = ""
        result["payee_bank_name"] = ""
        result["payee_account_number"] = ""
        result["card_discount"] = False
        
        # Lookup each matched contact and build parallel lists
        if result["id"]:
            valid_ids = []
            names = []
            mobile_numbers = []
            for cid in result["id"]:
                matched_contact = next((c for c in phone_contacts_data if c['id'] == cid), None)
                if matched_contact:
                    valid_ids.append(cid)
                    names.append(matched_contact['name'])
                    mobile_numbers.append(matched_contact['number'])
                    log(f"✅ Matched contact by ID: {matched_contact['name']} ({matched_contact['number']})")
                else:
                    log(f"⚠️ Contact ID {cid} not found in phone_contacts_data")
            result["id"] = valid_ids
            result["name"] = names
            result["mobile_number"] = mobile_numbers
        elif mobile_number:
            # User dictated a number directly — no contact match
            result["mobile_number"] = [mobile_number]
        
        return result
        
    except Exception as e:
        log(f"Error processing mobile topup intent: {e}")
        return {"type": "mobile_topup", "id": [], "name": [], "bank_name": [], "amount": None, "bill_type": [], "bill_name": [], "mobile_number": [], "statement_period_month": "", "statement_period_year": "", "detected_language": data_dict["detected_language"], "payee_name": "", "payee_bank_name": "", "payee_account_number": "", "card_discount": False}


def process_download_statement_intent(data_dict, background_tasks, context_data=None):
    """Process download statement intent with focused GPT function call"""
    
    download_statement_function = {
        "name": "process_download_statement",
        "description": "Process download statement command to extract time period preferences",
        "parameters": {
            "type": "object",
            "properties": {
                "statement_period_month": {
                    "type": "string",
                    "description": "Month name in English (e.g., 'August', 'January'); empty for yearly statements"
                },
                "statement_period_year": {
                    "type": "string",
                    "description": "Year as 'YYYY' format (e.g., '2024'); empty for monthly statements"
                }
            }
        }
    }
    
    today = datetime.now()
    prompt = f"""
    You are processing a DOWNLOAD STATEMENT command. Extract time period preferences.
    
    Transcript: "{data_dict['transcribed_text']}"
    Language: {data_dict['detected_language']}
    Today's date: {today.strftime('%B %d, %Y')}
    
    TIME PERIOD DETECTION:
    - For MONTHLY statements: Extract month name in English (e.g., "August", "January")
    - Add corresponding year to statement_period_year
    - If month is in future relative to today, use previous year
    - Examples: "August" (if today is Oct 2025) → month="August", year="2025"
    
    - For YEARLY statements: Extract year as "YYYY" format (e.g., "2024")
    - Leave statement_period_month empty
    
    - If BOTH mentioned: Populate both statement_period_month and statement_period_year
    
    KEYWORDS: "monthly", "yearly", "last month", "previous year", "mahana", "سالانہ",
    "مهيني" (Sindhi: monthly), "سالانه" (Sindhi: yearly), "گذريل مهينو" (Sindhi: last month)
    
    DEFAULT BEHAVIOR:
    - If no specific period mentioned: use current month and year
    - Current month: {today.strftime('%B')}, Current year: {today.year}
    
    Return structured data for statement download operation.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Process this download statement command: {data_dict['transcribed_text']}"}
            ],
            functions=[download_statement_function],
            function_call={"name": "process_download_statement"},
            temperature=0.0,
            service_tier="priority"
        )
        
        function_call = response.choices[0].message.function_call
        result = json.loads(function_call.arguments)
        result["type"] = "download_statement"
        result["id"] = []
        result["name"] = []
        result["bank_name"] = []
        result["amount"] = data_dict.get("extracted_amount")
        result["bill_type"] = []
        result["bill_name"] = []
        result["mobile_number"] = []
        result["detected_language"] = data_dict["detected_language"]
        result["statement_period_month"] = result.get("statement_period_month", "")
        result["statement_period_year"] = result.get("statement_period_year", "")
        result["payee_name"] = ""
        result["payee_bank_name"] = ""
        result["payee_account_number"] = ""
        result["card_discount"] = False
        
        # Set defaults if empty
        if not result["statement_period_month"] and not result["statement_period_year"]:
            result["statement_period_month"] = today.strftime("%B")
            result["statement_period_year"] = str(today.year)
        
        return result
        
    except Exception as e:
        log(f"Error processing download statement intent: {e}")
        return {"type": "download_statement", "id": [], "name": [], "bank_name": [], "amount": None, "bill_type": [], "bill_name": [], "mobile_number": [], "statement_period_month": today.strftime("%B"), "statement_period_year": str(today.year), "detected_language": data_dict["detected_language"], "payee_name": "", "payee_bank_name": "", "payee_account_number": "", "card_discount": False}


def process_add_new_payee_intent(data_dict, background_tasks, context_data=None):
    """Process add new payee intent with focused GPT function call"""
    """When the intent is add_new_payee, the user can also mention the name of the payee, the bank name, and the account number, we need to extract these details and return them in the response."""
    """Details can be mentioned in urdu or english, but we need to return them in english."""
    
    add_new_payee_function = {
        "name": "process_add_new_payee",
        "description": "Process add new payee command to extract payee details",
        "parameters": {
            "type": "object",
            "properties": {
                "payee_name": {
                    "type": "string",
                    "description": "The name of the payee"
                },
                "payee_bank_name": {
                    "type": "string",
                    "description": "The bank name of the payee"
                },
                "payee_account_number": {
                    "type": "string",
                    "description": "The account number of the payee"
                }
            }
        }
    }

    list_of_all_pakistani_banks = ["HBL", "UBL", "MCB", "Meezan", "Alfalah", "Faysal", "Askari", "JS Bank", "Standard Chartered", "Habib Bank", "United Bank", "MCB Bank", "Meezan Bank", "Alfalah Bank", "Faysal Bank", "Askari Bank", "JS Bank Bank", "Standard Chartered Bank", "Habib Bank Bank", "United Bank Bank"]
    list_of_all_pakistani_banks_urdu = ["ایچ بی ایل", "یو بی ایل", "ایم سی بی", "میضان", "الفا", "فیصل", "اسکری", "جے ایس بینک", "اسٹینڈرڈ چارٹرڈ", "یو بی ایل بینک", "ایچ بی ایل بینک", "ایم سی بی بینک", "میضان بینک", "الفا بینک", "فیصل بینک", "اسکری بینک", "جے ایس بینک بینک", "اسٹینڈرڈ چارٹرڈ بینک"]
    
    list_of_all_pakistani_banks_sindhi = ["ايڇ بي ايل", "يو بي ايل", "ايم سي بي", "ميزان", "الفلاح", "فيصل", "اسڪري", "جي ايس بينڪ", "اسٽينڊرڊ چارٽرڊ"]

    prompt = f"""You are processing a ADD NEW PAYEE command. Extract payee details from the transcript.
    
    Transcript: "{data_dict['transcribed_text']}"
    Language: {data_dict['detected_language']}
    
    YOUR TASK: Extract payee details from the transcript.

    User can mention the name of the payee, the bank name, and the account number in the transcript.
    Details can be mentioned in Sindhi, Urdu, or English, but we need to return them in English.

    Mentioned bank name most often belongs to one of these lists:
    English banks: {json.dumps(list_of_all_pakistani_banks)}
    Urdu banks: {json.dumps(list_of_all_pakistani_banks_urdu)}
    Sindhi banks: {json.dumps(list_of_all_pakistani_banks_sindhi)}

    If the user doesn't mention the details, return empty strings for the details.
    RETURN STRUCTURED DATA FOR ADD NEW PAYEE OPERATION.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Process this add new payee command: {data_dict['transcribed_text']}"}
            ],
            functions=[add_new_payee_function],
            function_call={"name": "process_add_new_payee"},
            temperature=0.0,
            service_tier="priority"
        )
        function_call = response.choices[0].message.function_call
        result = json.loads(function_call.arguments)
        result["type"] = "add_new_payee"
        result["id"] = []
        result["name"] = []
        result["bank_name"] = []
        result["amount"] = 0
        result["bill_type"] = []
        result["bill_name"] = []
        result["mobile_number"] = []
        result["statement_period_month"] = ""
        result["statement_period_year"] = ""
        result["payee_name"] = result.get("payee_name", "")
        result["payee_bank_name"] = result.get("payee_bank_name", "")
        result["payee_account_number"] = result.get("payee_account_number", "")
        result["card_discount"] = False
        
        return result
        
    except Exception as e:
        log(f"Error processing add new payee intent: {e}")
        return {"type": "add_new_payee", "id": [], "name": [], "bank_name": [], "amount": 0, "bill_type": [], "bill_name": [], "mobile_number": [], "statement_period_month": "", "statement_period_year": "", "detected_language": data_dict["detected_language"], "payee_name": "", "payee_bank_name": "", "payee_account_number": "", "card_discount": False}


def process_deals_and_discounts_intent(data_dict, background_tasks, context_data=None):
    """Process deals and discounts intent with focused GPT function call"""
    """When the intent is deals_and_discounts, the user can also mention whether he wants discounts related to his/her Card, so we just need to return the boolean value of the card_discount field."""
    
    deals_and_discounts_function = {
        "name": "process_deals_and_discounts",
        "description": "Process deals and discounts command to extract card discount details",
        "parameters": {
            "type": "object",
            "properties": {
                "card_discount": {
                    "type": "boolean",
                    "description": "Whether the user wants discounts related to his/her Card"
                }
            }
        }
    }
    
    prompt = f"""You are processing a DEALS AND DISCOUNTS command. Extract card discount confirmation from the transcript.
    
    Transcript: "{data_dict['transcribed_text']}"
    Language: {data_dict['detected_language']}
    
    YOUR TASK: Extract card discount details from the transcript.
    
    User can mention whether he wants discounts related to his/her Card in the transcript.
    The transcript may be in Sindhi, Urdu, or English.
    Return structured data for deals and discounts operation."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Process this deals and discounts command: {data_dict['transcribed_text']}"}
            ],
            functions=[deals_and_discounts_function],
            function_call={"name": "process_deals_and_discounts"},
            temperature=0.0,
            service_tier="priority"
        )
        function_call = response.choices[0].message.function_call
        result = json.loads(function_call.arguments)
        result["type"] = "deals_and_discounts"
        result["id"] = []
        result["name"] = []
        result["bank_name"] = []
        result["amount"] = 0
        result["bill_type"] = []
        result["bill_name"] = []
        result["mobile_number"] = []
        result["statement_period_month"] = ""
        result["statement_period_year"] = ""
        result["payee_name"] = ""
        result["payee_bank_name"] = ""
        result["payee_account_number"] = ""
        result["card_discount"] = result.get("card_discount", False)
        
        return result
        
    except Exception as e:
        log(f"Error processing deals and discounts intent: {e}")
        return {"type": "deals_and_discounts", "id": [], "name": [], "bank_name": [], "amount": 0, "bill_type": [], "bill_name": [], "mobile_number": [], "statement_period_month": "", "statement_period_year": "", "detected_language": data_dict["detected_language"], "payee_name": "", "payee_bank_name": "", "payee_account_number": "", "card_discount": False}


