"""
English Numeric Converter Utility

This module provides comprehensive conversion functions for English spoken numbers,
number words, and mixed numeric expressions commonly used in banking contexts.
"""

import re
from typing import Union, Optional, Dict, List


class EnglishNumericConverter:
    """Converts English number words and spoken numbers to Western digits."""
    
    def __init__(self):
        # Basic number mappings (0-19)
        self.basic_numbers = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
            'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
            'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
            'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19
        }
        
        # Tens (20-90)
        self.tens = {
            'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
            'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90
        }
        
        # Numbers from 21-99 (all explicitly defined)
        self.twenties_thirties = {
            # Twenty series (21-29)
            'twenty one': 21, 'twenty-one': 21,
            'twenty two': 22, 'twenty-two': 22,
            'twenty three': 23, 'twenty-three': 23,
            'twenty four': 24, 'twenty-four': 24,
            'twenty five': 25, 'twenty-five': 25,
            'twenty six': 26, 'twenty-six': 26,
            'twenty seven': 27, 'twenty-seven': 27,
            'twenty eight': 28, 'twenty-eight': 28,
            'twenty nine': 29, 'twenty-nine': 29,
            
            # Thirty series (31-39)
            'thirty one': 31, 'thirty-one': 31,
            'thirty two': 32, 'thirty-two': 32,
            'thirty three': 33, 'thirty-three': 33,
            'thirty four': 34, 'thirty-four': 34,
            'thirty five': 35, 'thirty-five': 35,
            'thirty six': 36, 'thirty-six': 36,
            'thirty seven': 37, 'thirty-seven': 37,
            'thirty eight': 38, 'thirty-eight': 38,
            'thirty nine': 39, 'thirty-nine': 39,
        }
        
        self.forties_fifties = {
            # Forty series (41-49)
            'forty one': 41, 'forty-one': 41,
            'forty two': 42, 'forty-two': 42,
            'forty three': 43, 'forty-three': 43,
            'forty four': 44, 'forty-four': 44,
            'forty five': 45, 'forty-five': 45,
            'forty six': 46, 'forty-six': 46,
            'forty seven': 47, 'forty-seven': 47,
            'forty eight': 48, 'forty-eight': 48,
            'forty nine': 49, 'forty-nine': 49,
            
            # Fifty series (51-59)
            'fifty one': 51, 'fifty-one': 51,
            'fifty two': 52, 'fifty-two': 52,
            'fifty three': 53, 'fifty-three': 53,
            'fifty four': 54, 'fifty-four': 54,
            'fifty five': 55, 'fifty-five': 55,
            'fifty six': 56, 'fifty-six': 56,
            'fifty seven': 57, 'fifty-seven': 57,
            'fifty eight': 58, 'fifty-eight': 58,
            'fifty nine': 59, 'fifty-nine': 59,
        }
        
        self.sixties_seventies = {
            # Sixty series (61-69)
            'sixty one': 61, 'sixty-one': 61,
            'sixty two': 62, 'sixty-two': 62,
            'sixty three': 63, 'sixty-three': 63,
            'sixty four': 64, 'sixty-four': 64,
            'sixty five': 65, 'sixty-five': 65,
            'sixty six': 66, 'sixty-six': 66,
            'sixty seven': 67, 'sixty-seven': 67,
            'sixty eight': 68, 'sixty-eight': 68,
            'sixty nine': 69, 'sixty-nine': 69,
            
            # Seventy series (71-79)
            'seventy one': 71, 'seventy-one': 71,
            'seventy two': 72, 'seventy-two': 72,
            'seventy three': 73, 'seventy-three': 73,
            'seventy four': 74, 'seventy-four': 74,
            'seventy five': 75, 'seventy-five': 75,
            'seventy six': 76, 'seventy-six': 76,
            'seventy seven': 77, 'seventy-seven': 77,
            'seventy eight': 78, 'seventy-eight': 78,
            'seventy nine': 79, 'seventy-nine': 79,
        }
        
        self.eighties_nineties = {
            # Eighty series (81-89)
            'eighty one': 81, 'eighty-one': 81,
            'eighty two': 82, 'eighty-two': 82,
            'eighty three': 83, 'eighty-three': 83,
            'eighty four': 84, 'eighty-four': 84,
            'eighty five': 85, 'eighty-five': 85,
            'eighty six': 86, 'eighty-six': 86,
            'eighty seven': 87, 'eighty-seven': 87,
            'eighty eight': 88, 'eighty-eight': 88,
            'eighty nine': 89, 'eighty-nine': 89,
            
            # Ninety series (91-99)
            'ninety one': 91, 'ninety-one': 91,
            'ninety two': 92, 'ninety-two': 92,
            'ninety three': 93, 'ninety-three': 93,
            'ninety four': 94, 'ninety-four': 94,
            'ninety five': 95, 'ninety-five': 95,
            'ninety six': 96, 'ninety-six': 96,
            'ninety seven': 97, 'ninety-seven': 97,
            'ninety eight': 98, 'ninety-eight': 98,
            'ninety nine': 99, 'ninety-nine': 99,
        }
        
        # Combine all compound numbers (21-99)
        self.compound_numbers = {
            **self.twenties_thirties,
            **self.forties_fifties,
            **self.sixties_seventies,
            **self.eighties_nineties
        }
        
        # Multipliers
        self.multipliers = {
            'hundred': 100,
            'thousand': 1000,
            'lakh': 100000,
            'lakhs': 100000,
            'million': 1000000,
            'crore': 10000000,
            'crores': 10000000,
            'billion': 1000000000,
        }
        
        # All number words combined
        self.all_number_words = {**self.basic_numbers, **self.tens, **self.compound_numbers}
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        # Pattern for all number words (case insensitive)
        number_words = list(self.basic_numbers.keys()) + list(self.tens.keys())
        number_pattern = '|'.join(re.escape(word) for word in number_words)
        self.number_regex = re.compile(f'\\b({number_pattern})\\b', re.IGNORECASE)
        
        # Pattern for multipliers
        multiplier_pattern = '|'.join(re.escape(word) for word in self.multipliers.keys())
        self.multiplier_regex = re.compile(f'\\b({multiplier_pattern})\\b', re.IGNORECASE)
        
        # Pattern for compound numbers (with hyphen)
        compound_pattern = '|'.join(re.escape(word) for word in self.compound_numbers.keys())
        self.compound_regex = re.compile(f'\\b({compound_pattern})\\b', re.IGNORECASE)
    
    def _apply_fuzzy_corrections(self, text: str) -> str:
        """Apply fuzzy matching corrections for common speech-to-text errors."""
        fuzzy_corrections = {
            # Common mispronunciations and variations
            'won': 'one',
            'tree': 'three',
            'fore': 'four',
            'tin': 'ten',
            
            # Plural variations
            'hundreds': 'hundred',
            'thousands': 'thousand',
            'millions': 'million',
            'billions': 'billion',
            
            # Common compound errors (multi-word - process these first)
            'twenty won': 'twenty one',
            'thirty to': 'thirty two',
            'forty for': 'forty four',
            'fifty ate': 'fifty eight',
        }
        
        result = text.lower()
        for incorrect, correct in fuzzy_corrections.items():
            result = re.sub(rf'\b{re.escape(incorrect)}\b', correct, result, flags=re.IGNORECASE)
        
        return result
    
    def words_to_number(self, text: str) -> Optional[int]:
        """
        Convert English number words to numeric value.
        Handles complex expressions like "two hundred fifty thousand three hundred twenty one"
        or "twelve lakh fifteen thousand six hundred thirty five"
        
        Args:
            text: Text containing English number words
            
        Returns:
            Numeric value or None if no valid number found
        """
        if not text or not isinstance(text, str):
            return None
        
        # Apply fuzzy corrections
        text = self._apply_fuzzy_corrections(text)
        
        # Replace hyphens with spaces to handle compound numbers like "twenty-one"
        text = text.replace('-', ' ')
        
        # Split into words
        words = text.lower().split()
        
        total = 0
        current = 0
        
        i = 0
        while i < len(words):
            word = words[i]
            
            # Skip common filler words
            if word in ['and', 'a', 'the', 'rupees', 'rupee', 'rs', 'dollars', 'dollar']:
                i += 1
                continue
            
            # Check for basic numbers (0-19)
            if word in self.basic_numbers:
                current += self.basic_numbers[word]
                i += 1
            
            # Check for tens (20-90)
            elif word in self.tens:
                current += self.tens[word]
                i += 1
                
                # Check if followed by ones digit (for compound like "thirty five")
                if i < len(words) and words[i] in self.basic_numbers and self.basic_numbers[words[i]] < 10:
                    current += self.basic_numbers[words[i]]
                    i += 1
            
            # Check for multipliers
            elif word in self.multipliers:
                multiplier = self.multipliers[word]
                
                if multiplier == 100:
                    # Hundred: multiply current by 100
                    if current == 0:
                        current = 100
                    else:
                        current *= 100
                    # DON'T add to total yet - continue parsing for possible tens/ones
                    # Example: "six hundred thirty five" should be 635, not 600 + 35
                else:
                    # Thousand, million, billion, lakh, crore: multiply and add to total
                    if current == 0:
                        current = multiplier
                    else:
                        current *= multiplier
                    total += current
                    current = 0
                
                i += 1
            
            else:
                i += 1
        
        # Add any remaining current value
        total += current
        
        # Return the total, including 0 if explicitly stated
        if total > 0 or (total == 0 and 'zero' in text.lower()):
            return total
        return None
    
    def extract_number_from_text(self, text: str) -> Optional[Union[int, float]]:
        """
        Extract number from text that may contain number words or digits.
        
        Args:
            text: Input text
            
        Returns:
            Numeric value or None if no valid number found
        """
        if not text or not isinstance(text, str):
            return None
        
        # Clean the text first
        cleaned_text = self._clean_amount_text(text)
        
        # Try to extract digit-based numbers first
        digit_amount = self._extract_numeric_value(cleaned_text)
        if digit_amount is not None:
            return digit_amount
        
        # Try to extract word-based numbers
        word_amount = self.words_to_number(cleaned_text)
        if word_amount is not None:
            return word_amount
        
        return None
    
    def _clean_amount_text(self, text: str) -> str:
        """Clean text by removing currency symbols and other non-numeric characters."""
        # Remove common currency symbols and words
        currency_patterns = [
            r'[Rr][Ss]\.?\s*',  # Rs, Rs., rs, etc.
            r'[Rr]upees?\s*',    # Rupee, Rupees
            r'\$\s*',            # Dollar sign
            r'[Dd]ollars?\s*',   # Dollar, Dollars
            r'[Uu][Ss][Dd]\s*',  # USD
            r'[Pp]akistani\s+[Rr]upees?\s*',  # Pakistani Rupees
            r'[Pp][Kk][Rr]\s*',  # PKR
            r'€\s*',             # Euro sign
            r'[Ee]uros?\s*',     # Euro, Euros
            r'£\s*',             # Pound sign
            r'[Pp]ounds?\s*',    # Pound, Pounds
        ]
        
        cleaned = text
        for pattern in currency_patterns:
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
        
        # Remove commas and extra spaces
        cleaned = re.sub(r'[,\s]+', ' ', cleaned)
        
        return cleaned.strip()
    
    def _extract_numeric_value(self, text: str) -> Optional[Union[int, float]]:
        """Extract numeric value from cleaned text containing digits."""
        # Pattern 1: Numbers with k/K (thousands)
        k_pattern = re.search(r'\b(\d+(?:\.\d+)?)\s*[kK]\b', text)
        if k_pattern:
            try:
                return float(k_pattern.group(1)) * 1000
            except ValueError:
                pass
        
        # Pattern 2: Numbers with m/M (millions)
        m_pattern = re.search(r'\b(\d+(?:\.\d+)?)\s*[mM]\b', text)
        if m_pattern:
            try:
                return float(m_pattern.group(1)) * 1000000
            except ValueError:
                pass
        
        # Pattern 3: Numbers with b/B (billions)
        b_pattern = re.search(r'\b(\d+(?:\.\d+)?)\s*[bB]\b', text)
        if b_pattern:
            try:
                return float(b_pattern.group(1)) * 1000000000
            except ValueError:
                pass
        
        # Pattern 4: Numbers with lakh/lakhs
        lakh_pattern = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:lakh|lakhs)\b', text, re.IGNORECASE)
        if lakh_pattern:
            try:
                return float(lakh_pattern.group(1)) * 100000
            except ValueError:
                pass
        
        # Pattern 5: Numbers with crore/crores
        crore_pattern = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:crore|crores)\b', text, re.IGNORECASE)
        if crore_pattern:
            try:
                return float(crore_pattern.group(1)) * 10000000
            except ValueError:
                pass
        
        # Pattern 6: Numbers with million/millions
        million_pattern = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:million|millions)\b', text, re.IGNORECASE)
        if million_pattern:
            try:
                return float(million_pattern.group(1)) * 1000000
            except ValueError:
                pass
        
        # Pattern 7: Numbers with billion/billions
        billion_pattern = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:billion|billions)\b', text, re.IGNORECASE)
        if billion_pattern:
            try:
                return float(billion_pattern.group(1)) * 1000000000
            except ValueError:
                pass
        
        # Pattern 8: Numbers with thousand/thousands
        thousand_pattern = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:thousand|thousands)\b', text, re.IGNORECASE)
        if thousand_pattern:
            try:
                return float(thousand_pattern.group(1)) * 1000
            except ValueError:
                pass
        
        # Pattern 9: Complex expressions like "2 million 500 thousand"
        complex_million_pattern = re.search(
            r'\b(\d+)\s*(?:million|millions)\s*(\d+)\s*(?:thousand|thousands)\b', 
            text, 
            re.IGNORECASE
        )
        if complex_million_pattern:
            try:
                million_part = float(complex_million_pattern.group(1)) * 1000000
                thousand_part = float(complex_million_pattern.group(2)) * 1000
                return million_part + thousand_part
            except ValueError:
                pass
        
        # Pattern 10: Decimal numbers
        decimal_pattern = re.search(r'\b(\d+\.\d+)\b', text)
        if decimal_pattern:
            try:
                return float(decimal_pattern.group(1))
            except ValueError:
                pass
        
        # Pattern 11: Simple integers (check this last)
        # If multiple numbers found, prefer larger ones as they're more likely to be amounts
        all_numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', text)
        if all_numbers:
            try:
                numbers = [float(num) for num in all_numbers]
                
                # Filter out phone numbers and other context numbers
                filtered_numbers = []
                for num in numbers:
                    # Skip numbers that are part of phone numbers
                    if self._is_phone_number_context(num, text):
                        continue
                    filtered_numbers.append(num)
                
                if filtered_numbers:
                    # Filter out very small numbers (1, 2) unless they're the only numbers
                    # These are often context words like "one task" or "two people"
                    if len(filtered_numbers) > 1:
                        # If multiple numbers, prefer larger ones
                        larger_numbers = [num for num in filtered_numbers if num >= 10]
                        if larger_numbers:
                            return max(larger_numbers)  # Return the largest reasonable amount
                        else:
                            return max(filtered_numbers)  # If all are small, return the largest
                    else:
                        return filtered_numbers[0]  # Only one number found
                else:
                    # If all numbers were filtered out, return the original logic
                    if len(numbers) > 1:
                        larger_numbers = [num for num in numbers if num >= 10]
                        if larger_numbers:
                            return max(larger_numbers)
                        else:
                            return max(numbers)
                    else:
                        return numbers[0]
            except ValueError:
                pass
        
        return None
    
    def _is_phone_number_context(self, number: float, text: str) -> bool:
        """
        Check if a number is part of a phone number context.
        
        Args:
            number: The number to check
            text: The full text containing the number
            
        Returns:
            True if the number appears to be part of a phone number
        """
        import re
        
        # Convert number to string for pattern matching
        num_str = str(int(number)) if number.is_integer() else str(number)
        
        # Phone number patterns - be more specific
        phone_patterns = [
            r'\b\d{3,4}[-.]?\d{3}[-.]?\d{4}\b',  # 0342-355-1182 or 03423551182
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',    # 342-355-1182
            r'\b\d{4}[-.]?\d{3}[-.]?\d{4}\b',    # 0342-355-1182
            r'\+\d{1,3}[-.]?\d{3,4}[-.]?\d{3}[-.]?\d{4}\b',  # +92-342-355-1182
            r'\b\d{10,15}\b',  # Long sequences of digits (10-15 digits)
        ]
        
        # Check if the number appears in any phone number pattern
        for pattern in phone_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if num_str in match.group():
                    return True
        
        # Additional heuristics for phone numbers - be more specific
        # Look for context words that are specifically about phone numbers
        phone_context_patterns = [
            r'\b(?:phone|mobile|contact|call|dial)\s+(?:number\s+)?\d+[-.]?\d+[-.]?\d+\b',
            r'\bnumber\s+\d{3,4}[-.]?\d{3}[-.]?\d{4}\b',
            r'\b\d{3,4}[-.]?\d{3}[-.]?\d{4}\s+(?:number|phone|mobile)\b',
        ]
        
        for pattern in phone_context_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Check if our number is part of this pattern
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if num_str in match.group():
                        return True
        
        return False
    
    def convert_all_numerals(self, text: str) -> str:
        """
        Convert all English number words in text to digits.
        
        Args:
            text: Input text containing English number words
            
        Returns:
            Text with number words converted to digits
        """
        if not text or not isinstance(text, str):
            return text
        
        # Don't apply fuzzy corrections in general text to avoid changing "to" to "two", etc.
        result = text
        
        # Split into sentences to handle each separately
        sentences = re.split(r'([.!?])', result)
        converted_sentences = []
        
        for sentence in sentences:
            # Find all number phrases in the sentence
            words = sentence.split()
            converted_words = []
            i = 0
            
            while i < len(words):
                word = words[i].lower().strip(',;:').replace('-', ' ')
                
                # Check if this word starts a number phrase (including compound numbers)
                if (word in self.basic_numbers or word in self.tens or 
                    word in self.multipliers or word in self.compound_numbers):
                    # Collect consecutive number words
                    number_phrase = []
                    j = i
                    while j < len(words):
                        w = words[j].lower().strip(',;:').replace('-', ' ')
                        if (w in self.basic_numbers or w in self.tens or 
                            w in self.multipliers or w in self.compound_numbers or 
                            w in ['and', 'a']):
                            number_phrase.append(words[j].strip(',;:'))
                            j += 1
                        else:
                            break
                    
                    # Convert the number phrase
                    phrase_text = ' '.join(number_phrase)
                    number_value = self.words_to_number(phrase_text)
                    
                    if number_value is not None:
                        converted_words.append(str(number_value))
                        i = j
                    else:
                        converted_words.append(words[i])
                        i += 1
                else:
                    converted_words.append(words[i])
                    i += 1
            
            converted_sentences.append(' '.join(converted_words))
        
        return ''.join(converted_sentences)
    
    def get_english_numeric_examples(self) -> Dict[str, int]:
        """Get examples of English numeric expressions for testing."""
        return {
            # Basic numbers
            "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
            "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
            
            # Teen numbers
            "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
            "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
            
            # Tens
            "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
            "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
            
            # Compound numbers
            "twenty one": 21, "thirty-five": 35, "forty two": 42, "ninety-nine": 99,
            
            # Hundreds
            "one hundred": 100, "two hundred": 200, "five hundred": 500,
            "nine hundred": 900,
            
            # Thousands
            "one thousand": 1000, "five thousand": 5000, "ten thousand": 10000,
            "fifty thousand": 50000, "ninety thousand": 90000,
            
            # Complex numbers
            "one hundred twenty three": 123,
            "five hundred forty five": 545,
            "two thousand five hundred": 2500,
            "ten thousand five hundred": 10500,
            "twenty five thousand": 25000,
            "one hundred thousand": 100000,
            
            # Lakhs and crores (South Asian numbering)
            "one lakh": 100000, "five lakhs": 500000,
            "one crore": 10000000, "ten crores": 100000000,
            
            # Millions and billions
            "one million": 1000000, "five million": 5000000,
            "one billion": 1000000000,
            
            # Very complex numbers
            "two hundred fifty thousand": 250000,
            "three hundred twenty thousand": 320000,
            "one million five hundred thousand": 1500000,
            "two million three hundred thousand": 2300000,
        }


# Global instance for easy import
english_converter = EnglishNumericConverter()


def convert_english_amount(text: str) -> Optional[Union[int, float]]:
    """
    Convenience function to convert English amount text to numeric value.
    
    Args:
        text: Text containing English number words or digits
        
    Returns:
        Numeric value or None if no valid amount found
    """
    return english_converter.extract_number_from_text(text)


def preprocess_english_text(text: str) -> str:
    """
    Preprocess text by converting all English number words to digits.
    
    Args:
        text: Input text that may contain English number words
        
    Returns:
        Text with all number words converted to digits
    """
    return english_converter.convert_all_numerals(text)


if __name__ == "__main__":
    # Test the converter
    converter = EnglishNumericConverter()
    
    test_cases = [
        "five thousand rupees",
        "50k",
        "fifty thousand",
        "two hundred fifty thousand",
        "one lakh",
        "five lakhs",
        "one million",
        "two million five hundred thousand",
        "twenty one",
        "one hundred twenty three",
        "five hundred forty five dollars",
        "ten thousand five hundred",
    ]
    
    print("Testing English Numeric Converter:")
    print("=" * 60)
    
    for test_case in test_cases:
        result = converter.extract_number_from_text(test_case)
        print(f"Input: '{test_case}' -> Output: {result}")
    
    print("\n" + "=" * 60)
    print("Testing word to number conversion:")
    print("=" * 60)
    
    for example, expected in converter.get_english_numeric_examples().items():
        result = converter.words_to_number(example)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{example}' -> {result} (expected: {expected})")

