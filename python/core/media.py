# core/media.py
import os, requests, pathlib, random

PEXELS_URL = "https://api.pexels.com/v1/search"

def fetch_broll(query, n=6, base_dir="python/output/tmp"):
    key = os.getenv("PEXELS_KEY")
    pathlib.Path(base_dir).mkdir(parents=True, exist_ok=True)
    r = requests.get(PEXELS_URL, headers={"Authorization": key}, params={"query": query, "per_page": n*2})
    r.raise_for_status()
    items = r.json().get("photos", [])
    random.shuffle(items)
    paths = []
    for i, p in enumerate(items[:n]):
        src = p["src"].get("large2x") or p["src"].get("original")
        img = requests.get(src, timeout=30).content
        fp = pathlib.Path(base_dir) / f"img_{i}.jpg"
        fp.write_bytes(img)
        paths.append(str(fp))
    return paths
