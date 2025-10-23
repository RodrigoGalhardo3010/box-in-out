from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, concatenate_videoclips
import requests, io, os, textwrap, pathlib

W, H, DUR = 1080, 1920, 60

def _download_or_load(source: str) -> bytes:
    """Baixa de URL ou lê de arquivo local."""
    # Verifica se é URL
    if source.startswith(('http://', 'https://')):
        print(f"    Baixando: {source[:60]}...")
        return requests.get(source, timeout=30).content
    
    # É arquivo local
    if os.path.exists(source):
        print(f"    Carregando: {os.path.basename(source)}")
        with open(source, 'rb') as f:
            return f.read()
    
    raise FileNotFoundError(f"Imagem não encontrada: {source}")

def _captioned_image(img_bytes: bytes, text: str) -> Image.Image:
    """Cria imagem com legenda."""
    base = Image.open(io.BytesIO(img_bytes)).convert('RGB').resize((W, H))
    draw = ImageDraw.Draw(base)
    
    # caixa de legenda
    pad = 32
    box_h = 300
    draw.rectangle([(0, H - box_h), (W, H)], fill=(0, 0, 0, 180))
    
    # texto
    try:
        # Tenta diferentes fontes
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 54)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 54)
            except:
                font = ImageFont.load_default()
    
    wrapped = textwrap.fill(text, width=28)
    draw.multiline_text((pad, H - box_h + pad), wrapped, font=font, fill=(255, 255, 255))
    
    return base

def build_video(image_sources: list[str], lines: list[str], out_path: str):
    """
    Constrói vídeo a partir de imagens e legendas.
    
    Args:
        image_sources: Lista de URLs ou caminhos de arquivo das imagens
        lines: Lista de textos para legendas
        out_path: Caminho do arquivo de vídeo de saída
    """
    if not image_sources:
        raise RuntimeError("Sem imagens para compor o vídeo.")
    
    if not lines:
        raise RuntimeError("Sem legendas para o vídeo.")
    
    print(f"  [video] Construindo vídeo com {len(image_sources)} imagens...")
    
    per = max(2, DUR // max(1, len(image_sources)))  # segundos por cena
    clips = []
    
    for i, source in enumerate(image_sources):
        try:
            text = lines[i % len(lines)]
            
            # Baixa ou carrega a imagem
            img_bytes = _download_or_load(source)
            
            # Cria frame com legenda
            frame = _captioned_image(img_bytes, text)
            
            # Converte para bytes
            buf = io.BytesIO()
            frame.save(buf, format='JPEG', quality=92)
            buf.seek(0)
            
            # Cria clip
            clip = ImageClip(buf.getvalue()).set_duration(per)
            clips.append(clip)
            
            print(f"    Clip {i+1}/{len(image_sources)} criado")
            
        except Exception as e:
            print(f"    Erro ao processar imagem {i+1}: {e}")
            continue
    
    if not clips:
        raise RuntimeError("Nenhum clip foi criado com sucesso.")
    
    # Concatena e exporta
    print(f"  [video] Concatenando {len(clips)} clips...")
    video = concatenate_videoclips(clips, method="compose")
    video = video.set_duration(min(DUR, len(clips) * per))
    
    print(f"  [video] Exportando para {out_path}...")
    video.write_videofile(
        out_path, 
        fps=30, 
        codec='libx264',
        audio=False,
        preset='medium',
        threads=4,
        logger=None  # Remove logs verbosos
    )
    
    print(f"  [video] Vídeo salvo: {out_path}")
