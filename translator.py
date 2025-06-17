import requests
import os

def translate_word(text, target_lang="EN"):
    API_KEY = os.getenv("DEEPL_API_KEY")
    url = "https://api-free.deepl.com/v2/translate"
    data = {
        "auth_key": API_KEY,
        "text": text,
        "target_lang": target_lang
    }
    response = requests.post(url, data=data).json()
    translated_text = response['translations'][0]['text']
    detected_lang = response['translations'][0]['detected_source_language']
    return translated_text, detected_lang
