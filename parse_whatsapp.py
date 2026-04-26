"""
parse_whatsapp.py
─────────────────
Reads one or more WhatsApp .txt export files and extracts ONLY the
messages YOU sent, then saves them to my_whatsapp_messages.txt

HOW TO USE:
  1. Export your WhatsApp chats:
       iPhone/Android → open chat → tap name → Export Chat → Without Media
  2. Put all the .txt files in a folder called  "whatsapp_exports"
  3. Set YOUR_NAME below to exactly how your name appears in the chat
  4. Run:  python parse_whatsapp.py
"""

import re
import os
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────────────────
YOUR_NAME = "Your Name"          # ← change this to your name in WhatsApp
EXPORTS_FOLDER = "whatsapp_exports"   # folder with your .txt files
OUTPUT_FILE = "my_whatsapp_messages.txt"
# ────────────────────────────────────────────────────────────────────────────

# WhatsApp line formats (handles different phone/locale formats):
# Android:  "12/31/23, 10:45 PM - Name: message"
# iPhone:   "[31/12/2023, 22:45:00] Name: message"
PATTERNS = [
    re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4},\s[\d:]+\s?[APM]*\s-\s(.+?):\s(.+)$"),
    re.compile(r"^\[\d{1,2}/\d{1,2}/\d{2,4},\s[\d:]+[\s\u202f][APM]*\]\s(.+?):\s(.+)$"),
]

def parse_file(filepath: Path) -> list[str]:
    """Extract messages sent by YOUR_NAME from a single export file."""
    messages = []
    current_sender = None
    current_text = []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            matched = False
            for pattern in PATTERNS:
                m = pattern.match(line)
                if m:
                    # Save previous message if it was yours
                    if current_sender == YOUR_NAME and current_text:
                        messages.append(" ".join(current_text))
                    current_sender = m.group(1).strip()
                    current_text = [m.group(2).strip()]
                    matched = True
                    break

            if not matched and current_sender:
                # Continuation of a multi-line message
                current_text.append(line.strip())

    # Don't forget the last message
    if current_sender == YOUR_NAME and current_text:
        messages.append(" ".join(current_text))

    return messages


def main():
    exports_path = Path(EXPORTS_FOLDER)
    if not exports_path.exists():
        print(f"[!] Folder '{EXPORTS_FOLDER}' not found.")
        print(f"    Create it and put your WhatsApp .txt exports inside.")
        return

    txt_files = list(exports_path.glob("*.txt"))
    if not txt_files:
        print(f"[!] No .txt files found in '{EXPORTS_FOLDER}'")
        return

    all_messages = []
    for f in txt_files:
        msgs = parse_file(f)
        print(f"[✓] {f.name} → {len(msgs)} messages from you")
        all_messages.extend(msgs)

    # Filter out system messages and very short noise
    all_messages = [m for m in all_messages if len(m) > 3 and
                    m not in ("<Media omitted>", "This message was deleted",
                              "null", "audio omitted", "image omitted",
                              "video omitted", "sticker omitted", "GIF omitted")]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("\n".join(all_messages))

    print(f"\n✅ Done! {len(all_messages)} messages saved to '{OUTPUT_FILE}'")
    print(f"   You can now run:  python categorize_messages.py")


if __name__ == "__main__":
    main()
