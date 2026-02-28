import re

def get_prediction(model, vectorizer, text):
    text= vectorizer.transform([text])
    return model.predict(text)[0]

def check_if_urdu(text):
    b= re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+', text)
    if b:
        return True
    return False

# Sindhi-specific Unicode characters that do not commonly appear in standard Urdu text
_SINDHI_SPECIFIC_CHARS = frozenset([
    '\u067A',  # ٺ  ARABIC LETTER TTEH WITH RING
    '\u067B',  # ٻ  ARABIC LETTER BEH WITH BAR
    '\u067F',  # ٿ  ARABIC LETTER TTEH WITH FOUR DOTS ABOVE
    '\u0680',  # ڀ  ARABIC LETTER BEH WITH FOUR DOTS BELOW
    '\u0683',  # ڃ  ARABIC LETTER NYEH
    '\u0684',  # ڄ  ARABIC LETTER DYEH
    '\u0687',  # ڇ  ARABIC LETTER TCHEH WITH FOUR DOTS
    '\u068A',  # ڊ  ARABIC LETTER DAL WITH DOT BELOW
    '\u068D',  # ڍ  ARABIC LETTER DAL WITH DOT BELOW AND SMALL TAH
    '\u068E',  # ڎ  ARABIC LETTER DAL WITH FOUR DOTS ABOVE
    '\u068F',  # ڏ  ARABIC LETTER DAL WITH DOT ABOVE
    '\u06AA',  # ڪ  ARABIC LETTER SWASH KAF
    '\u06B1',  # ڱ  ARABIC LETTER NOON WITH RING
    '\u06B3',  # ڳ  ARABIC LETTER GAF WITH TWO DOTS BELOW
    '\u06FD',  # ۽  ARABIC SIGN SINDHI AMPERSAND
    '\u06FE',  # ۾  ARABIC SIGN SINDHI POSTPOSITION MEN
])

def check_if_sindhi(text: str) -> bool:
    """
    Return True if the text contains characters that are specific to the
    Sindhi script and are not commonly found in standard Urdu/Arabic text.
    """
    return any(c in _SINDHI_SPECIFIC_CHARS for c in text)

