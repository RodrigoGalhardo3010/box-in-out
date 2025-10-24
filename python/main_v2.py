import os, pathlib, shutil, argparse, io
from typing import List, Dict
from story import story_lines
from media import pexels_images, clear_pexels_cache
from video_v2 import assemble_video
from translate import translate_text
from subtitles_multi import srt_from_timings
from narration import synthesize as tts
from music import load_background_music
from pydub import AudioSegment

# Saída da v2 (mantenho separada da v1)
OUT = pathlib.Path(__file__).parent / "output_v2"
OUT.mkdir(exist_ok=True)


def _norm_lang(code: str) -> str:
    """
    Normaliza códigos como 'pt-BR' -> 'pt' para o translate_v2,
    que espera apenas ISO-639-1.
    """
    return (code or "").strip().lower().split("-")[0]


def build_audio_narration(lines: List[str], lang: str = 'pt-BR') -> AudioSegment:
    """
    Gera a narração concatenando as falas (TTS) com pequenas pausas.
    """
    parts: List[AudioSegment] = []
    for line in lines:
        audio_mp3 = tts(line, lang=lang, speech_rate='medium')
        seg = AudioSegment.from_file(io.BytesIO(audio_mp3), format='mp3')
        # pequena pausa entre falas para legibilidade das legendas
        parts.append(seg + AudioSegment.silent(duration=250))
    return sum(parts, AudioSegment.silent(duration=0))


def duck_music(music: AudioSegment, voice: AudioSegment, duck_db: float = -12.0) -> AudioSegment:
    """
    Reduz a música quando há voz (mix simples com ganho relativo).
    """
    music_under = music.apply_gain(duck_db)
    mixed = music_under.overlay(voice)
    return mixed


def timings_from_audio(voice: AudioSegment, lines: List[str]) -> List[int]:
    """
    Distribui a duração total do áudio igualmente pelas falas.
    (simples e robusto; se quiser refinar, dá para usar VAD/aligner)
    """
    total = len(voice)
    n = max(1, len(lines))
    per = total // n
    timings = [per] * n
    if timings:
        timings[-1] = total - sum(timings[:-1])  # fecha a conta
    return timings


def run(topic: str, n_images: int = 8, lang_narration: str = 'pt-BR', sub_langs: List[str] = None):
    """
    Pipeline completa:
    - cria história,
    - gera narração (Camila/pt-BR por padrão),
    - carrega/loopa música e aplica ducking,
    - baixa imagens e monta vídeo,
    - produz SRT sidecar nos idiomas escolhidos.
    """
    sub_langs = sub_langs or os.getenv('SUB_LANGS', 'pt-BR,en,es').split(',')

    print(f"[topic] {topic}")
    # História curta em 6 atos
    lines = story_lines(topic)
    print("[story]", lines)

    # Narração
    voice = build_audio_narration(lines, lang=lang_narration)

    # Música + ducking
    music = load_background_music(total_duration_ms=len(voice))
    final_audio = duck_music(music, voice)

    # Salva áudio temporário
    tmp_audio = OUT / "temp_audio.mp3"
    final_audio.export(tmp_audio, format='mp3')

    # Imagens (Pexels)
    imgs = pexels_images(query=topic, limit=n_images)

    # Duração por imagem proporcional ao áudio total
    per_sec = max(1.0, (len(voice) / 1000.0) / max(1, len(imgs)))
    out_video = OUT / f"{topic.replace(' ', '_')}.mp4"

    # Montagem do vídeo com trilha
    assemble_video(imgs, per_sec, str(out_video), audio_path=str(tmp_audio))

    # Legendas (SRT sidecar)
    base_lines = lines
    timings = timings_from_audio(voice, base_lines)

    srt_paths: Dict[str, pathlib.Path] = {}
    for lang in sub_langs:
        raw_lang = (lang or "").strip()
        tgt = _norm_lang(raw_lang)

        if tgt == 'pt':  # pt é o idioma da narração; não precisa traduzir
            translated = base_lines
        else:
            translated = [translate_text(l, target=tgt) for l in base_lines]

        srt_content = srt_from_timings(translated, timings)
        srt_path = OUT / f"{out_video.stem}.{raw_lang}.srt"  # mantém rótulo original (ex.: pt-BR)
        srt_path.write_text(srt_content, encoding='utf-8')
        srt_paths[raw_lang] = srt_path

    print("\n✓ Vídeo gerado:", out_video)
    for lang, sp in srt_paths.items():
        print("  ↳ SRT:", lang, sp)
    return out_video, srt_paths


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument('--videos', type=int, default=1)
    ap.add_argument('--topic', type=str, default='energia solar residencial')
    ap.add_argument('--lang', type=str, default='pt-BR')  # narração (Camila)
    args = ap.parse_args()
    for _ in range(args.videos):
        run(topic=args.topic, lang_narration=args.lang)
