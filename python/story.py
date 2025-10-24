from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class StoryBeat:
    title: str
    text: str

def build_story(topic: str) -> List[StoryBeat]:
    """Gera uma história curta em 6 atos a partir do tema.
    Regra: linguagem simples, frases curtas (7–14 palavras), ritmo para shorts.
    """
    topic_clean = topic.strip().rstrip('.')
    beats = [
        ("Hook", f"{topic_clean}: você já pensou no impacto real disso hoje?"),
        ("Contexto", f"Em 10 segundos, te mostro o essencial sobre {topic_clean}."),
        ("Conflito", f"O problema: muita gente erra porque ignora um detalhe-chave."),
        ("Virada", f"A sacada: um passo simples muda tudo quando você aplica agora."),
        ("Payoff", f"Resultado: clareza, menos desperdício e ganho imediato em {topic_clean}."),
        ("CTA", f"Curtiu? Salve e compartilhe para lembrar de {topic_clean} depois."),
    ]
    return [StoryBeat(title=t[0], text=t[1]) for t in beats]

def story_lines(topic: str) -> List[str]:
    return [b.text for b in build_story(topic)]
