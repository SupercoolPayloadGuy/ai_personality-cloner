"""
generate_system_prompt.py
─────────────────────────
Analyzes your categorized messages using a LOCAL AI model (via Ollama)
and generates a custom system prompt for each writing style.

100% OFFLINE — nothing leaves your computer.

REQUIREMENTS:
  1. Install Ollama:  https://ollama.com
  2. Pull a model:    ollama pull llama3.2
  3. Run Ollama:      ollama serve   (or it starts automatically)
  4. Run this script: python generate_system_prompt.py

OUTPUT:
  system_prompts/friends_prompt.txt
  system_prompts/family_prompt.txt
  system_prompts/school_prompt.txt
  system_prompts/work_prompt.txt
"""

import json
import urllib.request
import urllib.error
from pathlib import Path
from textwrap import shorten

# ── CONFIG ──────────────────────────────────────────────────────────────────
OLLAMA_URL    = "http://localhost:11434/api/generate"
MODEL         = "llama3.2"          # change to any model you have pulled
INPUT_FOLDER  = "categorized"
OUTPUT_FOLDER = "system_prompts"
SAMPLE_SIZE   = 60                  # number of messages to send to the model
# ────────────────────────────────────────────────────────────────────────────

ANALYSIS_PROMPT = """You are a writing style analyst. Below are real messages written by a person in a '{category}' context.

Analyze their writing style carefully — tone, vocabulary, sentence length, punctuation habits, use of slang or formality, emotional expression, how they start/end messages, recurring phrases, and anything unique.

Then write a system prompt (2–4 paragraphs) that would make an AI assistant write EXACTLY like this person in a {category} context. Be specific. Include example phrases, patterns, and quirks you notice. Do NOT include any of the original messages in your output.

MESSAGES:
{messages}

Write the system prompt now:"""


def call_ollama(prompt: str) -> str:
    """Send a prompt to local Ollama and return the response."""
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result.get("response", "").strip()


def check_ollama() -> bool:
    """Check if Ollama is running."""
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=3)
        return True
    except Exception:
        return False


def load_messages(filepath: Path) -> list[str]:
    if not filepath.exists():
        return []
    content = filepath.read_text(encoding="utf-8")
    parts = content.split("\n\n")
    return [p.strip() for p in parts if len(p.strip()) > 10]


def main():
    if not check_ollama():
        print("╔══════════════════════════════════════════════════════╗")
        print("║  Ollama is not running!                              ║")
        print("║                                                      ║")
        print("║  1. Install it:  https://ollama.com                  ║")
        print("║  2. Pull model:  ollama pull llama3.2                ║")
        print("║  3. It starts automatically, then re-run this script ║")
        print("╚══════════════════════════════════════════════════════╝")
        return

    input_path  = Path(INPUT_FOLDER)
    output_path = Path(OUTPUT_FOLDER)
    output_path.mkdir(exist_ok=True)

    categories = ["friends", "family", "school", "work"]

    for category in categories:
        msg_file = input_path / f"{category}.txt"
        messages = load_messages(msg_file)

        if not messages:
            print(f"[~] No messages for '{category}' — skipping")
            continue

        # Use a sample to keep the prompt manageable
        sample = messages[:SAMPLE_SIZE]
        combined = "\n\n".join(sample)

        # Trim if too long (~12000 chars max)
        if len(combined) > 12000:
            combined = combined[:12000] + "\n[... trimmed ...]"

        prompt = ANALYSIS_PROMPT.format(
            category=category,
            messages=combined,
        )

        print(f"[~] Analyzing '{category}' style ({len(sample)} messages)...", flush=True)

        try:
            result = call_ollama(prompt)
            out_file = output_path / f"{category}_prompt.txt"
            out_file.write_text(result, encoding="utf-8")
            preview = shorten(result, width=80, placeholder="...")
            print(f"[✓] {category:10s} → saved to {out_file}")
            print(f"    Preview: {preview}\n")
        except Exception as e:
            print(f"[!] Error on '{category}': {e}")

    print(f"\n✅ Done! System prompts saved to '{OUTPUT_FOLDER}/'")
    print()
    print("── HOW TO USE YOUR SYSTEM PROMPTS ─────────────────────────────")
    print("  In LM Studio or Open WebUI:")
    print("  1. Open the System Prompt field")
    print("  2. Paste the content of e.g. friends_prompt.txt")
    print("  3. Chat — the AI will respond in your style")
    print()
    print("  In Ollama directly:")
    print("  $ ollama run llama3.2")
    print("  >>> /set system <paste your prompt here>")
    print("────────────────────────────────────────────────────────────────")


if __name__ == "__main__":
    main()
