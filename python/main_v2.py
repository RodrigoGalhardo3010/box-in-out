import os, pathlib, shutil, argparse, io
from typing import List
from story import story_lines
from media import pexels_images, clear_pexels_cache
from video_v2 import assemble_video
from translate import translate_text
from subtitles_multi import srt_from_timings
from narration import synthesize as tts
from music import load_background_music
from pydub import AudioSegment

OUT = pathlib.Path(__file__).parent / "output_v2"
OUT.mkdir(exist_ok=True)

def build_audio_narration(lines: List[str], lang: str) -> AudioSegment:
    parts = []
    # Heurística de duração: 0.6s por 7-10 palavras (~120–150 wpm)
    for line in lines:
        audio_mp3 = tts(line, lang=lang, speech_rate='medium')
        seg = AudioSegment.from_file(io.BytesIO(audio_mp3), format='mp3')
        parts.append(seg + AudioSegment.silent(duration=250))  # pequena pausa
    return sum(parts, AudioSegment.silent(duration=0))

def duck_music(music: AudioSegment, voice: AudioSegment, duck_db: float = -12.0) -> AudioSegment:
    # Reduz música quando há voz (simples: mix com ganho relativo)
    music_under = music.apply_gain(duck_db)
    mixed = music_under.overlay(voice)
    return mixed

def timings_from_audio(voice: AudioSegment, lines: List[str]) -> list:
    # Divide por número de falas proporcionalmente à duração
    total = len(voice)
    per = total // max(1,len(lines))
    timings = [per] * len(lines)
    # Ajusta último para fechar exatamente
    if timings:
        timings[-1] = total - sum(timings[:-1])
    return timings

def run(topic: str, n_images: int = 8, lang_narration: str = 'pt-BR', sub_langs: List[str] = None):
    sub_langs = sub_langs or os.getenv('SUB_LANGS','pt-BR,en,es').split(',')

    print(f"[topic] {topic}")
    # História em 6 atos
    lines = story_lines(topic)
    print("[story]", lines)

    # TTS
    voice = build_audio_narration(lines, lang=lang_narration)

    # Música
    music = load_background_music(total_duration_ms=len(voice))
    final_audio = duck_music(music, voice)

    # Salvar áudio final temporário
    tmp_audio = OUT / "temp_audio.mp3"
    final_audio.export(tmp_audio, format='mp3')

    # Imagens de apoio via Pexels
    imgs = pexels_images(query=topic, limit=n_images)

    # Montagem do vídeo
    per_sec = max(1.0, (len(voice)/1000.0)/max(1,len(imgs)))
    out_video = OUT / f"{topic.replace(' ','_')}.mp4"
    assemble_video(imgs, per_sec, str(out_video), audio_path=str(tmp_audio))

    # Legendas por idioma
    base_lines = lines
    # duração por linha conforme áudio real
    timings = timings_from_audio(voice, base_lines)

    srt_paths = {}
    for lang in sub_langs:
        if lang.strip() == 'pt-BR':
            translated = base_lines
        else:
            translated = [translate_text(l, target_language=lang.strip()) for l in base_lines]
        srt_content = srt_from_timings(translated, timings)
        srt_path = OUT / f"{out_video.stem}.{lang.strip()}.srt"
        srt_path.write_text(srt_content, encoding='utf-8')
        srt_paths[lang] = srt_path

    print("\n✓ Vídeo gerado:", out_video)
    for lang, sp in srt_paths.items():
        print("  ↳ SRT:", lang, sp)
    return out_video, srt_paths

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument('--videos', type=int, default=1)
    ap.add_argument('--topic', type=str, default='energia solar residencial')
    ap.add_argument('--lang', type=str, default='pt-BR')
    args = ap.parse_args()
    for _ in range(args.videos):
        run(topic=args.topic, lang_narration=args.lang)
