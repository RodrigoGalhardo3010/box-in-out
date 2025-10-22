import os
from typing import Dict

LANGS = {
    "pt": "Portuguese",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "it": "Italian",
    "de": "German",
    "zh": "Chinese (Simplified)",
}

def translate_text(text: str, target: str) -> str:
    # Tenta Google Cloud; se não houver chave, retorna o próprio texto.
    try:
        from google.cloud import translate_v2 as translate
        client = translate.Client()
        return client.translate(text, target_language=target)["translatedText"]
    except Exception:
        return text
