# python/core/tts.py
# TTS com Amazon Polly (PT-BR, EN, ES)
# - Retorna: caminho mp3, duração total (s), lista de durações por bloco (s)
# - Ajuste automático para ~60s se definido VIDEO_SECONDS
# - Engine neural sempre que possível

import os, io, boto3
from pydub import AudioSegment

VOICES = {
    "pt-BR": "Camila",   # alternativas: Vitoria, Thiago
    "en":    "Matthew",  # conforme especificado pelo usuário
    "es":    "Lucia"     # alternativas: Miguel, Conchita
}

def synthesize_ssml(text, lang):
    # SSML simples e robusto (pode evoluir para marcação de pausas)
    return f"<speak><prosody rate='medium'>{text}</prosody></speak>"

def tts_from_blocks(blocks, lang_code, out_path):
    polly = boto3.client("polly", region_name=os.getenv("AWS_REGION", "us-east-1"))
    voice = VOICES.get(lang_code, VOICES["en"])
    combined = AudioSegment.silent(duration=0)
    piece_durations = []

    for b in blocks:
        ssml = synthesize_ssml(b["text"], lang_code)
        try:
            resp = polly.synthesize_speech(
                TextType="ssml",
                Text=ssml,
                VoiceId=voice,
                OutputFormat="mp3",
                Engine="neural"
            )
        except Exception:
            # fallback para engine padrão se neural não estiver disponível
            resp = polly.synthesize_speech(
                TextType="ssml",
                Text=ssml,
                VoiceId=voice,
                OutputFormat="mp3"
            )

        audio_bytes = resp["AudioStream"].read()
        seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        piece_durations.append(len(seg) / 1000.0)
        combined += seg

        # pequena pausa entre blocos para melhor respiração
        combined += AudioSegment.silent(duration=200)

    total_secs = sum(piece_durations)

    # Ajuste final para durar ~ VIDEO_SECONDS
    target = float(os.getenv("VIDEO_SECONDS", "60"))
    if total_secs < target - 1.0:
        extra = (target - total_secs)
        combined += AudioSegment.silent(duration=int(extra * 1000))
        piece_durations.append(extra)
        total_secs = sum(piece_durations)

    # Exportação final
    combined.export(out_path, format="mp3")

    return out_path, total_secs, piece_durations
