"""
categorize_messages.py
──────────────────────
Takes your extracted messages and splits them into style categories:
  • friends  → casual, slang, informal
  • family   → warm, personal, caring
  • school   → academic, structured, formal
  • work     → professional, business-like
  • other    → everything else

Outputs one .txt file per category, ready for system prompt generation.

HOW TO USE:
  1. First run parse_whatsapp.py and/or parse_emails.py
  2. Run:  python categorize_messages.py
"""

import re
from pathlib import Path
from collections import defaultdict

# ── CONFIG ──────────────────────────────────────────────────────────────────
INPUT_FILES = [
    "my_whatsapp_messages.txt",
    "my_email_messages.txt",
]
OUTPUT_FOLDER = "categorized"
# ────────────────────────────────────────────────────────────────────────────

# Keywords used to auto-detect the style/context of each message
CATEGORY_KEYWORDS = {
    "school": [
        "homework", "assignment", "professor", "teacher", "exam", "test",
        "class", "lecture", "grade", "campus", "semester", "thesis",
        "research", "study", "university", "college", "school", "course",
        "deadline", "project", "presentation", "student", "tutor", "essay",
        "notes", ".edu", "syllabus", "quiz", "midterm", "final",
    ],
    "work": [
        "meeting", "deadline", "client", "project", "manager", "boss",
        "colleague", "office", "report", "invoice", "contract", "hr",
        "salary", "job", "interview", "team", "sprint", "slack", "zoom",
        "call", "email", "proposal", "budget", "department", "company",
        "quarterly", "kpi", "onboarding", "promotion",
    ],
    "family": [
        "mom", "dad", "mum", "papa", "mama", "brother", "sister", "bro",
        "sis", "grandma", "grandpa", "aunt", "uncle", "cousin", "family",
        "home", "house", "dinner", "sunday", "christmas", "birthday",
        "holiday", "visit", "coming over", "love you", "miss you",
        "thanksgiving", "easter", "parents",
    ],
    "friends": [
        "lol", "lmao", "haha", "bro", "dude", "ngl", "tbh", "omg",
        "wtf", "fr", "imo", "gonna", "wanna", "u ", " u ", "ur ",
        "party", "hang", "netflix", "game", "tonight", "weekend",
        "drink", "bar", "club", "memes", "vibe", "lowkey", "highkey",
        "slay", "bestie", "bff",
    ],
}


def classify(message: str) -> str:
    """Return the best-matching category for a message."""
    msg_lower = message.lower()
    scores = defaultdict(int)

    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in msg_lower:
                scores[category] += 1

    if not scores:
        return "other"

    best = max(scores, key=scores.get)
    # Only assign if there's a clear signal
    if scores[best] >= 1:
        return best
    return "other"


def load_messages(filepath: Path) -> list[str]:
    """Load messages from a file, split by line or separator."""
    if not filepath.exists():
        return []
    content = filepath.read_text(encoding="utf-8")
    # Email files use "---" as separator; WhatsApp files use newlines
    if "---" in content:
        parts = content.split("\n---\n")
    else:
        parts = content.splitlines()
    return [p.strip() for p in parts if p.strip()]


def main():
    output_path = Path(OUTPUT_FOLDER)
    output_path.mkdir(exist_ok=True)

    all_messages = []
    for filename in INPUT_FILES:
        msgs = load_messages(Path(filename))
        if msgs:
            print(f"[✓] Loaded {len(msgs)} messages from '{filename}'")
            all_messages.extend(msgs)
        else:
            print(f"[~] '{filename}' not found or empty — skipping")

    if not all_messages:
        print("\n[!] No messages found. Run parse_whatsapp.py and/or parse_emails.py first.")
        return

    # Categorize
    buckets = defaultdict(list)
    for msg in all_messages:
        category = classify(msg)
        buckets[category].append(msg)

    # Save each category
    print("\n── Results ─────────────────────────────────")
    for category in ["friends", "family", "school", "work", "other"]:
        msgs = buckets[category]
        out_file = output_path / f"{category}.txt"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write("\n\n".join(msgs))
        print(f"  {category:10s} → {len(msgs):4d} messages  →  {out_file}")

    total = sum(len(v) for v in buckets.values())
    print(f"\n✅ Done! {total} messages categorized into '{OUTPUT_FOLDER}/'")
    print(f"   Next step:  python generate_system_prompt.py")


if __name__ == "__main__":
    main()
