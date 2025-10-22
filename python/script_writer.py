def build_script(topic:str) -> list[str]:
    """Retorna linhas curtas (para legenda queimada) ~ 60s total."""
    hook = [f"Você viu isso? {topic} explodiu nas buscas!", "Fica até o fim para uma dica."]
    body = [
        "Resumo em 1 minuto:",
        "• O que é e por que importa.",
        "• O que mudou nesta semana.",
        "• Como isso pode te impactar.",
    ]
    tip = ["Dica extra: salve para lembrar e compartilhar.", "Segue a conta para as tendências diárias!"]
    lines = hook + body + tip
    # duplicar para preencher ~60s (ajuste simples)
    while len(lines) < 20:
        lines.append("Acompanhe as próximas tendências!")
    return lines[:22]
