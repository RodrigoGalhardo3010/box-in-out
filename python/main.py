import os, pathlib, time, json, re
from trends import top_topics_week
from script_writer import build_script
from media import pexels_images
from video import build_video
from translate import translate_text, LANGS
from subtitles import srt_from_lines
import hashlib
from PIL import Image
import io

OUT = pathlib.Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)

def slug(s:str)->str:
    s = re.sub(r"[^\w\- ]+", "", s).strip().lower().replace(" ", "-")
    return s[:60] if s else "video"

def generate_for_language(topic:str, lines:list[str], lang_code:str, images:list):
    # traduz linhas básicas
    t_lines = [translate_text(x, lang_code) if lang_code!='pt' else x for x in lines]
    # paths
    lang_dir = OUT / lang_code.upper()
    lang_dir.mkdir(parents=True, exist_ok=True)
    name = f"{slug(topic)}-{lang_code}.mp4"
    out_path = lang_dir / name
    
    # Converte BytesIO para PIL Images ou salva como arquivos temporários
    processed_images = []
    temp_dir = OUT / "temp_images"
    temp_dir.mkdir(exist_ok=True)
    
    for idx, img_data in enumerate(images):
        if isinstance(img_data, (str, pathlib.Path)):
            # Já é um caminho de arquivo
            processed_images.append(img_data)
        elif hasattr(img_data, 'read'):
            # É BytesIO ou similar
            try:
                # Salva temporariamente
                temp_path = temp_dir / f"{slug(topic)}_{idx}.jpg"
                img = Image.open(img_data)
                img.save(temp_path, 'JPEG')
                processed_images.append(str(temp_path))
            except Exception as e:
                print(f"  Erro ao processar imagem {idx}: {e}")
        else:
            # Já é PIL Image
            temp_path = temp_dir / f"{slug(topic)}_{idx}.jpg"
            img_data.save(temp_path, 'JPEG')
            processed_images.append(str(temp_path))
    
    if not processed_images:
        print("  -> Nenhuma imagem processada com sucesso")
        return None
    
    # vídeo
    build_video(processed_images, t_lines, str(out_path))
    # srt
    srt = srt_from_lines(t_lines, dur_per_line=3.0)
    (lang_dir / f"{slug(topic)}-{lang_code}.srt").write_text(srt, encoding='utf-8')
    return str(out_path)

def main():
    region = os.getenv("TRENDS_REGION", "BR")
    topics = top_topics_week(limit=25, region=region) or []
    if not topics:
        print("[warn] Nenhum tópico retornado. Verifique suas chaves de tendências.")
        return
    # escolhe 10 primeiros distintos
    selected = topics[:10]
    for idx, t in enumerate(selected, start=1):
        topic = t.get("title") or f"Topico-{idx}"
        print(f"[topic] {topic}")
        lines = build_script(topic)
        images = pexels_images(topic, limit=5)
        if not images:
            print("  -> Sem imagens do Pexels; pulando.")
            continue
        
        for lang in ["pt","en","es","fr","it","de","zh"]:
            try:
                out = generate_for_language(topic, lines, lang, images)
                if out:
                    print(f"  [{lang}] ok -> {out}")
                else:
                    print(f"  [{lang}] falhou ao gerar")
            except Exception as e:
                print(f"  [{lang}] erro: {e}")
    
    # Limpa imagens temporárias
    temp_dir = OUT / "temp_images"
    if temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir)
    
    print("Concluído. Arquivos em ./python/output/")

if __name__ == "__main__":
    main()
