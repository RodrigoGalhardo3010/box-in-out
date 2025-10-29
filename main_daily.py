# main_daily.py
import os, pathlib, datetime, json
from core.script_gen import generate_script, translate_blocks
from core.tts import tts_from_blocks
from core.media import fetch_broll
from core.assemble import build_video
from core.srt import write_srt_from_blocks

def main():
    date_str = datetime.date.today().isoformat()
    out_dir = pathlib.Path("python/output") / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    provider = "bedrock" if os.getenv("AWS_ACCESS_KEY_ID") else "openai"
    langs = os.getenv("LANGS", "pt-BR,en,es").split(",")
    target_secs = int(os.getenv("VIDEO_SECONDS", "60"))
    theme = os.getenv("THEME_SEED", "autoajuda")
    music_dir = os.getenv("MUSIC_DIR", "python/assets/music")
    branding_handle = os.getenv("BRANDING_HANDLE", "@BoxInandOut")

    # 1) Roteiro base PT-BR
    data_pt = generate_script(theme=theme, provider=provider)
    blocks_pt = data_pt["blocks"]
    (out_dir / "prompt.txt").write_text(json.dumps(data_pt, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2) Traduções
    blocks_en = translate_blocks(blocks_pt, "English", provider=provider)
    blocks_es = translate_blocks(blocks_pt, "Español", provider=provider)

    # 3) TTS
    mp3_pt, dur_pt, parts_pt = tts_from_blocks(blocks_pt, "pt-BR", str(out_dir / "daily_pt-BR.mp3"))
    mp3_en, dur_en, parts_en = tts_from_blocks(blocks_en, "en",     str(out_dir / "daily_en.mp3"))
    mp3_es, dur_es, parts_es = tts_from_blocks(blocks_es, "es",     str(out_dir / "daily_es.mp3"))

    # 4) B-roll (mix equilibrado)
    # Consulta genérica com palavras-chave variadas
    query = f"{theme} motivation lifestyle nature city"
    images = fetch_broll(query, n=6, base_dir=str(out_dir / "broll"))
    if not images:
        raise RuntimeError("Nenhuma imagem encontrada via Pexels. Verifique PEXELS_KEY.")

    # 5) Montagem do vídeo principal com narração PT-BR e branding final
    mp4_out = str(out_dir / "daily_master_1080x1920_60s.mp4")
    build_video(images, mp3_pt, mp4_out, target_secs=target_secs, music_dir=music_dir, branding_handle=branding_handle)

    # 6) Legendas SRT com base na duração real por bloco
    write_srt_from_blocks(blocks_pt, parts_pt, str(out_dir / "captions_pt-BR.srt"))
    write_srt_from_blocks(blocks_en, parts_en, str(out_dir / "captions_en.srt"))
    write_srt_from_blocks(blocks_es, parts_es, str(out_dir / "captions_es.srt"))

    print("Concluído:", out_dir)

if __name__ == "__main__":
    main()
