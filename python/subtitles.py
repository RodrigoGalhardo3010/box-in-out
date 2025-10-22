import srt, datetime
from typing import List

def srt_from_lines(lines: List[str], dur_per_line: float = 3.0) -> str:
    subs = []
    t = 0.0
    for i, line in enumerate(lines, 1):
        start = datetime.timedelta(seconds=t)
        end = datetime.timedelta(seconds=t + dur_per_line)
        subs.append(srt.Subtitle(index=i, start=start, end=end, content=line))
        t += dur_per_line
    return srt.compose(subs)
