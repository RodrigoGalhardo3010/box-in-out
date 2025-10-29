# core/assemble.py
import os, random, pathlib
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
from PIL import Image

W, H = 1080, 1920

def ken_burns(path, dur):
    img = Image.open(path).convert("RGB").resize((W, H))
    clip = ImageClip(img).set_duration(dur)
    zoom = 1.05
    return clip.resize(lambda t: 1 + (zoom - 1) * (t / dur))

def build_video(image_paths, narration_mp3, out_mp4, target_secs=60, music_dir=None, branding_handle=None):
    per_img = target_secs / max(1, len(image_paths))
    clips = [ken_burns(p, per_img) for p in image_paths]

    # Branding simples: quadro final com handle (3s)
    if branding_handle:
        txt_clip = (ImageClip(Image.new("RGB",(W,H),(0,0,0)))
                    .set_duration(3))
        clips.append(txt_clip)

    video = concatenate_videoclips(clips, method="compose")

    narration = AudioFileClip(narration_mp3)
    audio_layers = [narration.volumex(1.0)]

    if music_dir and os.path.isdir(music_dir):
        tracks = [os.path.join(music_dir, f) for f in os.listdir(music_dir) if f.lower().endswith((".mp3", ".wav", ".m4a"))]
        if tracks:
            bg = AudioFileClip(random.choice(tracks)).volumex(0.15)
            bg = bg.subclip(0, min(video.duration, bg.duration))
            audio_layers.append(bg)

    final_audio = CompositeAudioClip(audio_layers)
    video = video.set_audio(final_audio).set_duration(target_secs)

    pathlib.Path(os.path.dirname(out_mp4)).mkdir(parents=True, exist_ok=True)
    video.write_videofile(out_mp4, fps=30, codec="libx264", audio_codec="aac", threads=4, preset="medium")
    return out_mp4
