from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, concatenate_videoclips
import requests, io, os, textwrap

W, H, DUR = 1080, 1920, 60

def _download(url:str):
    return requests.get(url, timeout=30).content

def _captioned_image(img_bytes:bytes, text:str) -> Image.Image:
    base = Image.open(io.BytesIO(img_bytes)).convert('RGB').resize((W,H))
    draw = ImageDraw.Draw(base)
    # caixa de legenda
    pad = 32
    box_h = 300
    draw.rectangle([(0,H-box_h),(W,H)], fill=(0,0,0,160))
    # texto
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 54)
    except:
        font = ImageFont.load_default()
    wrapped = textwrap.fill(text, width=28)
    draw.multiline_text((pad, H-box_h+pad), wrapped, font=font, fill=(255,255,255))
    return base

def build_video(image_urls:list[str], lines:list[str], out_path:str):
    if not image_urls:
        raise RuntimeError("Sem imagens para compor o vídeo.")
    per = max(2, DUR // max(1,len(image_urls)))  # segundos por cena
    clips = []
    for i, url in enumerate(image_urls):
        text = lines[i % len(lines)]
        img_bytes = _download(url)
        frame = _captioned_image(img_bytes, text)
        buf = io.BytesIO()
        frame.save(buf, format='JPEG', quality=92)
        buf.seek(0)
        clip = ImageClip(buf).set_duration(per)
        clips.append(clip)
    video = concatenate_videoclips(clips).set_duration(DUR)
    video.write_videofile(out_path, fps=30, codec='libx264', audio=False)
