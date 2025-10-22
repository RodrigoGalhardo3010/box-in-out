import os, time
from typing import List, Dict
from serpapi import GoogleSearch
from pytrends.request import TrendReq

def top_topics_week(limit:int=20, region:str|None=None) -> List[Dict]:
    region = region or os.getenv("TRENDS_REGION","BR")
    serp_key = os.getenv("SERPAPI_KEY")
    topics: List[Dict] = []
    if serp_key:
        search = GoogleSearch({
            "engine":"google_trends",
            "trend_type":"daily_trends",
            "gl": region,
            "hl": "pt-BR" if region.upper()=="BR" else "en",
            "api_key": serp_key
        })
        data = search.get_dict()
        for day in data.get("trending_searches", []):
            for t in day.get("trending_searches", []):
                topics.append({
                    "title": t.get("title","").strip(),
                    "related": [q.get("query") for q in (t.get("relatedQueries") or [])],
                    "traffic": t.get("formattedTraffic")
                })
        seen=set(); dedup=[]
        for t in topics:
            k=t["title"].lower()
            if k and k not in seen:
                seen.add(k); dedup.append(t)
        return dedup[:limit]
    # fallback pytrends
    try:
        pn_map={"BR":"brazil","US":"united_states","FR":"france","DE":"germany","IT":"italy","ES":"spain"}
        py = TrendReq(hl='pt-BR', tz=0)
        daily = py.trending_searches(pn=pn_map.get(region.upper(), "brazil"))
        return [{"title": row[0], "related": [], "traffic": None} for _, row in daily.head(limit).iterrows()]
    except Exception as e:
        return []
