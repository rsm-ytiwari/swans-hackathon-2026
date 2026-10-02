"""Provider check: is each runtime LLM reachable, does it return valid JSON, and how fast?

Usage: uv run python scripts/check_providers.py [ollama gemini anthropic]
Skips any provider whose key or server isn't configured. Pre-event tooling, not product code.
"""

import json
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

PROMPT = (
    "Classify this law-firm intake message. Reply with JSON only: "
    '{"category": "new_lead" | "existing_client_status" | "medical_update" | "other", '
    '"urgent": true | false}\n\n'
    'Message: "Hi, I was rear-ended last Tuesday and my neck still hurts. The ER said to see a '
    'specialist but I missed my appointment. Is that a problem for my case?"'
)
EXPECTED = {"category": "medical_update", "urgent": True}


def openai_compatible(base_url: str, api_key: str, model: str) -> str:
    from openai import OpenAI

    client = OpenAI(base_url=base_url, api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": PROMPT}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return resp.choices[0].message.content


def anthropic_call(model: str) -> str:
    import anthropic

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model, max_tokens=200, messages=[{"role": "user", "content": PROMPT}]
    )
    return resp.content[0].text


PROVIDERS = {
    "ollama": lambda: openai_compatible(
        "http://localhost:11434/v1", "ollama", os.getenv("OLLAMA_MODEL", "gemma4:26b")
    ),
    "gemini": lambda: openai_compatible(
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        os.environ["GEMINI_API_KEY"],
        os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    ),
    "anthropic": lambda: anthropic_call(os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")),
}
REQUIRED_ENV = {"gemini": "GEMINI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}


def parse_json(text: str) -> dict:
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    return json.loads(text)


def main() -> None:
    names = sys.argv[1:] or list(PROVIDERS)
    for name in names:
        env = REQUIRED_ENV.get(name)
        if env and not os.getenv(env):
            print(f"[skip] {name}: {env} not set in .env")
            continue
        start = time.perf_counter()
        try:
            raw = PROVIDERS[name]()
            secs = time.perf_counter() - start
            out = parse_json(raw)
            verdict = "correct" if out == EXPECTED else f"differs from expected {EXPECTED}"
            print(f"[ok]   {name}: {secs:.1f}s · {out} · {verdict}")
        except Exception as e:  # report every failure mode, keep checking the others
            print(f"[fail] {name}: {type(e).__name__}: {str(e)[:200]}")


if __name__ == "__main__":
    main()
