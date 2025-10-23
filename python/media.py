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
                "size": "large"  # imagens grandes para melhor qualidade
            },
            timeout=10
        )
        r.raise_for_status()
        
        photos = r.json().get("photos", [])
        if not photos:
            print(f"[pexels] Nenhuma imagem encontrada para '{query}'")
            return []
        
        print(f"[pexels] {len(photos)} imagens encontradas para '{query}'")
        
        # Cria diretório temporário para cache
        cache_dir = pathlib.Path(__file__).parent / "output" / "pexels_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_paths = []
        
        # Baixa cada imagem
        for idx, photo in enumerate(photos):
            try:
                # Pega URL da imagem em alta qualidade
                img_url = photo["src"].get("large2x") or photo["src"].get("large") or photo["src"]["original"]
                
                # Nome do arquivo baseado no ID da foto
                photo_id = photo.get("id", idx)
                filename = f"pexels_{photo_id}_{idx}.jpg"
                filepath = cache_dir / filename
                
                # Se já existe em cache, usa ele
                if filepath.exists():
                    downloaded_paths.append(str(filepath))
                    continue
                
                # Baixa a imagem
                img_response = requests.get(img_url, timeout=15, stream=True)
                img_response.raise_for_status()
                
                # Abre com PIL para validar e converter
                img = Image.open(BytesIO(img_response.content))
                
                # Converte para RGB (remove alpha se tiver)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Redimensiona se necessário (para economizar espaço)
                max_size = (1920, 1080)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Salva como JPEG
                img.save(filepath, 'JPEG', quality=90, optimize=True)
                downloaded_paths.append(str(filepath))
                
                print(f"  [pexels] Baixada imagem {idx+1}/{len(photos)}")
                
            except Exception as e:
                print(f"  [pexels] Erro ao baixar imagem {idx}: {e}")
                continue
        
        if not downloaded_paths:
            print(f"[pexels] Nenhuma imagem baixada com sucesso para '{query}'")
            return []
        
        print(f"[pexels] {len(downloaded_paths)} imagens prontas")
        return downloaded_paths
        
    except requests.exceptions.RequestException as e:
        print(f"[pexels] Erro na API: {e}")
        return []
    except Exception as e:
        print(f"[pexels] Erro geral: {e}")
        return []


def clear_pexels_cache():
    """Limpa o cache de imagens do Pexels."""
    cache_dir = pathlib.Path(__file__).parent / "output" / "pexels_cache"
    if cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir)
        print("[pexels] Cache limpo")
