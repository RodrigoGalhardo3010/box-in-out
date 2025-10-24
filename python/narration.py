import os, io
import boto3

# ==========================================================
# Narração padrão para vídeos do TikTok (voz Camila - pt-BR)
# ==========================================================

DEFAULT_LANG = 'pt-BR'
DEFAULT_VOICE = 'Camila'

# Caso futuramente queira vozes adicionais:
VOICE_BY_LANG = {
    'pt-BR': 'Camila',   # Outras opções: 'Thiago', 'Vitoria'
}
LANG_CODE_BY_LANG = {
    'pt-BR': 'pt-BR',
}

def get_polly():
    """Retorna cliente boto3 Polly configurado com a região do ambiente."""
    region = os.getenv('AWS_REGION', 'us-east-1')
    return boto3.client('polly', region_name=region)

def synthesize(text: str, lang: str = DEFAULT_LANG, speech_rate: str = 'medium') -> bytes:
    """
    Gera áudio MP3 via AWS Polly.
    - text: Texto a ser narrado (SSML seguro).
    - lang: Idioma (padrão pt-BR).
    - speech_rate: 'slow', 'medium' ou 'fast'.
    """
    polly = get_polly()
    voice = VOICE_BY_LANG.get(lang, DEFAULT_VOICE)

    rate_map = {'slow': '85%', 'medium': '100%', 'fast': '115%'}
    rate = rate_map.get(speech_rate, '100%')
    ssml = f"<speak><prosody rate='{rate}'>{text}</prosody></speak>"

    # Monta parâmetros (só envia LanguageCode se existir)
    kwargs = dict(
        VoiceId=voice,
        OutputFormat='mp3',
        TextType='ssml',
        Text=ssml,
    )
    lang_code = LANG_CODE_BY_LANG.get(lang)
    if lang_code:
        kwargs['LanguageCode'] = lang_code

    # Chama o Polly com parâmetros válidos
    resp = polly.synthesize_speech(**kwargs)
    return resp['AudioStream'].read()
