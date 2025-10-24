import math, os, io, tempfile, pathlib
from typing import List, Tuple
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip
from PIL import Image

def _ken_burns(img_path: str, dur: float, size=(1080,1920)) -> ImageClip:
    W,H = size
    img = Image.open(img_path).convert('RGB')
    img = img.resize(size, resample=Image.LANCZOS)
    clip = ImageClip(img).set_duration(dur)
    # pequeno zoom
    zoom = 1.05
    return clip.resize(lambda t: 1 + (zoom-1)*(t/dur))

def assemble_video(images: List[str], per_sec: float, out_path: str, audio_path: str = None) -> None:
    clips = [_ken_burns(p, per_sec) for p in images]
    video = concatenate_videoclips(clips, method="compose") if clips else ImageClip(color=(0,0,0), size=(1080,1920), duration=per_sec)
    if audio_path and os.path.exists(audio_path):
        video = video.set_audio(AudioFileClip(audio_path))
    video.write_videofile(out_path, fps=30, codec='libx264', audio=bool(audio_path), preset='medium', threads=4, logger=None)
