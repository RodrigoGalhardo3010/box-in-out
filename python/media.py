import os, requests, pathlib
from io import BytesIO
from PIL import Image

PEXELS_KEY = os.getenv("PEXELS_KEY")

def pexels_images(query: str, limit: int = 5) -> list[str]:
    """
    Busca imagens no Pexels e retorna caminhos de arquivos locais.
    
    Args:
        query: termo de busca
        limit: número máximo de imagens
        
    Returns:
        Lista de caminhos de arquivos das imagens baixadas
    """
    if not PEXELS_KEY:
        print("[pexels] PEXELS_KEY não configurada")
        return []
    
    try:
        # Busca imagens na API
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_KEY},
            params={
                "query": query, 
                "orientation": "portrait", 
                "per_page": limit,
            },
            timeout=10
        )
        r.raise_for_status()
        
        photos = r.json().get("photos", [])
        if not photos:
            print(f"[pexels] Nenhuma imagem encontrada para '{query}'")
            return []
        
        print(f"[pexels] {len(photos)} imagens encontradas para '{query}'")
        
        # Cria diretório de cache
        cache_dir = pathlib.Path(__file__).parent / "output" / "pexels_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_paths = []
        
        # Baixa cada imagem
        for idx, photo in enumerate(photos):
            try:
                # URL da imagem
                img_url = photo["src"].get("large2x") or photo["src"].get("large") or photo["src"]["original"]
                
                # Nome do arquivo
                photo_id = photo.get("id", idx)
                filename = f"pexels_{photo_id}.jpg"
                filepath = cache_dir / filename
                
                # Se já existe em cache, reutiliza
                if filepath.exists() and filepath.stat().st_size > 0:
                    downloaded_paths.append(str(filepath))
                    print(f"  [pexels] {idx+1}/{len(photos)} (cache)")
                    continue
                
                # Baixa a imagem
                print(f"  [pexels] Baixando {idx+1}/{len(photos)}...")
                img_response = requests.get(img_url, timeout=20, stream=True)
                img_response.raise_for_status()
                
                # Valida e converte
                img = Image.open(BytesIO(img_response.content))
                
                # Garante RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Redimensiona se muito grande
                max_size = (1920, 1920)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Salva
                img.save(filepath, 'JPEG', quality=90, optimize=True)
                downloaded_paths.append(str(filepath))
                
            except Exception as e:
                print(f"  [pexels] Erro na imagem {idx+1}: {e}")
                continue
        
        if not downloaded_paths:
            print(f"[pexels] Nenhuma imagem baixada para '{query}'")
            return []
        
        print(f"[pexels] {len(downloaded_paths)} imagens prontas")
        return downloaded_paths
        
    except requests.exceptions.RequestException as e:
        print(f"[pexels] Erro na API: {e}")
        return []
    except Exception as e:
        print(f"[pexels] Erro: {e}")
        return []


def clear_pexels_cache():
    """Limpa o cache de imagens do Pexels."""
    cache_dir = pathlib.Path(__file__).parent / "output" / "pexels_cache"
    if cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        print("[pexels] Cache limpo")
