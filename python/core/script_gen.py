# python/core/script_gen.py
# Geração de roteiro (PT-BR) e traduções (EN/ES)
# - Provider: Bedrock (Claude 3.5 Sonnet) ou OpenAI (fallback/primário, se OPENAI_API_KEY estiver definido)
# - Parsing robusto: extrai o primeiro JSON com "blocks" mesmo se o modelo escrever prosa antes/depois
# - Normalização: garante 6–8 blocos, remove lixo
# - Fallback local: roteiro seguro quando a LLM falhar

import os
import re
import json
import datetime

import requests
import boto3
import botocore

DEFAULT_THEME = os.getenv("THEME_SEED", "autoajuda")
BEDROCK_MODEL = os.getenv(
    "BEDROCK_MODEL_ID",
    "anthropic.claude-3-5-sonnet-20240620-v1:0"
)

# ======================================================================
# Prompts: resposta ESTRITA em JSON
# ======================================================================

SYSTEM_PT = (
    "Você é um roteirista de vídeos curtos de autoajuda. "
    "Responda ESTRITAMENTE em JSON válido, sem qualquer texto antes ou depois. "
    "Formato obrigatório: {\"language\":\"pt-BR\",\"blocks\":[{\"text\":\"...\"}, ...]}. "
    "Use entre 6 e 8 blocos, com 1–2 frases curtas por bloco. "
    "Tom: pragmático, gentil, sem promessas exageradas. "
    "Foque em um micro-hábito aplicável hoje. "
    "Inclua um CTA sutil no último bloco."
)

# ATENÇÃO: chaves do exemplo JSON precisam ser ESCAPADAS ({{ }}) para não colidirem com str.format
PROMPT_PT = (
    "Crie um roteiro ORIGINAL de autoajuda com o tema: \"{theme}\".\n"
    "- Duração alvo: ~60s de narração.\n"
    "- 6 a 8 blocos; cada bloco com 1–2 frases curtas.\n"
    "- Proíba listas numeradas, markdown, emojis e comentários.\n"
    "- SAÍDA: SOMENTE JSON MINIFICADO no formato:\n"
    "{{\"language\":\"pt-BR\",\"blocks\":[{{\"text\":\"...\"}}]}}\n"
)

# ======================================================================
# Providers
# ======================================================================

def _openai_chat(messages, model="gpt-4o-mini"):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY ausente")
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": model, "messages": messages, "temperature": 0.8},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]

def _bedrock_claude(prompt_text, system_text=None):
    region = os.getenv("AWS_REGION", "us-east-1")
    client = boto3.client("bedrock-runtime", region_name=region)
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1200,
        "temperature": 0.8,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt_text}]}
        ]
    }
    if system_text:
        payload["system"] = system_text
    body = json.dumps(payload)
    response = client.invoke_model(
        modelId=BEDROCK_MODEL,
        body=body,
        contentType="application/json",
        accept="application/json"
    )
    out = json.loads(response["body"].read())
    return out["content"][0]["text"]

# ======================================================================
# Parsing robusto de JSON e fallbacks
# ======================================================================

def _extract_json_with_blocks(text: str):
    """Extrai o primeiro objeto JSON contendo a chave 'blocks' mesmo
    que haja prosa antes/depois. Evita regex recursiva; usa varredura
    por chaves balanceadas e respeita strings/escapes."""
    # 1) Tenta bloco cercado por ```json ... ```
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        cand = fenced.group(1)
        data = json.loads(cand)
        if isinstance(data, dict) and "blocks" in data:
            return data

    # 2) Varredura manual por chaves balanceadas
    n = len(text)
    i = 0
    while i < n:
        if text[i] == "{":
            depth = 0
            j = i
            in_str = False
            esc = False
            while j < n:
                ch = text[j]
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == '"':
                        in_str = False
                else:
                    if ch == '"':
                        in_str = True
                    elif ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            cand = text[i:j+1]
                            try:
                                data = json.loads(cand)
                                if isinstance(data, dict) and "blocks" in data:
                                    return data
                            except json.JSONDecodeError:
                                pass
                            break
                j += 1
            i = j
        i += 1

    raise json.JSONDecodeError("JSON com 'blocks' não encontrado", text, 0)

def _normalize_blocks(data):
    if not isinstance(data, dict) or "blocks" not in data:
        raise ValueError("payload inválido: 'blocks' ausente")

    raw = data.get("blocks") or []
    norm = []
    for b in raw:
        if isinstance(b, dict):
            t = str(b.get("text", "")).strip()
        else:
            t = str(b).strip()
        if t:
            norm.append({"text": t})

    # Garante 6–8 blocos
    if len(norm) > 8:
        norm = norm[:8]
    if len(norm) < 6 and norm:
        last = norm[-1]["text"]
        while len(norm) < 6:
            norm.append({"text": last})

    return {"language": "pt-BR", "blocks": norm}

def _fallback_script(theme: str):
    base = [
        f"Respire fundo. Hoje vamos falar de {theme} em 1 minuto.",
        "Escolha um hábito pequeno para ajustar hoje, nada grandioso, apenas um passo concreto.",
        "Defina um gatilho: quando X acontecer, você fará Y por 2 minutos.",
        "Facilite o ambiente: deixe visível o que ajuda e esconda o que atrapalha.",
        "Registre uma linha por dia. Sem culpa, apenas dados para aprender com o processo.",
        "Se falhar, recomece ainda hoje, em versão menor. Consistência supera intensidade.",
        "Se fez sentido, compartilhe com alguém e salve para lembrar amanhã."
    ]
    return {"language": "pt-BR", "blocks": [{"text": t} for t in base]}

# ======================================================================
# API pública
# ======================================================================

def generate_script(theme=DEFAULT_THEME, provider="bedrock"):
    """Gera o roteiro em PT-BR como JSON com 6–8 blocos."""
    today = datetime.date.today().isoformat()
    prompt_text = PROMPT_PT.format(theme=f"{theme} {today}")
    content = None

    try:
        if provider == "openai":
            content = _openai_chat(
                [{"role": "system", "content": SYSTEM_PT},
                 {"role": "user", "content": prompt_text}]
            )
        else:
            content = _bedrock_claude(prompt_text, system_text=SYSTEM_PT)
    except botocore.exceptions.ClientError:
        # Fallback: se Bedrock não estiver habilitado, tenta OpenAI
        if os.getenv("OPENAI_API_KEY"):
            content = _openai_chat(
                [{"role": "system", "content": SYSTEM_PT},
                 {"role": "user", "content": prompt_text}]
            )
        else:
            return _fallback_script(theme)
    except Exception:
        # Falha geral na chamada
        if os.getenv("OPENAI_API_KEY"):
            try:
                content = _openai_chat(
                    [{"role": "system", "content": SYSTEM_PT},
                     {"role": "user", "content": prompt_text}]
                )
            except Exception:
                return _fallback_script(theme)
        else:
            return _fallback_script(theme)

    # Parsing robusto
    try:
        if content and content.strip().startswith("{"):
            data = json.loads(content)
        else:
            data = _extract_json_with_blocks(content)
        return _normalize_blocks(data)
    except Exception:
        return _fallback_script(theme)

def translate_blocks(blocks, target_lang, provider="bedrock"):
    """Traduz blocos mantendo a contagem e a ordem, retornando [{text:...}, ...]."""
    text = "\n".join([b["text"] for b in blocks])
    prompt = (
        f"Traduza as linhas abaixo para {target_lang}, mantendo sentido, concisão e naturalidade. "
        f"Responda com as linhas na MESMA ORDEM, uma por linha, sem numeração e sem comentários.\n\n{text}"
    )

    try:
        if provider == "openai":
            out = _openai_chat(
                [{"role": "system", "content": "Traduza preservando concisão e naturalidade."},
                 {"role": "user", "content": prompt}]
            )
        else:
            out = _bedrock_claude(prompt, system_text="Traduza preservando concisão e naturalidade.")
    except botocore.exceptions.ClientError:
        if os.getenv("OPENAI_API_KEY"):
            out = _openai_chat(
                [{"role": "system", "content": "Traduza preservando concisão e naturalidade."},
                 {"role": "user", "content": prompt}]
            )
        else:
            out = text
    except Exception:
        if os.getenv("OPENAI_API_KEY"):
            try:
                out = _openai_chat(
                    [{"role": "system", "content": "Traduza preservando concisão e naturalidade."},
                     {"role": "user", "content": prompt}]
                )
            except Exception:
                out = text
        else:
            out = text

    out_lines = [x.strip() for x in out.split("\n") if x.strip()]
    if len(out_lines) < len(blocks):
        out_lines += [""] * (len(blocks) - len(out_lines))
    return [{"text": t} for t in out_lines[:len(blocks)]]
