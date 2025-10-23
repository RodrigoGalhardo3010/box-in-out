import os, pathlib, shutil
from trends import top_topics_week
from script_writer import build_script
from media import pexels_images, clear_pexels_cache
from video import build_video
from translate import translate_text
from subtitles import srt_from_lines
import re

OUT = pathlib.Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)

def slug(s: str) -> str:
    """Converte texto em slug válido para nome de arquivo."""
    s = re.sub(r"[^\w\- ]+", "", s).strip().lower().replace(" ", "-")
    return s[:60] if s else "video"

def generate_for_language(topic: str, lines: list[str], lang_code: str, images: list[str]):
    """Gera vídeo para um idioma específico."""
    try:
        # Traduz linhas
        t_lines = [translate_text(x, lang_code) if lang_code != 'pt' else x for x in lines]
        
        # Cria diretório do idioma
        lang_dir = OUT / lang_code.upper()
        lang_dir.mkdir(parents=True, exist_ok=True)
        
        # Caminhos de saída
        name = f"{slug(topic)}-{lang_code}.mp4"
        out_path = lang_dir / name
        
        # Gera vídeo
        build_video(images, t_lines, str(out_path))
        
        # Gera SRT
        srt = srt_from_lines(t_lines, dur_per_line=3.0)
        srt_path = lang_dir / f"{slug(topic)}-{lang_code}.srt"
        srt_path.write_text(srt, encoding='utf-8')
        
        return str(out_path)
        
    except Exception as e:
        print(f"    Erro ao gerar vídeo: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("="*70)
    print("GERADOR DE VÍDEOS MULTI-IDIOMA")
    print("="*70)
    
    region = os.getenv("TRENDS_REGION", "BR")
    topics = top_topics_week(limit=25, region=region) or []
    
    if not topics:
        print("\n[AVISO] Nenhum tópico retornado.")
        print("Verifique suas variáveis de ambiente:")
        print("  - SERPAPI_KEY (para tendências)")
        print("  - PEXELS_KEY (para imagens)")
        return
    
    # Processa os 10 primeiros tópicos
    selected = topics[:10]
    total_videos = 0
    
    for idx, t in enumerate(selected, start=1):
        topic = t.get("title") or f"Topico-{idx}"
        
        print(f"\n{'='*70}")
        print(f"[{idx}/10] {topic}")
        print('='*70)
        
        try:
            # 1. Gera script
            print("  [1/3] Gerando script...")
            lines = build_script(topic)
            if not lines:
                print("  ✗ Script vazio - pulando tópico")
                continue
            print(f"  ✓ Script: {len(lines)} linhas")
            
            # 2. Busca imagens
            print("  [2/3] Buscando imagens no Pexels...")
            images = pexels_images(topic, limit=5)
            if not images:
                print("  ✗ Sem imagens - pulando tópico")
                continue
            print(f"  ✓ Imagens: {len(images)} prontas")
            
            # 3. Gera vídeos em todos os idiomas
            print("  [3/3] Gerando vídeos...")
            success = 0
            
            for lang in ["pt", "en", "es", "fr", "it", "de", "zh"]:
                print(f"\n  [{lang.upper()}]")
                result = generate_for_language(topic, lines, lang, images)
                if result:
                    print(f"  ✓ [{lang.upper()}] {os.path.basename(result)}")
                    success += 1
                    total_videos += 1
                else:
                    print(f"  ✗ [{lang.upper()}] Falhou")
            
            print(f"\n  Resumo: {success}/7 idiomas OK")
            
        except KeyboardInterrupt:
            print("\n\n[INTERROMPIDO] Cancelado pelo usuário")
            break
        except Exception as e:
            print(f"  ✗ Erro geral: {e}")
            import traceback
            traceback.print_exc()
    
    # Resultado final
    print("\n" + "="*70)
    print(f"✓ CONCLUÍDO! {total_videos} vídeos gerados")
    print(f"📁 Salvos em: {OUT.absolute()}")
    print("="*70)
    
    # Opção de limpar cache (descomente se quiser limpar ao final)
    # clear_pexels_cache()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPrograma interrompido.")
    except Exception as e:
        print(f"\n\nErro fatal: {e}")
        import traceback
        traceback.print_exc()
