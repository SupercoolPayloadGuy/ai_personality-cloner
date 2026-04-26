"""
categorize_messages.py
──────────────────────
Sorts your exported messages into style categories:

  FIXED RULES (no keyword detection needed):
  • Discord messages   → always FRIENDS
  • WhatsApp messages  → always FRIENDS
  • Email messages     → always SCHOOL

  EXTRA categories (from email content):
  • work   → professional emails (auto-detected)
  • other  → anything else

Outputs one .txt file per category in the  categorized/  folder.

HOW TO USE:
  1. First run any/all of:
       parse_whatsapp.py
       parse_discord.py
       parse_emails.py
  2. Run:  python categorize_messages.py
"""

from pathlib import Path
from collections import defaultdict

# ── CONFIG ──────────────────────────────────────────────────────────────────
OUTPUT_FOLDER = "categorized"

# Source files and their fixed category
FIXED_SOURCES = {
    "my_whatsapp_messages.txt": "friends",
    "my_discord_messages.txt":  "friends",
    "my_email_messages.txt":    "school",   # all emails → school by default
}

# Within emails, these keywords bump a message to "work" instead of "school"
WORK_KEYWORDS = [
    "meeting", "deadline", "client", "invoice", "contract", "manager",
    "colleague", "salary", "budget", "quarterly", "department", "onboarding",
    "promotion", "sprint", "proposal", "hr ", "boss", "office",
]
# ────────────────────────────────────────────────────────────────────────────


def load_messages(filepath: Path) -> list[str]:
    if not filepath.exists():
        return []
    content = filepath.read_text(encoding="utf-8")
    if "\n---\n" in content:
        parts = content.split("\n---\n")
    elif "\n\n" in content:
        parts = content.split("\n\n")
    else:
        parts = content.splitlines()
    return [p.strip() for p in parts if len(p.strip()) > 3]


def classify_email(message: str) -> str:
    """Emails default to 'school', unless they look professional → 'work'."""
    msg_lower = message.lower()
    work_score = sum(1 for kw in WORK_KEYWORDS if kw in msg_lower)
    return "work" if work_score >= 2 else "school"


def main():
    output_path = Path(OUTPUT_FOLDER)
    output_path.mkdir(exist_ok=True)

    buckets: dict[str, list[str]] = defaultdict(list)

    print("── Loading sources ─────────────────────────────────────────────")
    for filename, fixed_category in FIXED_SOURCES.items():
        messages = load_messages(Path(filename))
        if not messages:
            print(f"  [~] '{filename}' not found or empty — skipping")
            continue

        print(f"  [✓] {filename:35s} → {len(messages):4d} messages → '{fixed_category}'")

        for msg in messages:
            if fixed_category == "school":
                category = classify_email(msg)
            else:
                category = fixed_category
            buckets[category].append(msg)

    if not any(buckets.values()):
        print("\n[!] No messages found at all.")
        print("    Run parse_whatsapp.py, parse_discord.py, and/or parse_emails.py first.")
        return

    print("\n── Saving categories ───────────────────────────────────────────")
    for category in ["friends", "school", "work", "other"]:
        msgs = buckets.get(category, [])
        out_file = output_path / f"{category}.txt"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write("\n\n".join(msgs))
        status = f"{len(msgs):4d} messages" if msgs else "  (empty)"
        print(f"  {category:10s} → {status:20s} → {out_file}")

    total = sum(len(v) for v in buckets.values())
    print(f"\n✅ Done! {total} messages sorted into '{OUTPUT_FOLDER}/'")
    print(f"\n── Summary ─────────────────────────────────────────────────────")
    print(f"  friends  = WhatsApp + Discord  (your casual voice)")
    print(f"  school   = Emails              (your formal/academic voice)")
    print(f"  work     = Professional emails (auto-detected)")
    print(f"\n   Next step:  python generate_system_prompt.py")


if __name__ == "__main__":
    main()
