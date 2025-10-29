# core/tts.py
import os, io, boto3
from pydub import AudioSegment

VOICES = {
    "pt-BR": "Camila",   # alternativas: Vitoria, Thiago
    "en":    "Matthew",  # definido pelo usuário
    "es":    "Lucia"     # alternativas: Miguel, Conchita
}

def synthesize_ssml(text, lang):
    return f"<speak><prosody rate='medium'>{text}</prosody></speak>"

def tts_from_blocks(blocks, lang_code, out_path):
    polly = boto3.client("polly", region_name=os.getenv("AWS_REGION", "us-east-1"))
    voice = VOICES.get(lang_code, VOICES["en"])
    combined = AudioSegment.silent(duration=0)
    piece_durations = []

    for i, b in enumerate(blocks):
        ssml = synthesize_ssml(b["text"], lang_code)
        resp = polly.synthesize_speech(
            TextType="ssml",
            Text=ssml,
            VoiceId=voice,
            OutputFormat="mp3",
            Engine="neural"
        )
        audio_bytes = resp["AudioStream"].read()
        seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        combined += seg + AudioSegment.silent(duration=250)  # pequena pausa
        piece_durations.append(len(seg)/1000.0 + 0.250)

    combined.export(out_path, format="mp3")
    total_secs = sum(piece_durations)
    return out_path, total_secs, piece_durations
