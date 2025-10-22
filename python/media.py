import os, requests
PEXELS_KEY = os.getenv("PEXELS_KEY")

def pexels_images(query: str, limit:int=5) -> list[str]:
    if not PEXELS_KEY:
        return []
    r = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": PEXELS_KEY},
        params={"query": query, "orientation":"portrait", "per_page": limit}
    )
    r.raise_for_status()
    return [p["src"]["large2x"] for p in r.json().get("photos", [])]
