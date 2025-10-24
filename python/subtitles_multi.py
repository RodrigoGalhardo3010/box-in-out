import srt, datetime as dt
from typing import List, Dict

def srt_from_timings(lines: List[str], timings_ms: List[int]) -> str:
    """Gera SRT a partir de falas e duração por fala (ms)."""
    subs = []
    t = 0
    for i, (line, dur) in enumerate(zip(lines, timings_ms), start=1):
        start = dt.timedelta(milliseconds=t)
        end = dt.timedelta(milliseconds=t+dur)
        subs.append(srt.Subtitle(index=i, start=start, end=end, content=line))
        t += dur
    return srt.compose(subs)
