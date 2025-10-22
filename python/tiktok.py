import os, requests, mimetypes

TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")
OPEN_ID = os.getenv("TIKTOK_OPEN_ID")
ENABLE = os.getenv("ENABLE_TIKTOK_UPLOAD", "false").lower() == "true"

BASE = "https://open.tiktokapis.com/v2"

def upload_draft_file(mp4_path:str, title:str, hashtags:list[str]|None=None):
    """Placeholder de envio. Alguns apps usam fluxo init->upload->publish.
    Aqui deixamos um esqueleto de "multipart" (pode mudar conforme aprovação do app).
    Se ENABLE=false ou faltarem credenciais, apenas retorna sem enviar.
    """
    if not ENABLE or not TOKEN or not OPEN_ID:
        return {"sent": False, "reason": "upload desativado ou credenciais ausentes", "file": mp4_path}
    # Exemplo ilustrativo (pode variar conforme seu app):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    files = {"video": (os.path.basename(mp4_path), open(mp4_path, 'rb'), 'video/mp4')}
    data = {
        "open_id": OPEN_ID,
        "title": title[:220],
    }
    # Endpoint real pode ser diferente dependendo do modo (draft/direct). Ajuste conforme sua aprovação.
    url = f"{BASE}/post/publish/inspection/"  # rascunho/inspeção ilustrativo
    r = requests.post(url, headers=headers, files=files, data=data, timeout=120)
    try:
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"sent": False, "error": str(e), "status": getattr(r, 'status_code', None), "text": r.text[:500]}
