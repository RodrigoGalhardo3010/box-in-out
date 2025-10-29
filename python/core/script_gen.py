# core/script_gen.py
import os, json, datetime
import requests
import boto3

DEFAULT_THEME = os.getenv("THEME_SEED", "autoajuda")
BEDROCK_MODEL = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")

SYSTEM_PT = (
 "Você é um roteirista de vídeos curtos de autoajuda. "
 "Escreva um roteiro inspirador, prático e direto, dividido em 6 a 8 blocos "
 "equilibrados para um vídeo de 60 segundos, com linguagem acessível e não clichê. "
 "Inclua um call-to-action suave no final. Não use listas numeradas."
)

PROMPT_PT = """Crie um roteiro original de autoajuda com o tema: "{theme}".
Requisitos:
- Duração total aproximada: 60 segundos de narração.
- Divida em 6 a 8 blocos curtos; cada bloco deve ter 1 a 2 frases.
- Tom: pragmático, gentil, sem promessas exageradas.
- Sem jargões de coaching. Foco em 1 micro-hábito que possa ser feito hoje.
- Saída em JSON com: language, blocks[], onde cada block tem "text".
"""

def _openai_chat(messages, model="gpt-4o-mini"):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY ausente")
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": model, "messages": messages, "temperature": 0.8}
    ).json()
    return resp["choices"][0]["message"]["content"]

def _bedrock_claude(prompt_text, system_text=None):
    region = os.getenv("AWS_REGION", "us-east-1")
    client = boto3.client("bedrock-runtime", region_name=region)
    # Anthropic Messages API payload
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
    # Claude returns [{'type':'text','text': '...'}]
    return out["content"][0]["text"]

def generate_script(theme=DEFAULT_THEME, provider="bedrock"):
    today = datetime.date.today().isoformat()
    if provider == "openai":
        content = _openai_chat(
            [{"role":"system","content": SYSTEM_PT},
             {"role":"user","content": PROMPT_PT.format(theme=f"{theme} {today}")}]
        )
    else:
        content = _bedrock_claude(
            PROMPT_PT.format(theme=f"{theme} {today}"),
            system_text=SYSTEM_PT
        )

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # fallback simples: 7 blocos por quebras de linha
        blocks = [b.strip() for b in content.split("\n") if b.strip()]
        data = {"language": "pt-BR", "blocks": [{"text": t} for t in blocks[:8]]}

    return data  # {"language":"pt-BR","blocks":[{"text":...}, ...]}

def translate_blocks(blocks, target_lang, provider="bedrock"):
    text = "\n".join([b["text"] for b in blocks])
    prompt = f"Traduza mantendo sentido, concisão e naturalidade. Idioma destino: {target_lang}.\n\n{text}"
    if provider == "openai":
        out = _openai_chat(
            [{"role":"system","content":"Traduza preservando concisão e naturalidade."},
             {"role":"user","content": prompt}]
        )
    else:
        out = _bedrock_claude(
            prompt,
            system_text="Traduza preservando concisão e naturalidade."
        )
    out_blocks = [x.strip() for x in out.split("\n") if x.strip()]
    # garante o mesmo número de blocos
    if len(out_blocks) < len(blocks):
        out_blocks += [""] * (len(blocks) - len(out_blocks))
    return [{"text": t} for t in out_blocks[:len(blocks)]]
