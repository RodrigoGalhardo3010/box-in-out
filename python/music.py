import os, random, io, math
from typing import Optional, Tuple
from pydub import AudioSegment

# Pequena faixa default (sine pad) caso não haja MP3 local
def _embedded_tone(duration_ms=60000) -> AudioSegment:
    from pydub.generators import Sine
    base = Sine(440).to_audio_segment(duration=duration_ms).apply_gain(-18)
    pad  = Sine(880).to_audio_segment(duration=duration_ms).apply_gain(-22)
    return base.overlay(pad)

def load_background_music(total_duration_ms: int) -> AudioSegment:
    music_dir = os.getenv('MUSIC_DIR', 'python/assets/music').strip()
    candidates = []
    if os.path.isdir(music_dir):
        for f in os.listdir(music_dir):
            if f.lower().endswith(('.mp3','.wav','.m4a','.flac','.ogg')):
                candidates.append(os.path.join(music_dir,f))
    if candidates:
        path = random.choice(candidates)
        track = AudioSegment.from_file(path)
    else:
        track = _embedded_tone(total_duration_ms)

    # Loop até cobrir toda a duração
    out = AudioSegment.silent(duration=0)
    while len(out) < total_duration_ms:
        out += track
    return out[:total_duration_ms]
