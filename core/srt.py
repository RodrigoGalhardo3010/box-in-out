# core/srt.py
import pathlib

def write_srt_from_blocks(blocks, piece_durations, out_path):
    lines = []
    t = 0.0
    for i, (b, dur) in enumerate(zip(blocks, piece_durations), start=1):
        start = t
        end = t + dur
        lines.append(f"{i}\n{_fmt(start)} --> {_fmt(end)}\n{b['text']}\n")
        t = end
    pathlib.Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    return out_path

def _fmt(sec):
    h = int(sec // 3600); sec -= h*3600
    m = int(sec // 60); sec -= m*60
    s = int(sec)
    ms = int((sec - s) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
