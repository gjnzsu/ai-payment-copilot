from __future__ import annotations

import os


def polish_explanation(deterministic_explanation: str) -> tuple[str, str]:
    if not os.getenv("OPENAI_API_KEY"):
        return deterministic_explanation, "Deterministic"

    try:
        from openai import OpenAI
    except ImportError:
        return deterministic_explanation, "Deterministic"

    client = OpenAI()
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        input=(
            "Rewrite this payment operations diagnosis in concise business language. "
            "Keep every fact unchanged and do not add new evidence.\n\n"
            f"{deterministic_explanation}"
        ),
    )
    return response.output_text.strip(), "LLM polished"
