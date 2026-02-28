import re

def get_prediction(model, vectorizer, text):
    text= vectorizer.transform([text])
    return model.predict(text)[0]

def check_if_urdu(text):
    b= re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+', text)
    if b:
        return True
    return False

