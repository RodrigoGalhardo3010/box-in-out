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
        print("[trends] SERPAPI_KEY não configurada")
        return []
    
    # SerpApi para Google Trends usa 'geo' (não 'gl')
    params = {
        "engine": "google_trends",
        "data_type": "TIMESERIES",  # ou "GEO_MAP", "RELATED_QUERIES"
        "q": "all",  # para trending searches
        "geo": region.upper(),  # ex.: BR, US, FR...
        "api_key": api_key,
    }
    
    try:
        search = GoogleSearch(params)
        data = search.get_dict() or {}
        
        out: List[Dict] = []
        
        # Tenta diferentes estruturas de resposta
        # Estrutura 1: daily_searches
        if "daily_searches" in data:
            for day in data.get("daily_searches", [])[:limit]:
                for search_item in day.get("searches", []):
                    title = search_item.get("query", "").strip()
                    if not title:
                        continue
                    out.append({
                        "title": title,
                        "related": search_item.get("related_queries", []),
                        "traffic": search_item.get("formattedTraffic")
                    })
        
        # Estrutura 2: trending_searches
        elif "trending_searches" in data:
            for day in data.get("trending_searches", []):
                for t in day.get("trending_searches", []):
                    title = (t.get("title") or "").strip()
                    if not title:
                        continue
                    related = []
                    for q in (t.get("relatedQueries") or t.get("related_queries") or []):
                        rel = q.get("query") or q.get("title")
                        if rel:
                            related.append(rel)
                    out.append({
                        "title": title,
                        "related": related,
                        "traffic": t.get("formattedTraffic")
                    })
        
        # Estrutura 3: interest_over_time
        elif "interest_over_time" in data:
            timeline = data.get("interest_over_time", {}).get("timeline_data", [])
            if timeline:
                # Pega os tópicos mais populares
                out.append({
                    "title": data.get("search_parameters", {}).get("q", "Trending Topic"),
                    "related": [],
                    "traffic": None
                })
        
        # dedup e corte
        seen = set()
        dedup: List[Dict] = []
        for t in out:
            k = t["title"].lower()
            if k and k not in seen:
                seen.add(k)
                dedup.append(t)
        
        result = dedup[:limit]
        if result:
            print(f"[trends] SerpApi retornou {len(result)} tópicos")
        return result
        
    except Exception as e:
        print(f"[trends] SerpApi erro: {e}")
        return []

def _serpapi_realtime_trends(limit: int, region: str) -> List[Dict]:
    """Alternativa: usa trending searches em tempo real."""
    try:
        from serpapi import GoogleSearch
    except Exception:
        return []
    
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return []
    
    params = {
        "engine": "google_trends_trending_now",
        "geo": region.upper(),
        "api_key": api_key,
    }
    
    try:
        data = GoogleSearch(params).get_dict() or {}
        out: List[Dict] = []
        
        for item in data.get("trending_searches", [])[:limit]:
            title = item.get("query", "").strip()
            if title:
                out.append({
                    "title": title,
                    "related": item.get("related_queries", []),
                    "traffic": item.get("search_count")
                })
        
        if out:
            print(f"[trends] SerpApi realtime retornou {len(out)} tópicos")
        return out
        
    except Exception as e:
        print(f"[trends] SerpApi realtime erro: {e}")
        return []

def _pytrends_daily(limit: int, region: str) -> List[Dict]:
    """Fallback usando pytrends - DESABILITADO devido a erros 404."""
    # O pytrends está quebrado, então vamos pular direto para o backup
    print("[trends] pytrends desabilitado (erro 404 conhecido)")
    return []

def _get_backup_topics(limit: int, region: str) -> List[Dict]:
    """Tópicos backup inteligentes baseados na região."""
    
    backup_by_region = {
        "BR": [
            {"title": "Black Friday 2025", "related": ["promoções", "descontos"], "traffic": None},
            {"title": "Inteligência Artificial no Brasil", "related": ["IA", "tecnologia"], "traffic": None},
            {"title": "Carros Elétricos", "related": ["EV", "sustentabilidade"], "traffic": None},
            {"title": "Copa do Mundo 2026", "related": ["seleção", "futebol"], "traffic": None},
            {"title": "Energia Solar", "related": ["fotovoltaica", "economia"], "traffic": None},
            {"title": "Saúde Mental", "related": ["ansiedade", "depressão"], "traffic": None},
            {"title": "E-commerce Brasil", "related": ["vendas online", "marketplace"], "traffic": None},
            {"title": "Bitcoin e Criptomoedas", "related": ["cripto", "investimento"], "traffic": None},
            {"title": "Receitas Fitness", "related": ["dieta", "saúde"], "traffic": None},
            {"title": "Empreendedorismo Digital", "related": ["negócios online", "startup"], "traffic": None},
        ],
        "US": [
            {"title": "AI Technology 2025", "related": ["ChatGPT", "automation"], "traffic": None},
            {"title": "Stock Market Trends", "related": ["investing", "economy"], "traffic": None},
            {"title": "Electric Vehicles", "related": ["Tesla", "EV"], "traffic": None},
            {"title": "Cybersecurity", "related": ["data protection", "hacking"], "traffic": None},
            {"title": "Climate Change", "related": ["environment", "sustainability"], "traffic": None},
            {"title": "Mental Health", "related": ["wellness", "therapy"], "traffic": None},
            {"title": "Remote Work", "related": ["work from home", "productivity"], "traffic": None},
            {"title": "Cryptocurrency", "related": ["Bitcoin", "blockchain"], "traffic": None},
            {"title": "Space Exploration", "related": ["NASA", "SpaceX"], "traffic": None},
            {"title": "Social Media Trends", "related": ["TikTok", "Instagram"], "traffic": None},
        ],
    }
    
    # Tópicos genéricos se região não estiver no dicionário
    default = backup_by_region.get("BR")  # usa BR como padrão
    topics = backup_by_region.get(region.upper(), default)
    
    return topics[:limit]

def top_topics_week(limit: int = 20, region: str | None = None) -> List[Dict]:
    """Busca tópicos em tendência com múltiplas fontes."""
    region = region or os.getenv("TRENDS_REGION", "BR")
    
    print(f"[trends] Buscando tendências para região: {region}")
    
    # 1) Tenta SerpApi realtime (mais confiável)
    items = _serpapi_realtime_trends(limit, region)
    if items:
        return items
    
    # 2) Tenta SerpApi daily trends
    items = _serpapi_daily_trends(limit, region)
    if items:
        return items
    
    # 3) Pytrends desabilitado (retorna vazio)
    # items = _pytrends_daily(limit, region)
    
    # 4) Backup inteligente baseado na região
    print(f"[trends] Usando tópicos backup para {region}")
    backup = _get_backup_topics(limit, region)
    return backup
