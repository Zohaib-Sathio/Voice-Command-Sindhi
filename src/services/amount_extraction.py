from src.utils.urdu_numeric_converter import preprocess_urdu_text, convert_urdu_amount, urdu_converter
from src.utils.english_numeric_converter import preprocess_english_text, convert_english_amount
from src.utils.roman_urdu_numeric_converter import preprocess_roman_urdu_text, convert_roman_urdu_amount
from openai import OpenAI
import os
import json
import re
from typing import Optional, Union
from src.utils.logger import log


def extract_amount_from_transcript(text: str, language: str = "english") -> dict:
    """
    Intelligently extract amount from transcript using Urdu, English, and Roman Urdu converters.
    This function is LANGUAGE-DETECTION AGNOSTIC - it always tries all converters
    and uses intelligent heuristics to pick the correct amount, regardless of what
    Whisper reports as the detected language.
    
    Handles three scenarios:
    1. Standard Urdu numbers: "پانچ ہزار" → 5000
    2. Standard English numbers: "five thousand" → 5000
    3. English-in-Urdu-script: "ٹین" (ten in Urdu letters) → 10
    
    Args:
        text: The transcribed text
        language: Detected language from Whisper ('english', 'urdu', or other)
                 Note: This may be incorrect, so we validate against actual content
    
    Returns:
        dict: {
            'amount': extracted amount or None,
            'preprocessed_text': text with numerals converted to digits,
            'source': which converter found the amount ('urdu', 'english', 'roman_urdu', 'both', or None),
            'language_mismatch': True if detected language doesn't match extraction source,
            'actual_language': The language that actually contained the amount
        }
    """
    result = {
        'amount': None,
        'preprocessed_text': text,
        'source': None,
        'language_mismatch': False,
        'actual_language': language
    }
    
    # Check if this is an action phrase that should return None (before any preprocessing)
    if urdu_converter._is_action_phrase(text):
        return result
    
    # ALWAYS try ALL THREE converters regardless of detected language
    # This protects against incorrect language detection and mixed scripts
    
    # Try Urdu converter (for actual Urdu words)
    preprocessed_urdu = preprocess_urdu_text(text)
    urdu_amount = convert_urdu_amount(preprocessed_urdu)
    
    # Try English converter (for English words)
    preprocessed_english = preprocess_english_text(text)
    english_amount = convert_english_amount(preprocessed_english)
    
    # Try Roman Urdu converter (for English words written in Urdu script)
    # Note: convert first, then preprocess for display
    roman_urdu_amount = convert_roman_urdu_amount(text)
    preprocessed_roman_urdu = preprocess_roman_urdu_text(text)
    
    # Helper function to detect Urdu characters in text
    def has_urdu_chars(txt: str) -> bool:
        """Check if text contains Urdu/Arabic script characters"""
        urdu_range = range(0x0600, 0x06FF)  # Arabic/Urdu Unicode range
        return any(ord(char) in urdu_range for char in txt)
    
    # Determine which amount to use with intelligent heuristics
    # Priority: Roman Urdu (if has Urdu chars) > Urdu > English
    
    # Check if text has Urdu script
    text_has_urdu_script = has_urdu_chars(text)
    
    # Collect all found amounts
    amounts_found = []
    if roman_urdu_amount is not None:
        amounts_found.append(('roman_urdu', roman_urdu_amount, preprocessed_roman_urdu))
    if urdu_amount is not None:
        amounts_found.append(('urdu', urdu_amount, preprocessed_urdu))
    if english_amount is not None:
        amounts_found.append(('english', english_amount, preprocessed_english))
    
    # If no amounts found
    if not amounts_found:
        return result
    
    # If text has Urdu script, prefer Urdu converter first, then Roman Urdu
    if text_has_urdu_script:
        # Try Urdu converter first (actual Urdu words like "دو لاکھ")
        if urdu_amount is not None:
            result['amount'] = urdu_amount
            result['source'] = 'urdu'
            result['actual_language'] = 'urdu'
            result['preprocessed_text'] = preprocessed_urdu
            
            # Check for language mismatch
            if language.lower() != 'urdu':
                result['language_mismatch'] = True
        
        # Otherwise try Roman Urdu converter (English words in Urdu script like "ٹین")
        elif roman_urdu_amount is not None:
            result['amount'] = roman_urdu_amount
            result['source'] = 'roman_urdu'
            result['actual_language'] = 'urdu'
            result['preprocessed_text'] = preprocessed_roman_urdu
            
            # Check for language mismatch
            if language.lower() != 'urdu':
                result['language_mismatch'] = True
        
        # Fallback to English if available
        elif english_amount is not None:
            result['amount'] = english_amount
            result['source'] = 'english'
            result['actual_language'] = 'english'
            result['preprocessed_text'] = preprocessed_english
            
            # Mismatch: English amount but Urdu script present
            result['language_mismatch'] = True
    
    else:
        # No Urdu script - use English converter
        if english_amount is not None:
            result['amount'] = english_amount
            result['source'] = 'english'
            result['actual_language'] = 'english'
            result['preprocessed_text'] = preprocessed_english
            
            # Check for language mismatch
            if language.lower() == 'urdu':
                result['language_mismatch'] = True
        
        # Fallback to others if English didn't find anything
        elif urdu_amount is not None:
            result['amount'] = urdu_amount
            result['source'] = 'urdu'
            result['actual_language'] = 'urdu'
            result['preprocessed_text'] = preprocessed_urdu
            result['language_mismatch'] = True  # No Urdu script but Urdu amount found
        
        elif roman_urdu_amount is not None:
            result['amount'] = roman_urdu_amount
            result['source'] = 'roman_urdu'
            result['actual_language'] = 'urdu'
            result['preprocessed_text'] = preprocessed_roman_urdu
            result['language_mismatch'] = True  # No Urdu script but found Roman Urdu
    
    return result


def verify_amount_with_llm(
    transcript: str,
    extracted_amount: Optional[Union[int, float]],
    language: str,
    intent: str,
    preprocessed_text: str = ""
) -> dict:
    """
    Use GPT-4o-mini to verify and potentially correct the extracted amount.
    
    This hybrid approach combines rule-based extraction with LLM intelligence to:
    - Validate that the extracted amount makes sense in context
    - Catch semantic errors that regex might miss
    - Handle ambiguous cases better
    - Provide confidence scoring
    
    Args:
        transcript: Original transcribed text
        extracted_amount: Amount extracted by rule-based system (or None)
        language: Detected language ('english', 'urdu', etc.)
        intent: Detected intent ('mobile_topup', 'send_money', 'pay_bill', etc.)
        preprocessed_text: Text after numeric conversion (optional)
    
    Returns:
        dict: {
            'verified_amount': Final amount after LLM verification,
            'confidence': 'high', 'medium', or 'low',
            'llm_corrected': True if LLM changed the amount,
            'llm_reasoning': Why LLM made the decision,
            'original_amount': The original extracted amount
        }
    """
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Prepare context information
        context_info = f"""
Original Transcript: {transcript}
Detected Language: {language}
Intent Type: {intent}
Rule-based Extracted Amount: {extracted_amount if extracted_amount is not None else "None (no amount found)"}
"""
        
        if preprocessed_text and preprocessed_text != transcript:
            context_info += f"Preprocessed Text (numbers converted): {preprocessed_text}\n"
        
        # Construct prompt for GPT
        prompt = f"""You are an expert at extracting and verifying monetary amounts from Pakistani banking voice commands.

{context_info}

Your task:
1. Analyze if the rule-based extracted amount ({extracted_amount}) is reasonable given the transcript and context
2. If the extracted amount seems correct, confirm it
3. If the extracted amount seems wrong or is None, extract the correct amount from the transcript
4. Handle Urdu/Roman Urdu numeric expressions (e.g., "پانچ ہزار", "paanch hazaar", "five thousand" all mean 5000)

Critical rules:
- If transcript clearly states an amount and extracted amount matches, confirm it
- If extracted amount is None but transcript has an amount, provide the correct amount
- If extracted amount exists but doesn't match transcript, correct it
- If no amount mentioned in transcript at all, return None
- Consider action phrases: "بھر دو" (do it) where "دو" is NOT the number "two"

Respond ONLY with valid JSON in this exact format:
{{
    "verified_amount": <number or null>,
    "confidence": "<high|medium|low>",
    "llm_corrected": <true|false>,
}}

Examples:
- If transcript says "پانچ ہزار روپے بھیجو" and extracted 5000 → {{"verified_amount": 5000, "confidence": "high", "llm_corrected": false}}
- If transcript says "mobile topup of fifty" and extracted None → {{"verified_amount": 50, "confidence": "medium", "llm_corrected": true}}
- If transcript says "بل بھر دو" and extracted 2 → {{"verified_amount": null, "confidence": "high", "llm_corrected": true}}
"""
        
        # Call GPT-4o-mini
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert amount extraction validator for Pakistani banking systems. You understand Urdu, Roman Urdu, and English numeric expressions. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Low temperature for consistency
            max_tokens=200,
            service_tier="priority"
        )
        
        # Parse response
        llm_response = response.choices[0].message.content.strip()
        
        # Extract JSON from response (in case GPT adds extra text)
        json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
        if json_match:
            llm_response = json_match.group()
        
        result = json.loads(llm_response)
        
        # Add original amount to result
        result['original_amount'] = extracted_amount
        
        # Validate result structure
        if 'verified_amount' not in result:
            result['verified_amount'] = extracted_amount
            result['confidence'] = 'low'
            result['llm_corrected'] = False
        
        # Normalize confidence values
        if result.get('confidence') not in ['high', 'medium', 'low']:
            result['confidence'] = 'medium'
        
        log(f"  Confidence: {result['confidence']}")
        return result
        
    except json.JSONDecodeError as e:
        log(f"✗ LLM verification failed - JSON parse error: {e}")
        log(f"  LLM Response: {llm_response}")
        return {
            'verified_amount': extracted_amount,
            'confidence': 'low',
            'llm_corrected': False,
            'reasoning': f'JSON parse error: {str(e)}',
            'original_amount': extracted_amount
        }
    
    except Exception as e:
        log(f"✗ LLM verification failed: {e}")
        # Fallback to original extraction
        return {
            'verified_amount': extracted_amount,
            'confidence': 'low',
            'llm_corrected': False,
            'reasoning': f'LLM verification error: {str(e)}',
            'original_amount': extracted_amount
        }