"""
Roman Urdu / English-in-Urdu-Script Numeric Converter

This module handles the edge case where English is spoken but transcribed in Urdu script.
For example: "ten" spoken in English gets transcribed as "ٹین" in Urdu script.

This commonly happens when:
- User speaks English but Whisper detects it as Urdu
- Mixed language conversations
- English words phonetically written in Urdu script
"""

import re
from typing import Union, Optional, Dict


class RomanUrduNumericConverter:
    """Converts English number words written in Urdu script to digits."""
    
    def __init__(self):
        # English number words written in Urdu script (phonetic transliteration)
        # These are how English number words sound when written in Urdu letters
        
        # Basic numbers (0-19) in Urdu script but English pronunciation
        # Multiple variations to handle different Whisper transcription styles
        self.english_in_urdu_basic = {
            'زیرو': 0, 'زیروو': 0, 'زیرہ': 0,  # zero
            'ون': 1, 'وان': 1, 'وون': 1,  # one
            'ٹو': 2, 'ٹوو': 2, 'ٹُو': 2,  # two
            'تھری': 3, 'تھر': 3, 'تھرِی': 3,  # three
            'فور': 4, 'فوور': 4, 'فورر': 4,  # four
            'فائیو': 5, 'فائیوو': 5, 'فایو': 5, 'فائو': 5,  # five
            'سکس': 6, 'سکسز': 6, 'سکسس': 6,  # six
            'سیون': 7, 'سیوین': 7, 'سیوَن': 7,  # seven
            'ایٹ': 8, 'آٹ': 8, 'ایٹ': 8,  # eight
            'نائن': 9, 'نائین': 9, 'نائیں': 9,  # nine
            'ٹین': 10, 'ٹیَن': 10, 'ٹینَ': 10,  # ten
            'الیون': 11, 'الیوین': 11, 'ایلیون': 11,  # eleven
            'ٹویلو': 12, 'ٹوئلو': 12, 'ٹوئیلو': 12,  # twelve
            'تھرٹین': 13, 'تھرٹن': 13, 'تھَرٹین': 13,  # thirteen
            'فورٹین': 14, 'فورٹن': 14, 'فورٹِین': 14,  # fourteen
            'ففٹین': 15, 'ففٹن': 15, 'فِفٹین': 15,  # fifteen
            'سکسٹین': 16, 'سکسٹن': 16, 'سِکسٹین': 16,  # sixteen
            'سیونٹین': 17, 'سیونٹن': 17, 'سیونَٹین': 17,  # seventeen
            'ایٹین': 18, 'ایٹن': 18, 'ایٹِین': 18,  # eighteen
            'نائنٹین': 19, 'نائنٹن': 19, 'نائنٹِین': 19,  # nineteen
        }
        
        # Tens (20-90) in Urdu script but English pronunciation
        self.english_in_urdu_tens = {
            'ٹوینٹی': 20, 'ٹونٹی': 20,  # twenty
            'تھرٹی': 30, 'تھرٹ': 30,  # thirty
            'فورٹی': 40, 'فورٹ': 40,  # forty
            'ففٹی': 50, 'ففٹ': 50,  # fifty
            'سکسٹی': 60, 'سکسٹ': 60,  # sixty
            'سیونٹی': 70, 'سیونٹ': 70,  # seventy
            'ایٹی': 80,  # eighty
            'نائنٹی': 90, 'نائنٹ': 90,  # ninety
        }
        
        # Multipliers in Urdu script but English pronunciation
        self.english_in_urdu_multipliers = {
            'ہنڈریڈ': 100, 'ہنڈرڈ': 100,  # hundred
            'تھاؤزنڈ': 1000, 'تھاؤزینڈ': 1000, 'ہزار': 1000,  # thousand (mixed)
            'لاکھ': 100000,  # lakh (same in both)
            'ملین': 1000000, 'ملیون': 1000000,  # million
            'کروڑ': 10000000,  # crore (same in both)
            'بلین': 1000000000, 'بلیون': 1000000000,  # billion
        }
        
        # Compound numbers 21-99 (English pronunciation in Urdu script)
        # Twenties (21-29)
        self.twenties = {
            'ٹوینٹی ون': 21, 'ٹونٹی ون': 21,  # twenty one
            'ٹوینٹی ٹو': 22, 'ٹونٹی ٹو': 22,  # twenty two
            'ٹوینٹی تھری': 23, 'ٹونٹی تھری': 23,  # twenty three
            'ٹوینٹی فور': 24, 'ٹونٹی فور': 24,  # twenty four
            'ٹوینٹی فائیو': 25, 'ٹونٹی فائیو': 25, 'ٹونٹی فایو': 25,  # twenty five
            'ٹوینٹی سکس': 26, 'ٹونٹی سکس': 26,  # twenty six
            'ٹوینٹی سیون': 27, 'ٹونٹی سیون': 27,  # twenty seven
            'ٹوینٹی ایٹ': 28, 'ٹونٹی ایٹ': 28,  # twenty eight
            'ٹوینٹی نائن': 29, 'ٹونٹی نائن': 29,  # twenty nine
        }
        
        # Thirties (31-39)
        self.thirties = {
            'تھرٹی ون': 31, 'تھرٹ ون': 31,  # thirty one
            'تھرٹی ٹو': 32, 'تھرٹ ٹو': 32,  # thirty two
            'تھرٹی تھری': 33, 'تھرٹ تھری': 33,  # thirty three
            'تھرٹی فور': 34, 'تھرٹ فور': 34,  # thirty four
            'تھرٹی فائیو': 35, 'تھرٹ فائیو': 35, 'تھرٹ فایو': 35,  # thirty five
            'تھرٹی سکس': 36, 'تھرٹ سکس': 36,  # thirty six
            'تھرٹی سیون': 37, 'تھرٹ سیون': 37,  # thirty seven
            'تھرٹی ایٹ': 38, 'تھرٹ ایٹ': 38,  # thirty eight
            'تھرٹی نائن': 39, 'تھرٹ نائن': 39,  # thirty nine
        }
        
        # Forties (41-49)
        self.forties = {
            'فورٹی ون': 41, 'فورٹ ون': 41,  # forty one
            'فورٹی ٹو': 42, 'فورٹ ٹو': 42,  # forty two
            'فورٹی تھری': 43, 'فورٹ تھری': 43,  # forty three
            'فورٹی فور': 44, 'فورٹ فور': 44,  # forty four
            'فورٹی فائیو': 45, 'فورٹ فائیو': 45, 'فورٹ فایو': 45,  # forty five
            'فورٹی سکس': 46, 'فورٹ سکس': 46,  # forty six
            'فورٹی سیون': 47, 'فورٹ سیون': 47,  # forty seven
            'فورٹی ایٹ': 48, 'فورٹ ایٹ': 48,  # forty eight
            'فورٹی نائن': 49, 'فورٹ نائن': 49,  # forty nine
        }
        
        # Fifties (51-59)
        self.fifties = {
            'ففٹی ون': 51, 'ففٹ ون': 51,  # fifty one
            'ففٹی ٹو': 52, 'ففٹ ٹو': 52,  # fifty two
            'ففٹی تھری': 53, 'ففٹ تھری': 53,  # fifty three
            'ففٹی فور': 54, 'ففٹ فور': 54,  # fifty four
            'ففٹی فائیو': 55, 'ففٹ فائیو': 55, 'ففٹ فایو': 55,  # fifty five
            'ففٹی سکس': 56, 'ففٹ سکس': 56,  # fifty six
            'ففٹی سیون': 57, 'ففٹ سیون': 57,  # fifty seven
            'ففٹی ایٹ': 58, 'ففٹ ایٹ': 58,  # fifty eight
            'ففٹی نائن': 59, 'ففٹ نائن': 59,  # fifty nine
        }
        
        # Sixties (61-69)
        self.sixties = {
            'سکسٹی ون': 61, 'سکسٹ ون': 61,  # sixty one
            'سکسٹی ٹو': 62, 'سکسٹ ٹو': 62,  # sixty two
            'سکسٹی تھری': 63, 'سکسٹ تھری': 63,  # sixty three
            'سکسٹی فور': 64, 'سکسٹ فور': 64,  # sixty four
            'سکسٹی فائیو': 65, 'سکسٹ فائیو': 65, 'سکسٹ فایو': 65,  # sixty five
            'سکسٹی سکس': 66, 'سکسٹ سکس': 66,  # sixty six
            'سکسٹی سیون': 67, 'سکسٹ سیون': 67,  # sixty seven
            'سکسٹی ایٹ': 68, 'سکسٹ ایٹ': 68,  # sixty eight
            'سکسٹی نائن': 69, 'سکسٹ نائن': 69,  # sixty nine
        }
        
        # Seventies (71-79)
        self.seventies = {
            'سیونٹی ون': 71, 'سیونٹ ون': 71,  # seventy one
            'سیونٹی ٹو': 72, 'سیونٹ ٹو': 72,  # seventy two
            'سیونٹی تھری': 73, 'سیونٹ تھری': 73,  # seventy three
            'سیونٹی فور': 74, 'سیونٹ فور': 74,  # seventy four
            'سیونٹی فائیو': 75, 'سیونٹ فائیو': 75, 'سیونٹ فایو': 75,  # seventy five
            'سیونٹی سکس': 76, 'سیونٹ سکس': 76,  # seventy six
            'سیونٹی سیون': 77, 'سیونٹ سیون': 77,  # seventy seven
            'سیونٹی ایٹ': 78, 'سیونٹ ایٹ': 78,  # seventy eight
            'سیونٹی نائن': 79, 'سیونٹ نائن': 79,  # seventy nine
        }
        
        # Eighties (81-89)
        self.eighties = {
            'ایٹی ون': 81,  # eighty one
            'ایٹی ٹو': 82,  # eighty two
            'ایٹی تھری': 83,  # eighty three
            'ایٹی فور': 84,  # eighty four
            'ایٹی فائیو': 85, 'ایٹی فایو': 85,  # eighty five
            'ایٹی سکس': 86,  # eighty six
            'ایٹی سیون': 87,  # eighty seven
            'ایٹی ایٹ': 88,  # eighty eight
            'ایٹی نائن': 89,  # eighty nine
        }
        
        # Nineties (91-99)
        self.nineties = {
            'نائنٹی ون': 91, 'نائنٹ ون': 91,  # ninety one
            'نائنٹی ٹو': 92, 'نائنٹ ٹو': 92,  # ninety two
            'نائنٹی تھری': 93, 'نائنٹ تھری': 93,  # ninety three
            'نائنٹی فور': 94, 'نائنٹ فور': 94,  # ninety four
            'نائنٹی فائیو': 95, 'نائنٹ فائیو': 95, 'نائنٹ فایو': 95,  # ninety five
            'نائنٹی سکس': 96, 'نائنٹ سکس': 96,  # ninety six
            'نائنٹی سیون': 97, 'نائنٹ سیون': 97,  # ninety seven
            'نائنٹی ایٹ': 98, 'نائنٹ ایٹ': 98,  # ninety eight
            'نائنٹی نائن': 99, 'نائنٹ نائن': 99,  # ninety nine
        }
        
        # Common thousands (compound numbers with thousand)
        self.thousands_compounds = {
            'ون تھاؤزنڈ': 1000, 'ٹو تھاؤزنڈ': 2000, 'تھری تھاؤزنڈ': 3000,
            'فور تھاؤزنڈ': 4000, 'فائیو تھاؤزنڈ': 5000, 'سکس تھاؤزنڈ': 6000,
            'سیون تھاؤزنڈ': 7000, 'ایٹ تھاؤزنڈ': 8000, 'نائن تھاؤزنڈ': 9000,
            'ٹین تھاؤزنڈ': 10000, 'الیون تھاؤزنڈ': 11000, 'ٹویلو تھاؤزنڈ': 12000,
            'تھرٹین تھاؤزنڈ': 13000, 'فورٹین تھاؤزنڈ': 14000, 'ففٹین تھاؤزنڈ': 15000,
            'سکسٹین تھاؤزنڈ': 16000, 'سیونٹین تھاؤزنڈ': 17000, 'ایٹین تھاؤزنڈ': 18000,
            'نائنٹین تھاؤزنڈ': 19000, 'ٹوینٹی تھاؤزنڈ': 20000, 'تھرٹی تھاؤزنڈ': 30000,
            'فورٹی تھاؤزنڈ': 40000, 'ففٹی تھاؤزنڈ': 50000, 'سکسٹی تھاؤزنڈ': 60000,
            'سیونٹی تھاؤزنڈ': 70000, 'ایٹی تھاؤزنڈ': 80000, 'نائنٹی تھاؤزنڈ': 90000,
            'ٹوینٹی ون تھاؤزنڈ': 21000, 'ٹوینٹی ٹو تھاؤزنڈ': 22000, 'ٹوینٹی تھری تھاؤزنڈ': 23000,
            'ٹوینٹی فور تھاؤزنڈ': 24000, 'ٹوینٹی فائیو تھاؤزنڈ': 25000, 'ٹوینٹی سکس تھاؤزنڈ': 26000,
            'ٹوینٹی سیون تھاؤزنڈ': 27000, 'ٹوینٹی ایٹ تھاؤزنڈ': 28000, 'ٹوینٹی نائن تھاؤزنڈ': 29000,
            'تھرٹی ون تھاؤزنڈ': 31000, 'تھرٹی ٹو تھاؤزنڈ': 32000, 'تھرٹی تھری تھاؤزنڈ': 33000,
            'تھرٹی فور تھاؤزنڈ': 34000, 'تھرٹی فائیو تھاؤزنڈ': 35000, 'تھرٹی سکس تھاؤزنڈ': 36000,
            'تھرٹی سیون تھاؤزنڈ': 37000, 'تھرٹی ایٹ تھاؤزنڈ': 38000, 'تھرٹی نائن تھاؤزنڈ': 39000,
            'فورٹی ون تھاؤزنڈ': 41000, 'فورٹی ٹو تھاؤزنڈ': 42000, 'فورٹی تھری تھاؤزنڈ': 43000,
            'فورٹی فور تھاؤزنڈ': 44000, 'فورٹی فائیو تھاؤزنڈ': 45000, 'فورٹی سکس تھاؤزنڈ': 46000,
            'فورٹی سیون تھاؤزنڈ': 47000, 'فورٹی ایٹ تھاؤزنڈ': 48000, 'فورٹی نائن تھاؤزنڈ': 49000,
            'ففٹی ون تھاؤزنڈ': 51000, 'ففٹی ٹو تھاؤزنڈ': 52000, 'ففٹی تھری تھاؤزنڈ': 53000,
            'ففٹی فور تھاؤزنڈ': 54000, 'ففٹی فائیو تھاؤزنڈ': 55000, 'ففٹی سکس تھاؤزنڈ': 56000,
            'ففٹی سیون تھاؤزنڈ': 57000, 'ففٹی ایٹ تھاؤزنڈ': 58000, 'ففٹی نائن تھاؤزنڈ': 59000,
            'سکسٹی ون تھاؤزنڈ': 61000, 'سکسٹی ٹو تھاؤزنڈ': 62000, 'سکسٹی تھری تھاؤزنڈ': 63000,
            'سکسٹی فور تھاؤزنڈ': 64000, 'سکسٹی فائیو تھاؤزنڈ': 65000, 'سکسٹی سکس تھاؤزنڈ': 66000,
            'سکسٹی سیون تھاؤزنڈ': 67000, 'سکسٹی ایٹ تھاؤزنڈ': 68000, 'سکسٹی نائن تھاؤزنڈ': 69000,
            'سیونٹی ون تھاؤزنڈ': 71000, 'سیونٹی ٹو تھاؤزنڈ': 72000, 'سیونٹی تھری تھاؤزنڈ': 73000,
            'سیونٹی فور تھاؤزنڈ': 74000, 'سیونٹی فائیو تھاؤزنڈ': 75000, 'سیونٹی سکس تھاؤزنڈ': 76000,
            'سیونٹی سیون تھاؤزنڈ': 77000, 'سیونٹی ایٹ تھاؤزنڈ': 78000, 'سیونٹی نائن تھاؤزنڈ': 79000,
            'ایٹی ون تھاؤزنڈ': 81000, 'ایٹی ٹو تھاؤزنڈ': 82000, 'ایٹی تھری تھاؤزنڈ': 83000,
            'ایٹی فور تھاؤزنڈ': 84000, 'ایٹی فائیو تھاؤزنڈ': 85000, 'ایٹی سکس تھاؤزنڈ': 86000,
            'ایٹی سیون تھاؤزنڈ': 87000, 'ایٹی ایٹ تھاؤزنڈ': 88000, 'ایٹی نائن تھاؤزنڈ': 89000,
            'نائنٹی ون تھاؤزنڈ': 91000, 'نائنٹی ٹو تھاؤزنڈ': 92000, 'نائنٹی تھری تھاؤزنڈ': 93000,
            'نائنٹی فور تھاؤزنڈ': 94000, 'نائنٹی فائیو تھاؤزنڈ': 95000, 'نائنٹی سکس تھاؤزنڈ': 96000,
            'نائنٹی سیون تھاؤزنڈ': 97000, 'نائنٹی ایٹ تھاؤزنڈ': 98000, 'نائنٹی نائن تھاؤزنڈ': 99000,
        }
        
        # Common lakhs and crores (compound numbers with lakh/crore)
        self.lakhs_crores_compounds = {
            'ون لاکھ': 100000, 'ٹو لاکھ': 200000, 'تھری لاکھ': 300000,
            'فور لاکھ': 400000, 'فائیو لاکھ': 500000, 'سکس لاکھ': 600000,
            'سیون لاکھ': 700000, 'ایٹ لاکھ': 800000, 'نائن لاکھ': 900000,
            'ون کروڑ': 10000000, 'ٹو کروڑ': 20000000, 'تھری کروڑ': 30000000,
            'فور کروڑ': 40000000, 'فائیو کروڑ': 50000000, 'سکس کروڑ': 60000000,
            'سیون کروڑ': 70000000, 'ایٹ کروڑ': 80000000, 'نائن کروڑ': 90000000,
        }
        
        # Common hundreds (compound numbers with hundred)
        self.hundreds_compounds = {
            'ون ہنڈریڈ': 100, 'ٹو ہنڈریڈ': 200, 'تھری ہنڈریڈ': 300,
            'فور ہنڈریڈ': 400, 'فائیو ہنڈریڈ': 500, 'سکس ہنڈریڈ': 600,
            'سیون ہنڈریڈ': 700, 'ایٹ ہنڈریڈ': 800, 'نائن ہنڈریڈ': 900,
            'ٹو ہنڈریڈ تھاؤزنڈ': 200000, 'سکس ہنڈریڈ تھاؤزنڈ': 600000,
            'سیونٹی فائیو تھاؤزنڈ': 75000,
        }
        
        # Combine all compound numbers
        self.compound_numbers = {
            **self.twenties,
            **self.thirties,
            **self.forties,
            **self.fifties,
            **self.sixties,
            **self.seventies,
            **self.eighties,
            **self.nineties,
            **self.thousands_compounds,
            **self.lakhs_crores_compounds,
            **self.hundreds_compounds
        }
        
        # K, M, B abbreviations in Urdu script
        self.abbreviations = {
            'کے': 1000,  # k
            'ایم': 1000000,  # m
            'بی': 1000000000,  # b
        }
        
        # Combine all mappings
        self.all_mappings = {
            **self.english_in_urdu_basic,
            **self.english_in_urdu_tens,
            **self.english_in_urdu_multipliers,
            **self.compound_numbers,
            **self.abbreviations
        }
        
        # Compile regex pattern
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        pattern = '|'.join(re.escape(word) for word in self.all_mappings.keys())
        self.word_regex = re.compile(f'({pattern})', re.IGNORECASE)
    
    def convert_roman_urdu_to_number(self, text: str) -> Optional[int]:
        """
        Convert English number words written in Urdu script to numeric value.
        
        Args:
            text: Text containing English words in Urdu script
            
        Returns:
            Numeric value or None if no valid number found
        """
        if not text or not isinstance(text, str):
            return None
        
        # Split into words
        words = text.split()
        
        total = 0
        current = 0
        i = 0
        
        while i < len(words):
            word_clean = words[i].strip('۔،؛:')
            
            # Check for three-word compounds FIRST (like "سیونٹی فائیو تھاؤزنڈ")
            if i + 2 < len(words):
                three_word = word_clean + ' ' + words[i + 1].strip('۔،؛:') + ' ' + words[i + 2].strip('۔،؛:')
                if three_word in self.compound_numbers:
                    current += self.compound_numbers[three_word]
                    i += 3
                    continue
            
            # Check for two-word compounds
            if i + 1 < len(words):
                two_word = word_clean + ' ' + words[i + 1].strip('۔،؛:')
                if two_word in self.compound_numbers:
                    current += self.compound_numbers[two_word]
                    i += 2
                    continue
            
            # Check if it's a basic number (0-19)
            if word_clean in self.english_in_urdu_basic:
                current += self.english_in_urdu_basic[word_clean]
            
            # Check if it's a tens number (20-90)
            elif word_clean in self.english_in_urdu_tens:
                current += self.english_in_urdu_tens[word_clean]
            
            # Check if it's a multiplier
            elif word_clean in self.english_in_urdu_multipliers:
                multiplier = self.english_in_urdu_multipliers[word_clean]
                
                if multiplier == 100:
                    if current == 0:
                        current = 100
                    else:
                        current *= 100
                else:
                    if current == 0:
                        current = multiplier
                    else:
                        current *= multiplier
                    total += current
                    current = 0
            
            # Check for abbreviations
            elif word_clean in self.abbreviations:
                if current > 0:
                    current *= self.abbreviations[word_clean]
                    total += current
                    current = 0
            
            i += 1
        
        # Add any remaining current value
        total += current
        
        # If we found multiple numbers, prioritize larger amounts over context numbers
        # This handles cases like "ون تھنگ، فائیو تھاؤزنڈ" where we want 5000, not 6000
        if total > 0:
            # Collect all individual numbers found in the text
            all_numbers = []
            temp_i = 0
            
            while temp_i < len(words):
                word_clean = words[temp_i].strip('۔،؛:')
                
                # Check for three-word compounds FIRST (like "سیونٹی فائیو تھاؤزنڈ")
                if temp_i + 2 < len(words):
                    three_word = word_clean + ' ' + words[temp_i + 1].strip('۔،؛:') + ' ' + words[temp_i + 2].strip('۔،؛:')
                    if three_word in self.compound_numbers:
                        all_numbers.append(self.compound_numbers[three_word])
                        temp_i += 3
                        continue
                
                # Check for two-word compounds
                if temp_i + 1 < len(words):
                    two_word = word_clean + ' ' + words[temp_i + 1].strip('۔،؛:')
                    if two_word in self.compound_numbers:
                        all_numbers.append(self.compound_numbers[two_word])
                        temp_i += 2
                        continue
                
                # Check individual numbers
                if word_clean in self.english_in_urdu_basic:
                    all_numbers.append(self.english_in_urdu_basic[word_clean])
                elif word_clean in self.english_in_urdu_tens:
                    all_numbers.append(self.english_in_urdu_tens[word_clean])
                elif word_clean in self.english_in_urdu_multipliers:
                    multiplier = self.english_in_urdu_multipliers[word_clean]
                    # Only count standalone multipliers, not when they're part of compound numbers
                    if multiplier > 1000:  # Only very large multipliers
                        all_numbers.append(multiplier)
                
                temp_i += 1
            
            # If multiple numbers found, prefer larger ones (likely amounts over context)
            if len(all_numbers) > 1:
                # Filter out very small numbers (1, 2) unless they're the only numbers
                larger_numbers = [num for num in all_numbers if num >= 10]
                if larger_numbers:
                    return max(larger_numbers)  # Return the largest reasonable amount
                else:
                    return max(all_numbers)  # If all are small, return the largest
        
        return total if total > 0 else None
    
    def extract_amount(self, text: str) -> Optional[Union[int, float]]:
        """
        Extract amount from text containing English words in Urdu script.
        
        Args:
            text: Input text
            
        Returns:
            Numeric value or None if no valid amount found
        """
        return self.convert_roman_urdu_to_number(text)
    
    def preprocess_text(self, text: str) -> str:
        """
        Convert English number words in Urdu script to digits.
        
        Args:
            text: Input text
            
        Returns:
            Text with numbers converted to digits
        """
        if not text or not isinstance(text, str):
            return text
        
        def replace_number(match):
            word = match.group(1)
            if word in self.all_mappings:
                return str(self.all_mappings[word])
            return word
        
        return self.word_regex.sub(replace_number, text)
    
    def has_roman_urdu_numbers(self, text: str) -> bool:
        """Check if text contains English number words in Urdu script."""
        if not text:
            return False
        return bool(self.word_regex.search(text))


# Global instance for easy import
roman_urdu_converter = RomanUrduNumericConverter()


def convert_roman_urdu_amount(text: str) -> Optional[Union[int, float]]:
    """
    Convenience function to convert Roman Urdu amount text to numeric value.
    
    Args:
        text: Text containing English words in Urdu script
        
    Returns:
        Numeric value or None if no valid amount found
    """
    return roman_urdu_converter.extract_amount(text)


def preprocess_roman_urdu_text(text: str) -> str:
    """
    Preprocess text by converting Roman Urdu numbers to digits.
    
    Args:
        text: Input text that may contain English words in Urdu script
        
    Returns:
        Text with numbers converted to digits
    """
    return roman_urdu_converter.preprocess_text(text)


if __name__ == "__main__":
    # Test the converter
    converter = RomanUrduNumericConverter()
    
    test_cases = [
        "ٹوپ اپ آف ٹین آن وارث",  # top up of ten on Waris
        "ٹوینٹی فائیو تھاؤزنڈ",  # twenty five thousand
        "ففٹی کے",  # 50k
        "ون لاکھ",  # one lakh
        "فائیو ملین",  # five million
        "تھرٹی فائیو",  # thirty five
        "سکسٹی سیون",  # sixty seven
        "نائنٹی نائن",  # ninety nine
        "ٹوینٹی ون تھاؤزنڈ",  # twenty one thousand
        "ففٹی تھری ہنڈریڈ",  # fifty three hundred
    ]
    
    print("Testing Roman Urdu Numeric Converter:")
    print("=" * 60)
    
    for test_case in test_cases:
        result = converter.extract_amount(test_case)
        preprocessed = converter.preprocess_text(test_case)
        try:
            print(f"Input: '{test_case}'")
            print(f"  Amount: {result}")
            print(f"  Preprocessed: '{preprocessed}'")
        except UnicodeEncodeError:
            print(f"Input: [Urdu script - cannot display]")
            print(f"  Amount: {result}")
            print(f"  Preprocessed: [converted text]")
        print()

