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

def convert_images_to_files(images: list, topic: str) -> list[str]:
    """Converte qualquer formato de imagem para arquivos temporários."""
    processed_images = []
    temp_dir = OUT / "temp_images"
    temp_dir.mkdir(exist_ok=True)
    
    for idx, img_data in enumerate(images):
        try:
            temp_path = temp_dir / f"{slug(topic)}_{idx}.jpg"
            
            if isinstance(img_data, (str, pathlib.Path)):
                # Já é um caminho de arquivo - copia para temp
                if os.path.exists(img_data):
                    img = Image.open(img_data)
                    img = img.convert('RGB')  # garante RGB
                    img.save(temp_path, 'JPEG', quality=95)
                    processed_images.append(str(temp_path))
                else:
                    print(f"  Aviso: arquivo não existe: {img_data}")
                    
            elif hasattr(img_data, 'read') or isinstance(img_data, (bytes, bytearray)):
                # É BytesIO, bytes ou similar
                if isinstance(img_data, (bytes, bytearray)):
                    img_data = io.BytesIO(img_data)
                
                # Reset do ponteiro se necessário
                if hasattr(img_data, 'seek'):
                    img_data.seek(0)
                
                img = Image.open(img_data)
                img = img.convert('RGB')  # garante RGB
                img.save(temp_path, 'JPEG', quality=95)
                processed_images.append(str(temp_path))
                
            elif isinstance(img_data, Image.Image):
                # Já é PIL Image
                img_data = img_data.convert('RGB')
                img_data.save(temp_path, 'JPEG', quality=95)
                processed_images.append(str(temp_path))
                
            else:
                print(f"  Aviso: tipo de imagem desconhecido: {type(img_data)}")
                
        except Exception as e:
            print(f"  Erro ao processar imagem {idx}: {e}")
            import traceback
            traceback.print_exc()
    
    return processed_images

def generate_for_language(topic:str, lines:list[str], lang_code:str, images:list):
    """Gera vídeo para um idioma específico."""
    # traduz linhas
    t_lines = [translate_text(x, lang_code) if lang_code!='pt' else x for x in lines]
    
    # paths
    lang_dir = OUT / lang_code.upper()
    lang_dir.mkdir(parents=True, exist_ok=True)
    name = f"{slug(topic)}-{lang_code}.mp4"
    out_path = lang_dir / name
    
    # Converte todas as imagens para arquivos
    processed_images = convert_images_to_files(images, topic)
    
    if not processed_images:
        print(f"  [{lang_code}] Nenhuma imagem processada com sucesso")
        return None
    
    print(f"  [{lang_code}] {len(processed_images)} imagens prontas")
    
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
        print(f"\n[topic {idx}/10] {topic}")
        
        try:
            lines = build_script(topic)
            if not lines:
                print("  -> Script vazio; pulando.")
                continue
                
            images = pexels_images(topic, limit=5)
            if not images:
                print("  -> Sem imagens do Pexels; pulando.")
                continue
            
            print(f"  -> {len(images)} imagens obtidas do Pexels")
            
            # Gera vídeo para cada idioma
            success_count = 0
            for lang in ["pt","en","es","fr","it","de","zh"]:
                try:
                    out = generate_for_language(topic, lines, lang, images)
                    if out:
                        print(f"  [{lang}] ✓ {out}")
                        success_count += 1
                    else:
                        print(f"  [{lang}] ✗ falhou")
                except Exception as e:
                    print(f"  [{lang}] ✗ erro: {e}")
                    import traceback
                    traceback.print_exc()
            
            print(f"  -> {success_count}/7 idiomas gerados com sucesso")
            
        except Exception as e:
            print(f"  Erro geral no tópico '{topic}': {e}")
            import traceback
            traceback.print_exc()
    
    # Limpa imagens temporárias
    print("\nLimpando arquivos temporários...")
    temp_dir = OUT / "temp_images"
    if temp_dir.exists():
        import shutil
        try:
            shutil.rmtree(temp_dir)
            print("  -> Temporários removidos")
        except Exception as e:
            print(f"  -> Erro ao limpar temporários: {e}")
    
    print("\n✓ Concluído! Arquivos em ./python/output/")

if __name__ == "__main__":
    main()
