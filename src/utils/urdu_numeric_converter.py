"""
Urdu Numeric Converter Utility

This module provides comprehensive conversion functions for Urdu numerals,
spoken numbers, and mixed language numeric expressions commonly used in
Pakistani banking contexts.
"""

import re
from typing import Union, Optional, Dict, List


class UrduNumericConverter:
    """Converts Urdu numerals, spoken numbers, and mixed expressions to Western digits."""
    
    def __init__(self):
        # Urdu digit mappings
        self.urdu_digits = {
            '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
            '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
        }
        
        # Hindi/Devanagari digit mappings (sometimes used in Urdu contexts)
        self.hindi_digits = {
            '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
            '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
        }
        
        # Urdu spoken number mappings
        self.urdu_spoken_numbers = {
            # Basic numbers (0-9)
            'صفر': '0', 'ایک': '1', 'دو': '2', 'تین': '3', 'چار': '4',
            'پانچ': '5', 'چھ': '6', 'سات': '7', 'آٹھ': '8', 'نو': '9',
            
            # Teen numbers (10-19)
            'دس': '10', 'گیارہ': '11', 'بارہ': '12', 'تیرہ': '13', "تریپن": "13", 'چودہ': '14',
            'پندرہ': '15', 'سولہ': '16', 'سترہ': '17', 'اٹھارہ': '18', "اٹھار": "18", 'انیس': '19',
            
            # Tens (20-90)
            'بیس': '20', 'اکیس': '21', 'بائیس': '22', 'تئیس': '23', 'چوبیس': '24',
            'پچیس': '25', 'چھبیس': '26', 'ستائیس': '27', 'اٹھائیس': '28', 'انتیس': '29',
            'تیس': '30', 'اکتیس': '31', 'بتیس': '32', 'تینتیس': '33', 'چونتیس': '34',
            'پینتیس': '35', 'چھتیس': '36', 'سینتیس': '37', 'اڑتیس': '38', 'انتالیس': '39',
            'چالیس': '40', 'اکتالیس': '41', 'بیتالیس': '42', 'تینتالیس': '43', 'چوالیس': '44',
            'پینتالیس': '45', 'چھیالیس': '46', 'سینتالیس': '47', 'اڑتالیس': '48', 'انچاس': '49',
            'پچاس': '50', 'اکیاون': '51', 'باون': '52', 'ترپن': '53', 'چون': '54', 'چونپن': '54',
            'پچپن': '55', 'چھپن': '56', 'ستاون': '57', 'اٹھاون': '58', 'انسٹھ': '59',
            'ساٹھ': '60', 'اکسٹھ': '61', 'باسٹھ': '62', 'ترسٹھ': '63', 'چوسٹھ': '64', 'چونسٹھ': '64', 
            'پینسٹھ': '65', 'چھیاسٹھ': '66', 'سڑسٹھ': '67', 'اڑسٹھ': '68', 'انہتر': '69',
            'ستر': '70', 'اکہتر': '71', 'بہتر': '72', 'تہتر': '73', 'چوہتر': '74', 'پچھتر': '75', "پچتھر": "75",
            'پچہتر': '75', 'چھہتر': '76', 'ستتر': '77', 'ستتر': '77', 'اٹھتر': '78', 'اناسی': '79',
            'اسی': '80', 'اکیاسی': '81', 'بیاسی': '82', 'تراسی': '83', 'چوراسی': '84',
            'پچاسی': '85', 'چھیاسی': '86', 'ستاسی': '87', 'اٹھاسی': '88', 'انواسی': '89',
            'نوے': '90', 'اکانوے': '91', 'بانوے': '92', 'بانویں': '92', 'ترانوے': '93', 'چورانوے': '94',
            'پچانوے': '95', 'چھیانوے': '96', 'ستانوے': '97', 'اٹھانوے': '98', 'ننانوے': '99',
            
            # Hundreds
            'سو': '100', 'ایک سو': '100', 'دو سو': '200', 'تین سو': '300',
            'چار سو': '400', 'پانچ سو': '500', 'چھ سو': '600',
            'سات سو': '700', 'آٹھ سو': '800', 'نو سو': '900',
            
            # Thousands
            'ہزار': '1000', 'ایک ہزار': '1000', 'دو ہزار': '2000',
            'تین ہزار': '3000', 'چار ہزار': '4000', 'پانچ ہزار': '5000',
            'چھ ہزار': '6000', 'سات ہزار': '7000', 'آٹھ ہزار': '8000',
            'نو ہزار': '9000', 'دس ہزار': '10000', 'بیس ہزار': '20000',
            'تیس ہزار': '30000', 'چالیس ہزار': '40000', 'پچاس ہزار': '50000',
            'ساٹھ ہزار': '60000', 'ستر ہزار': '70000', 'اسی ہزار': '80000',
            'نوے ہزار': '90000',
            
            # Lakhs (100,000)
            'لاکھ': '100000', 'ایک لاکھ': '100000', 'دو لاکھ': '200000',
            'تین لاکھ': '300000', 'چار لاکھ': '400000', 'پانچ لاکھ': '500000',
            'چھ لاکھ': '600000', 'سات لاکھ': '700000', 'آٹھ لاکھ': '800000',
            'نو لاکھ': '900000',
            
            # Crores (10,000,000)
            'کروڑ': '10000000', 'ایک کروڑ': '10000000', 'دو کروڑ': '20000000',
            'تین کروڑ': '30000000', 'چار کروڑ': '40000000', 'پانچ کروڑ': '50000000',
            
            # Millions (1,000,000) - English words sometimes used in Urdu context
            'ملین': '1000000', 'ایک ملین': '1000000', 'دو ملین': '2000000',
            'تین ملین': '3000000', 'چار ملین': '4000000', 'پانچ ملین': '5000000',
            
            # Mixed expressions
            'پچاس ہزار': '50000', 'پانچ لاکھ': '500000', 'ایک کروڑ': '10000000',
            'دو لاکھ پچاس ہزار': '250000', 'تین لاکھ بیس ہزار': '320000',
            'چار لاکھ پچاس ہزار': '450000', 'پانچ لاکھ ساٹھ ہزار': '560000',
            'چھ لاکھ ستر ہزار': '670000', 'سات لاکھ اسی ہزار': '780000',
            'آٹھ لاکھ نوے ہزار': '890000', 'نو لاکھ': '900000',
            
            # Common compound thousands (70s, 80s, 90s)
            'ستر ہزار': '70000', 'اکہتر ہزار': '71000', 'بہتر ہزار': '72000',
            'تہتر ہزار': '73000', 'چوہتر ہزار': '74000', 'پچہتر ہزار': '75000',
            'پچھتر ہزار': '75000', 'چھہتر ہزار': '76000', 'ستتر ہزار': '77000', 'اٹھتر ہزار': '78000',
            'اناسی ہزار': '79000', 'اسی ہزار': '80000', 'اکیاسی ہزار': '81000',
            'بیاسی ہزار': '82000', 'تراسی ہزار': '83000', 'چوراسی ہزار': '84000',
            'پچاسی ہزار': '85000', 'چھیاسی ہزار': '86000', 'ستاسی ہزار': '87000',
            'اٹھاسی ہزار': '88000', 'انواسی ہزار': '89000', 'نوے ہزار': '90000',
            
            # Common banking amounts
            'پانچ سو': '500', 'ایک ہزار': '1000', 'دو ہزار': '2000',
            'پانچ ہزار': '5000', 'دس ہزار': '10000', 'پچاس ہزار': '50000',
            'ایک لاکھ': '100000', 'دو لاکھ': '200000', 'پانچ لاکھ': '500000',
        }
        
        # Roman Urdu (Urdu written in English script) mappings
        self.roman_urdu_numbers = {
            # Basic numbers (0-9)
            'ek': '1', 'do': '2', 'teen': '3', 'char': '4', 'paanch': '5',
            'chh': '6', 'saat': '7', 'aath': '8', 'nau': '9',
            
            # Teen numbers (10-19)
            'das': '10', 'gyaarah': '11', 'baarah': '12', 'terah': '13', 'chaudah': '14',
            'pandrah': '15', 'solah': '16', 'satrah': '17', 'atharah': '18', 'unnees': '19',
            
            # Tens (20-90)
            'bees': '20', 'ikkees': '21', 'baaees': '22', 'teis': '23', 'chobees': '24',
            'pachees': '25', 'chhabbees': '26', 'sattaees': '27', 'athaees': '28', 'untees': '29',
            'tees': '30', 'iktees': '31', 'battees': '32', 'taintees': '33', 'chauntees': '34',
            'paintees': '35', 'chhattees': '36', 'saintees': '37', 'arttees': '38', 'untalis': '39',
            'chaalees': '40', 'iktalis': '41', 'baitis': '42', 'taintais': '43', 'chawalis': '44',
            'paintis': '45', 'chhiyais': '46', 'saintis': '47', 'artis': '48', 'unchas': '49',
            'pachaas': '50', 'ikyawn': '51', 'bawn': '52', 'terpann': '53', 'chawann': '54',
            'pachpann': '55', 'chhappan': '56', 'sattawan': '57', 'athawan': '58', 'unsath': '59',
            'saath': '60', 'iksath': '61', 'basath': '62', 'tirsath': '63', 'chausath': '64',
            'painsath': '65', 'chhiyasaath': '66', 'sarsath': '67', 'arsath': '68', 'unsath': '69',
            'sattar': '70', 'ikhattar': '71', 'bahattar': '72', 'tihattar': '73', 'chauhattar': '74',
            'pachhattar': '75', 'chhihattar': '76', 'sattattar': '77', 'athattar': '78', 'unasi': '79',
            'assi': '80', 'ikyaasi': '81', 'bayaasi': '82', 'tiraasi': '83', 'chauraasi': '84',
            'pachaasi': '85', 'chhiyaasi': '86', 'sattaasi': '87', 'athaasi': '88', 'unnaasi': '89',
            'navee': '90', 'ikyaanavee': '91', 'bayanavee': '92', 'tiranavee': '93', 'chauraanavee': '94',
            'pachaanavee': '95', 'chhiyaanavee': '96', 'sattaanavee': '97', 'athaanaavee': '98', 'ninaanavee': '99',
            'so': '100', 'hazaar': '1000', 'laakh': '100000', 'karor': '10000000',
            
            # Mixed expressions in Roman Urdu
            'pachaas hazaar': '50000', 'paanch laakh': '500000',
            'ek karor': '10000000', 'do laakh pachaas hazaar': '250000',
            'teen laakh bees hazaar': '320000', 'char laakh pachaas hazaar': '450000',
            'paanch laakh saath hazaar': '560000', 'chh laakh sattar hazaar': '670000',
            'saat laakh assi hazaar': '780000', 'aath laakh navee hazaar': '890000',
            'nau laakh': '900000',
        }
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        # Pattern for Urdu digits
        urdu_digit_pattern = '|'.join(re.escape(digit) for digit in self.urdu_digits.keys())
        self.urdu_digit_regex = re.compile(f'[{urdu_digit_pattern}]')
        
        # Pattern for Hindi digits
        hindi_digit_pattern = '|'.join(re.escape(digit) for digit in self.hindi_digits.keys())
        self.hindi_digit_regex = re.compile(f'[{hindi_digit_pattern}]')
        
        # Pattern for spoken numbers (case insensitive)
        spoken_pattern = '|'.join(re.escape(word) for word in self.urdu_spoken_numbers.keys())
        self.spoken_regex = re.compile(f'\\b({spoken_pattern})\\b', re.IGNORECASE)
        
        # Pattern for Roman Urdu numbers
        roman_pattern = '|'.join(re.escape(word) for word in self.roman_urdu_numbers.keys())
        self.roman_regex = re.compile(f'\\b({roman_pattern})\\b', re.IGNORECASE)
    
    def convert_urdu_digits(self, text: str) -> str:
        """Convert Urdu digits to Western digits."""
        result = text
        for urdu_digit, western_digit in self.urdu_digits.items():
            result = result.replace(urdu_digit, western_digit)
        return result
    
    def convert_hindi_digits(self, text: str) -> str:
        """Convert Hindi digits to Western digits."""
        result = text
        for hindi_digit, western_digit in self.hindi_digits.items():
            result = result.replace(hindi_digit, western_digit)
        return result
    
    def convert_spoken_numbers(self, text: str) -> str:
        """Convert spoken Urdu numbers to Western digits."""
        # Sort patterns by length (longest first) to ensure specific patterns match before general ones
        sorted_patterns = sorted(self.urdu_spoken_numbers.keys(), key=len, reverse=True)
        
        result = text
        for pattern in sorted_patterns:
            # Create word boundary pattern for each specific pattern
            pattern_regex = re.compile(r'\b' + re.escape(pattern) + r'\b', re.IGNORECASE)
            result = pattern_regex.sub(self.urdu_spoken_numbers[pattern], result)
        
        return result
    
    def convert_roman_urdu_numbers(self, text: str) -> str:
        """Convert Roman Urdu numbers to Western digits."""
        # Sort patterns by length (longest first) to ensure specific patterns match before general ones
        sorted_patterns = sorted(self.roman_urdu_numbers.keys(), key=len, reverse=True)
        
        result = text
        for pattern in sorted_patterns:
            # Create word boundary pattern for each specific pattern
            pattern_regex = re.compile(r'\b' + re.escape(pattern) + r'\b', re.IGNORECASE)
            result = pattern_regex.sub(self.roman_urdu_numbers[pattern], result)
        
        return result
    
    def _apply_fuzzy_corrections(self, text: str) -> str:
        """Apply fuzzy matching corrections for common Whisper transcription errors."""
        # Common transcription errors from Whisper for Urdu numbers
        fuzzy_corrections = {
            # Basic number mispronunciations (missing letters, extra letters, similar sounds)
            'ایکا': 'ایک',     # one
            'دوا': 'دو',       # two  
            'دون': 'دو',       # two
            'تینا': 'تین',     # three
            'تینہ': 'تین',     # three
            'چارا': 'چار',     # four
            'چارہ': 'چار',     # four
            'پانچا': 'پانچ',   # five
            'پانچہ': 'پانچ',   # five
            'چھا': 'چھ',       # six
            'چھہ': 'چھ',       # six
            'ساتا': 'سات',     # seven
            'ساتہ': 'سات',     # seven
            'آٹھا': 'آٹھ',     # eight
            'آٹھہ': 'آٹھ',     # eight
            'نوا': 'نو',       # nine
            'نوہ': 'نو',       # nine
            'دسا': 'دس',       # ten
            'دسہ': 'دس',       # ten
            
            # Hundred variations (missing 'ر', extra letters, similar sounds)
            'چاسو': 'چار سو',  # four hundred (missing 'ر')
            'چاسہ': 'چار سو',  # four hundred
            'چاسا': 'چار سو',  # four hundred
            'چھاسو': 'چھ سو',  # six hundred
            'چھاسہ': 'چھ سو',  # six hundred
            'چھاسا': 'چھ سو',  # six hundred
            'ساتسو': 'سات سو', # seven hundred
            'ساتسہ': 'سات سو', # seven hundred
            'ساتسا': 'سات سو', # seven hundred
            'آٹھسو': 'آٹھ سو', # eight hundred
            'آٹھسہ': 'آٹھ سو', # eight hundred
            'آٹھسا': 'آٹھ سو', # eight hundred
            'نوسو': 'نو سو',   # nine hundred
            'نوسہ': 'نو سو',   # nine hundred
            'نوسا': 'نو سو',   # nine hundred
            'ایکسو': 'ایک سو', # one hundred
            'ایکسہ': 'ایک سو', # one hundred
            'ایکسا': 'ایک سو', # one hundred
            'دوسو': 'دو سو',   # two hundred
            'دوسہ': 'دو سو',   # two hundred
            'دوسا': 'دو سو',   # two hundred
            'تینسو': 'تین سو', # three hundred
            'تینسہ': 'تین سو', # three hundred
            'تینسا': 'تین سو', # three hundred
            'پانچسو': 'پانچ سو', # five hundred
            'پانچسہ': 'پانچ سو', # five hundred
            'پانچسا': 'پانچ سو', # five hundred
            
            # Thousand variations (extra letters, missing letters)
            'ہزارا': 'ہزار',   # thousand
            'ہزارہ': 'ہزار',   # thousand
            'ہزاری': 'ہزار',   # thousand
            'ہزارو': 'ہزار',   # thousand
            'ہزارے': 'ہزار',   # thousand
            'ہزاری': 'ہزار',   # thousand
            'آدار': 'ہزار',   # thousand
            
            # Lakh variations
            'لاکھا': 'لاکھ',   # lakh
            'لاکھہ': 'لاکھ',   # lakh
            'لاکھی': 'لاکھ',   # lakh
            'لاکھو': 'لاکھ',   # lakh
            'لاکھے': 'لاکھ',   # lakh
            
            # Crore variations
            'کروڑا': 'کروڑ',   # crore
            'کروڑہ': 'کروڑ',   # crore
            'کروڑی': 'کروڑ',   # crore
            'کروڑو': 'کروڑ',   # crore
            'کروڑے': 'کروڑ',   # crore
            
            # Common spacing issues in compound numbers
            'دوہزار': 'دو ہزار',  # two thousand
            'تینہزار': 'تین ہزار', # three thousand
            'چارہزار': 'چار ہزار', # four thousand
            'پانچہزار': 'پانچ ہزار', # five thousand
            'دسہزار': 'دس ہزار', # ten thousand
            'بیسہزار': 'بیس ہزار', # twenty thousand
            
            # Roman Urdu variations
            'do hazaar': 'دو ہزار',
            'teen hazaar': 'تین ہزار',
            'char hazaar': 'چار ہزار',
            'paanch hazaar': 'پانچ ہزار',
            'das hazaar': 'دس ہزار',
            'bees hazaar': 'بیس ہزار',
            
            # Common Whisper errors for specific amounts
            'دین': 'دس',       # ten (Whisper sometimes hears 'دین' instead of 'دس')
            'گیارہ': 'گیارہ',   # eleven (usually correct)
            'بارہ': 'بارہ',     # twelve (usually correct)
            'تیرہ': 'تیرہ',     # thirteen (usually correct)
            'چودہ': 'چودہ',     # fourteen (usually correct)
            'پندرہ': 'پندرہ',   # fifteen (usually correct)
            'سولہ': 'سولہ',     # sixteen (usually correct)
            'سترہ': 'سترہ',     # seventeen (usually correct)
            'اٹھارہ': 'اٹھارہ', # eighteen (usually correct)
            'انیس': 'انیس',     # nineteen (usually correct)
            'بیس': 'بیس',       # twenty (usually correct)
            
            # Additional compound number corrections
            'پانچسو': 'پانچ سو', # five hundred
            'چھاسو': 'چھ سو',   # six hundred
            'ساتسو': 'سات سو',  # seven hundred
            'آٹھسو': 'آٹھ سو',  # eight hundred
            'نوسو': 'نو سو',    # nine hundred
        }
        
        result = text
        for incorrect, correct in fuzzy_corrections.items():
            result = result.replace(incorrect, correct)
        
        return result
    
    def extract_and_convert_amount(self, text: str) -> Optional[Union[int, float]]:
        """
        Extract and convert amount from text containing Urdu numerals.
        Returns the numeric value or None if no valid amount found.
        """
        if not text or not isinstance(text, str):
            return None
        
        # Step 0: Check if this is an action phrase that should return None
        if self._is_action_phrase(text):
            return None
        
        # Step 1: Convert all types of numerals
        converted_text = self.convert_all_numerals(text)
        
        # Step 2: Check for currency compound patterns BEFORE cleaning
        currency_compound_patterns = [
            r'\b(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*(?:rupees?|روپے?|rs?\.?)\b',  # "10 100000 12 1000 روپے"
            r'\b(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*(?:rupees?|روپے?|rs?\.?)\b',  # "1 100 12 روپے"
            r'\b(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*(?:rupees?|روپے?|rs?\.?)\b',  # "100 12 روپے"
        ]
        
        for pattern in currency_compound_patterns:
            currency_match = re.search(pattern, converted_text, re.IGNORECASE)
            if currency_match:
                try:
                    # For compound numbers near currency, handle multiplication and addition
                    groups = currency_match.groups()
                    if len(groups) == 2:  # "100 12 روپے" or "97 1000 روپے"
                        num1 = float(groups[0])
                        num2 = float(groups[1])
                        # If second number is a multiplier (1000, 100000, etc.), multiply
                        if num2 in [100, 1000, 100000, 1000000, 10000000]:
                            amount = num1 * num2
                        else:
                            # Otherwise, add them (e.g., "100 12" = 112)
                            amount = num1 + num2
                    elif len(groups) == 3:  # "1 100 12 روپے"
                        # This is likely "1 100" (hundred) + "12" = 112
                        if float(groups[0]) == 1 and float(groups[1]) == 100:
                            amount = float(groups[1]) + float(groups[2])  # 100 + 12 = 112
                        else:
                            amount = float(groups[0]) + float(groups[1]) + float(groups[2])
                    elif len(groups) == 4:  # "10 100000 12 1000 روپے"
                        # This is likely "10 100000" (10 lakh) + "12 1000" (12 thousand)
                        num1 = float(groups[0])
                        num2 = float(groups[1])
                        num3 = float(groups[2])
                        num4 = float(groups[3])
                        
                        # Calculate first compound: num1 * num2
                        if num2 in [100, 1000, 100000, 1000000, 10000000]:
                            amount1 = num1 * num2
                        else:
                            amount1 = num1 + num2
                        
                        # Calculate second compound: num3 * num4
                        if num4 in [100, 1000, 100000, 1000000, 10000000]:
                            amount2 = num3 * num4
                        else:
                            amount2 = num3 + num4
                        
                        # Add both compounds
                        amount = amount1 + amount2
                    else:
                        continue
                    
                    if amount > 0:  # Valid amount found
                        return amount
                except ValueError:
                    continue
        
        # Step 3: Clean the text (remove currency symbols, commas, etc.)
        cleaned_text = self._clean_amount_text(converted_text)
        
        # Step 4: Extract numeric value
        amount = self._extract_numeric_value(cleaned_text)
        
        return amount
    
    def convert_all_numerals(self, text: str) -> str:
        """Convert all types of numerals in the text."""
        # Apply fuzzy corrections FIRST to fix Whisper transcription errors
        result = self._apply_fuzzy_corrections(text)
        
        # Then convert in order: digits first, then spoken numbers
        result = self.convert_urdu_digits(result)
        result = self.convert_hindi_digits(result)
        result = self.convert_spoken_numbers(result)
        result = self.convert_roman_urdu_numbers(result)
        
        return result
    
    def _clean_amount_text(self, text: str) -> str:
        """Clean text by removing currency symbols, commas, and other non-numeric characters."""
        # Remove common currency symbols and words
        currency_patterns = [
            r'[Rr][Ss]\.?\s*',  # Rs, Rs., rs, etc.
            r'[Rr]upees?\s*',    # Rupee, Rupees, rupee, rupees
            r'روپے?\s*',         # روپے, روپیہ
            r'[Pp]akistani\s+[Rr]upees?\s*',  # Pakistani Rupees
            r'[Pp][Kk][Rr]\s*',  # PKR
        ]
        
        cleaned = text
        for pattern in currency_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove commas and extra spaces
        cleaned = re.sub(r'[,،\s]+', ' ', cleaned)
        
        return cleaned.strip()
    
    def _extract_numeric_value(self, text: str) -> Optional[Union[int, float]]:
        """Extract numeric value from cleaned text."""
        # Look for patterns like "50000", "50k", "50 thousand", etc.
        
        # Pattern 0: PRIORITY - Numbers near currency-related words (rupees, روپے, etc.)
        # This handles cases like "پچاس روپے" (fifty rupees) where we want the amount, not other numbers
        # BUT be careful not to interfere with compound numbers like "1 100000"
        currency_context_patterns = [
            r'\b(\d+(?:\.\d+)?)\s*(?:rupees?|روپے?|rs?\.?)\b',  # English and Urdu currency
            r'\b(?:rupees?|روپے?|rs?\.?)\s*(\d+(?:\.\d+)?)\b',  # Currency before number
            # Removed action word patterns as they were too aggressive and interfered with compound numbers
        ]
        
        # First, try to find compound numbers near currency words
        currency_compound_patterns = [
            r'\b(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*(?:rupees?|روپے?|rs?\.?)\b',  # "100 12 روپے"
            r'\b(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*(?:rupees?|روپے?|rs?\.?)\b',  # "1 100 12 روپے"
        ]
        
        for pattern in currency_compound_patterns:
            currency_match = re.search(pattern, text, re.IGNORECASE)
            if currency_match:
                try:
                    # For compound numbers near currency, add them together
                    groups = currency_match.groups()
                    if len(groups) == 2:  # "100 12 روپے"
                        amount = float(groups[0]) + float(groups[1])
                    elif len(groups) == 3:  # "1 100 12 روپے"
                        # This is likely "1 100" (hundred) + "12" = 112
                        if float(groups[0]) == 1 and float(groups[1]) == 100:
                            amount = float(groups[1]) + float(groups[2])  # 100 + 12 = 112
                        else:
                            amount = float(groups[0]) + float(groups[1]) + float(groups[2])
                    else:
                        continue
                    
                    if amount > 0:  # Valid amount found
                        return amount
                except ValueError:
                    continue
        
        # If no compound pattern matched, try simple currency patterns
        for pattern in currency_context_patterns:
            currency_match = re.search(pattern, text, re.IGNORECASE)
            if currency_match:
                try:
                    amount = float(currency_match.group(1))
                    if amount > 0:  # Valid amount found
                        return amount
                except ValueError:
                    continue
        
        # Pattern 1: Numbers with k/K (thousands) - check this first
        k_pattern = re.search(r'\b(\d+(?:\.\d+)?)\s*[kK]\b', text)
        if k_pattern:
            try:
                return float(k_pattern.group(1)) * 1000
            except ValueError:
                pass
        
        # Pattern 2: Handle multiple compound numbers in sequence (e.g., "2 1000 4 100 10")
        # This handles cases like "دو ہزار چار سو دس" -> "2 1000 4 100 10" -> 2410
        compound_patterns = [
            (r'\b(\d+(?:\.\d+)?)\s+1000\b', 1000),    # thousands: "2 1000" -> 2000
            (r'\b(\d+(?:\.\d+)?)\s+100000\b', 100000), # lakhs: "5 100000" -> 500000  
            (r'\b(\d+(?:\.\d+)?)\s+1000000\b', 1000000), # millions: "1 1000000" -> 1000000
            (r'\b(\d+(?:\.\d+)?)\s+10000000\b', 10000000), # crores: "2 10000000" -> 20000000
            (r'\b(\d+(?:\.\d+)?)\s+100\b', 100),       # hundreds: "4 100" -> 400
        ]
        
        # Also handle standalone hundreds (like "400", "500", etc.)
        standalone_hundreds_pattern = r'\b(400|500|600|700|800|900)\b'
        
        # First, try to find all compound numbers and sum them
        total_amount = 0
        remaining_text = text
        
        for pattern, multiplier in compound_patterns:
            matches = re.findall(pattern, remaining_text)
            for match in matches:
                try:
                    total_amount += float(match) * multiplier
                    # Remove this match from remaining text to avoid double counting
                    remaining_text = re.sub(pattern, '', remaining_text)
                except ValueError:
                    continue
        
        # Also handle standalone hundreds (like "400", "500", etc.)
        standalone_hundreds_matches = re.findall(standalone_hundreds_pattern, remaining_text)
        for match in standalone_hundreds_matches:
            try:
                total_amount += float(match)
                # Remove this match from remaining text to avoid double counting
                remaining_text = re.sub(r'\b' + re.escape(match) + r'\b', '', remaining_text)
            except ValueError:
                continue
        
        # If we found compound numbers, check if there are remaining small numbers
        # These are likely final units (like "تیس" = 30, "پینتیس" = 35) in expressions like
        # "بارہ لاکھ پندرہ ہزار چار سو تیس" (12 lakh 15 thousand 4 hundred 30)
        if total_amount > 0:
            # Look for remaining simple numbers in the remaining text
            simple_numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', remaining_text)
            
            # Filter: only add small numbers (< 100) that are not multipliers
            # AND ensure we're not adding context numbers by checking if they're reasonably placed
            for num_str in simple_numbers:
                try:
                    num = float(num_str)
                    # Only add if:
                    # 1. It's a small number (< 100) - likely a final unit
                    # 2. It's not a multiplier (100, 1000, etc.)
                    # 3. It's >= 20 to avoid common context numbers like 1-19 from "one task", "ten tasks"
                    if 20 <= num < 100 and num not in [100]:
                        total_amount += num
                        break  # Only add the first qualifying number
                except ValueError:
                    continue
            
            return total_amount
        
        # Pattern 3: Handle multiple units in sequence (e.g., "2 100000 50 1000") - check this after compound patterns
        multi_unit_pattern = re.findall(r'\b(\d+(?:\.\d+)?)\s+(\d+)\b', text)
        if multi_unit_pattern:
            try:
                total = 0
                for number_str, unit_str in multi_unit_pattern:
                    number = float(number_str)
                    unit = int(unit_str)
                    # Skip if this looks like a compound number already handled above
                    if unit in [1000, 100000, 10000000]:
                        continue
                    
                    # Skip if this pattern is near currency words (likely a compound amount)
                    pattern_text = f"{number_str} {unit_str}"
                    if re.search(rf'\b{re.escape(pattern_text)}\s*(?:rupees?|روپے?|rs?\.?)\b', text, re.IGNORECASE):
                        continue
                    
                    total += number * unit
                return total if total > 0 else None
            except ValueError:
                pass
        
        # Pattern 3: Complex expressions like "2 lakh 50 thousand" - check this before individual patterns
        complex_pattern = re.search(r'\b(\d+)\s*(?:lakh|lakhs)\s*(\d+)\s*(?:thousand|hazaar|hazar)\b', text, re.IGNORECASE)
        if complex_pattern:
            try:
                lakh_part = float(complex_pattern.group(1)) * 100000
                thousand_part = float(complex_pattern.group(2)) * 1000
                return lakh_part + thousand_part
            except ValueError:
                pass
        
        # Pattern 3: Numbers with lakh/lakhs
        lakh_pattern = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:lakh|lakhs)\b', text, re.IGNORECASE)
        if lakh_pattern:
            try:
                return float(lakh_pattern.group(1)) * 100000
            except ValueError:
                pass
        
        # Pattern 4: Numbers with crore/crores
        crore_pattern = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:crore|crores)\b', text, re.IGNORECASE)
        if crore_pattern:
            try:
                return float(crore_pattern.group(1)) * 10000000
            except ValueError:
                pass
        
        # Pattern 5: Handle preprocessed text with units (e.g., "5 1000", "50 100000")
        # This handles cases where preprocessing converted "پانچ ہزار" to "5 1000"
        # Check for patterns like "5 1000", "50 100000", etc.
        
        # Pattern for thousands: "5 1000"
        thousand_pattern = re.search(r'\b(\d+(?:\.\d+)?)\s+1000\b', text)
        if thousand_pattern:
            try:
                return float(thousand_pattern.group(1)) * 1000
            except ValueError:
                pass
        
        # Pattern for lakhs: "5 100000"
        lakh_pattern = re.search(r'\b(\d+(?:\.\d+)?)\s+100000\b', text)
        if lakh_pattern:
            try:
                return float(lakh_pattern.group(1)) * 100000
            except ValueError:
                pass
        
        # Pattern for millions: "5 1000000"
        million_pattern = re.search(r'\b(\d+(?:\.\d+)?)\s+1000000\b', text)
        if million_pattern:
            try:
                return float(million_pattern.group(1)) * 1000000
            except ValueError:
                pass
        
        # Pattern for crores: "5 10000000"
        crore_pattern = re.search(r'\b(\d+(?:\.\d+)?)\s+10000000\b', text)
        if crore_pattern:
            try:
                return float(crore_pattern.group(1)) * 10000000
            except ValueError:
                pass
        
        # Pattern 7: Direct numbers (check this last)
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
                    # Skip numbers that are part of action phrases (like "بھر دو")
                    if self._is_action_word_context(num, text):
                        continue
                    filtered_numbers.append(num)
                
                if filtered_numbers:
                    # Filter out very small numbers (1, 2) unless they're the only numbers
                    # These are often context words like "ایک کام" (one work)
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
    
    def _is_action_phrase(self, text: str) -> bool:
        """
        Check if the entire phrase is an action phrase that should not return any amount.
        
        Args:
            text: The original text to check
            
        Returns:
            True if this is an action phrase that should return None
        """
        import re
        
        # Common Urdu action phrases that should not return amounts
        action_phrase_patterns = [
            # "بھر دو" (do it/pay it) - "دو" means "do" not "two"
            r'بھر\s+دو\b',
            r'کر\s+دو\b',  # "کر دو" (do it)
            r'دے\s+دو\b',  # "دے دو" (give it)
            r'بھیج\s+دو\b',  # "بھیج دو" (send it)
            r'کرو\s+دو\b',  # "کرو دو" (do it)
            
            # Other action phrases with "دو"
            r'کام\s+دو\b',  # "کام دو" (work do)
            r'کرو\s+دو\b',  # "کرو دو" (do it)
            
            # Phrases with "ایک" (one) as action word
            r'ایک\s+کام\b',  # "ایک کام" (one work)
            r'ایک\s+بار\b',  # "ایک بار" (one time)
            r'ایک\s+دفعہ\b',  # "ایک دفعہ" (once)
            
            # Phrases with "تین" (three) as action word  
            r'تین\s+بار\b',  # "تین بار" (three times)
            r'تین\s+دفعہ\b',  # "تین دفعہ" (three times)
            
            # Bill payment phrases without amounts
            r'کا\s+بل\s+بھر\s+دو[۔،؛:]*\b',  # "کا بل بھر دو" (pay the bill)
            r'کا\s+بل\s+ادا\s+کرو[۔،؛:]*\b',  # "کا بل ادا کرو" (pay the bill)
            r'کا\s+بل\s+پے\s+کرو[۔،؛:]*\b',  # "کا بل پے کرو" (pay the bill)
        ]
        
        # Check if the text matches any action phrase pattern
        for pattern in action_phrase_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False

    def _is_action_word_context(self, number: float, text: str) -> bool:
        """
        Check if a number word is part of an action phrase rather than an amount.
        
        Args:
            number: The number to check
            text: The full text containing the number
            
        Returns:
            True if the number appears to be part of an action phrase
        """
        import re
        
        # Convert number to string for pattern matching
        num_str = str(int(number)) if number.is_integer() else str(number)
        
        # Common Urdu action phrases where numbers might appear as action words
        # These patterns indicate the number is NOT an amount but part of an action
        action_context_patterns = [
            # "بھر دو" (do it/pay it) - "دو" means "do" not "two"
            r'بھر\s+دو\b',
            r'کر\s+دو\b',  # "کر دو" (do it)
            r'دے\s+دو\b',  # "دے دو" (give it)
            r'بھیج\s+دو\b',  # "بھیج دو" (send it)
            r'کرو\s+دو\b',  # "کرو دو" (do it)
            
            # Other action phrases with "دو"
            r'کام\s+دو\b',  # "کام دو" (work do)
            r'کرو\s+دو\b',  # "کرو دو" (do it)
            
            # Phrases with "ایک" (one) as action word
            r'ایک\s+کام\b',  # "ایک کام" (one work)
            r'ایک\s+بار\b',  # "ایک بار" (one time)
            r'ایک\s+دفعہ\b',  # "ایک دفعہ" (once)
            
            # Phrases with "تین" (three) as action word  
            r'تین\s+بار\b',  # "تین بار" (three times)
            r'تین\s+دفعہ\b',  # "تین دفعہ" (three times)
        ]
        
        # Check if the number appears in any action context pattern
        for pattern in action_context_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False

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
            r'\b(?:phone|mobile|contact|call|dial|number)\s+(?:number\s+)?\d+[-.]?\d+[-.]?\d+\b',
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
    
    def get_urdu_numeric_examples(self) -> Dict[str, str]:
        """Get examples of Urdu numeric expressions for testing."""
        return {
            # Basic Urdu digits
            "۵۰۰۰": "5000",
            "۱۰۰۰۰": "10000",
            "۵۰۰۰۰": "50000",
            
            # Spoken Urdu
            "پانچ ہزار": "5000",
            "دس ہزار": "10000",
            "پچاس ہزار": "50000",
            "ایک لاکھ": "100000",
            "پانچ لاکھ": "500000",
            
            # Roman Urdu
            "paanch hazaar": "5000",
            "das hazaar": "10000",
            "pachaas hazaar": "50000",
            "ek laakh": "100000",
            "paanch laakh": "500000",
            
            # Mixed expressions
            "دو لاکھ پچاس ہزار": "250000",
            "تین لاکھ بیس ہزار": "320000",
            "do laakh pachaas hazaar": "250000",
            
            # With currency
            "پانچ ہزار روپے": "5000",
            "دس ہزار Rs": "10000",
            "پچاس ہزار rupees": "50000",
        }


# Global instance for easy import
urdu_converter = UrduNumericConverter()


def convert_urdu_amount(text: str) -> Optional[Union[int, float]]:
    """
    Convenience function to convert Urdu amount text to numeric value.
    
    Args:
        text: Text containing Urdu numerals, spoken numbers, or mixed expressions
        
    Returns:
        Numeric value or None if no valid amount found
    """
    return urdu_converter.extract_and_convert_amount(text)


def preprocess_urdu_text(text: str) -> str:
    """
    Preprocess text by converting all Urdu numerals to Western digits.
    
    Args:
        text: Input text that may contain Urdu numerals
        
    Returns:
        Text with all numerals converted to Western digits
    """
    return urdu_converter.convert_all_numerals(text)


if __name__ == "__main__":
    # Test the converter
    converter = UrduNumericConverter()
    
    test_cases = [
        "پانچ ہزار روپے",
        "۵۰۰۰",
        "pachaas hazaar",
        "دو لاکھ پچاس ہزار",
        "50k",
        "پچاس ہزار",
        "ایک لاکھ",
        "پانچ لاکھ",
    ]
    
    print("Testing Urdu Numeric Converter:")
    print("=" * 50)
    
    for test_case in test_cases:
        result = converter.extract_and_convert_amount(test_case)
        print(f"Input: '{test_case}' -> Output: {result}")
