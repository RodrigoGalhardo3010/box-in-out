# Box In And Out — TikTok Auto Shorts (Python)

Publica **10 vídeos de 1 minuto por dia** no TikTok, em **PT/EN/ES/FR/IT/DE/ZH**, usando **Google Trends** (SerpApi/pytrends), imagens **Pexels**, legendas queimadas simples e (opcional) **upload** via TikTok **Content Posting API**.

> **Primeiro uso:** os vídeos são gerados em `python/output/`.
> Para publicar no TikTok pela API, configure as variáveis e a permissão `video.upload` no TikTok Developers.

## Estrutura
```
python/
  requirements.txt
  main.py
  trends.py
  script_writer.py
  media.py
  video.py
  subtitles.py
  translate.py
  tiktok.py
.github/workflows/daily.yml
public/terms.html
public/privacy.html
```

## Variáveis de ambiente (GitHub → Settings → Secrets and variables → Actions)
- `SERPAPI_KEY` — (Trends)
- `PEXELS_KEY` — (imagens)
- `GCP_KEY_JSON` — conteúdo do key.json do Google Translate
- `TIKTOK_ACCESS_TOKEN` (opcional, postar)
- `TIKTOK_OPEN_ID` (opcional, postar)
- `ENABLE_TIKTOK_UPLOAD` = `false` | `true` (padrão: false)

## Rodar local
```bash
cd python
pip install -r requirements.txt
export SERPAPI_KEY=...
export PEXELS_KEY=...
python main.py
```

Os vídeos saem em `python/output/PT`, `EN`, etc.

## Publicação TikTok (opcional)
- Crie app em developers.tiktok.com, habilite **Content Posting API** e o escopo **video.upload**.
- Preencha `TIKTOK_ACCESS_TOKEN` e `TIKTOK_OPEN_ID`.
- Defina `ENABLE_TIKTOK_UPLOAD=true` no GitHub/Secrets para ativar o envio.
- O código usa **upload direto por arquivo** *placeholder*. Ajuste `tiktok.py` para seu fluxo exato (Direct Post/rascunho).
