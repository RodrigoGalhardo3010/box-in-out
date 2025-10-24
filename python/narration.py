import os, io, math, itertools
from typing import Optional
import boto3

# Mapeia idioma -> voz Polly
VOICE_BY_LANG = {
    'pt-BR': 'Camila',   # alternativas: Thiago, Vitoria
    'pt-PT': 'Ines',
    'en': 'Joanna',
    'en-US': 'Joanna',
    'en-GB': 'Amy',
    'es': 'Lucia',
    'es-ES': 'Lucia',
    'es-MX': 'Mia',
}

def get_polly():
    region = os.getenv('AWS_REGION', 'us-east-1')
    return boto3.client('polly', region_name=region)

def synthesize(text: str, lang: str = 'pt-BR', speech_rate: str = 'medium') -> bytes:
    """Gera áudio TTS via Polly, retornando bytes MP3."""
    polly = get_polly()
    voice = VOICE_BY_LANG.get(lang, 'Camila')
    # Ajuste leve de prosódia por taxa
    rate_map = {'slow':'85%', 'medium':'100%', 'fast':'115%'}
    rate = rate_map.get(speech_rate, '100%')
    ssml = f"""<speak><prosody rate='{rate}'>{text}</prosody></speak>"""
    resp = polly.synthesize_speech(VoiceId=voice, OutputFormat='mp3', TextType='ssml', Text=ssml, LanguageCode=None)
    return resp['AudioStream'].read()
