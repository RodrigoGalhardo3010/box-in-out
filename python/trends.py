import os
from typing import List, Dict

def _serpapi_daily_trends(limit: int, region: str) -> List[Dict]:
    """Usa SerpApi (pacote google-search-results) com engine google_trends."""
    try:
        from serpapi import GoogleSearch
    except Exception:
        return []

    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return []

    # SerpApi para Google Trends usa 'geo' (não 'gl')
    params = {
        "engine": "google_trends",
        "trend_type": "daily_trends",
        "geo": region.upper(),          # ex.: BR, US, FR...
        "api_key": api_key,
    }

    try:
        data = GoogleSearch(params).get_dict() or {}
        # Estrutura típica: data["trending_searches"][idx]["trending_searches"][...]
        out: List[Dict] = []
        for day in data.get("trending_searches", []):
            for t in day.get("trending_searches", []):
                title = (t.get("title") or "").strip()
                if not title:
                    continue
                related = []
                # alguns retornos usam 'relatedQueries' / outros 'related_queries'
                for q in (t.get("relatedQueries") or t.get("related_queries") or []):
                    rel = q.get("query") or q.get("title")
                    if rel:
                        related.append(rel)
                out.append({"title": title, "related": related, "traffic": t.get("formattedTraffic")})
        # dedup e corte
        seen = set()
        dedup: List[Dict] = []
        for t in out:
            k = t["title"].lower()
            if k and k not in seen:
                seen.add(k)
                dedup.append(t)
        return dedup[:limit]
    except Exception as e:
        # Log enxuto; o runner do GitHub mostrará isso
        print(f"[trends] SerpApi falhou: {e}")
        return []

def _pytrends_daily(limit: int, region: str) -> List[Dict]:
    """Fallback usando pytrends."""
    try:
        from pytrends.request import TrendReq
        pn_map = {
            "BR": "brazil", "US": "united_states", "FR": "france",
            "DE": "germany", "IT": "italy", "ES": "spain"
        }
        py = TrendReq(hl="pt-BR", tz=0)
        df = py.trending_searches(pn=pn_map.get(region.upper(), "brazil"))
        out = [{"title": row[0], "related": [], "traffic": None} for _, row in df.head(limit).iterrows()]
        return out
    except Exception as e:
        print(f"[trends] pytrends falhou: {e}")
        return []

def top_topics_week(limit: int = 20, region: str | None = None) -> List[Dict]:
    region = region or os.getenv("TRENDS_REGION", "BR")
    # 1) Tenta SerpApi
    items = _serpapi_daily_trends(limit, region)
    if items:
        return items
    # 2) Fallback pytrends
    items = _pytrends_daily(limit, region)
    if items:
        return items
    # 3) Backup (garante que o pipeline roda)
    print("[trends] Sem dados externos; retornando tópicos backup.")
    backup = [
        {"title": "Inteligência Artificial", "related": ["AI", "Machine Learning"], "traffic": None},
        {"title": "Carros Elétricos", "related": ["EV", "bateria"], "traffic": None},
        {"title": "Cibersegurança", "related": ["ransomware"], "traffic": None},
        {"title": "Energia Solar", "related": [], "traffic": None},
        {"title": "Saúde Digital", "related": [], "traffic": None},
        {"title": "E-commerce", "related": [], "traffic": None},
        {"title": "Criptomoedas", "related": [], "traffic": None},
        {"title": "Viagens 2025", "related": [], "traffic": None},
        {"title": "Empreendedorismo", "related": [], "traffic": None},
        {"title": "Produtividade", "related": [], "traffic": None},
    ]
    return backup[:limit]
