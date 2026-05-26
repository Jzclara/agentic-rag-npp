def format_history(history: list[dict[str, str]], max_turns: int = 4) -> str:
    recent_history = history[-max_turns * 2 :]

    if not recent_history:
        return "No previous conversation."

    lines = []
    for item in recent_history:
        role = item.get("role", "unknown")
        content = item.get("content", item.get("text", ""))
        lines.append(f"{role}: {content}")

    return "\n".join(lines)
