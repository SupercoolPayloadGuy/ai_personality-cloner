"""
parse_emails.py
───────────────
Reads your Gmail export (.mbox file from Google Takeout) and extracts
ONLY emails YOU sent, saved to my_email_messages.txt

HOW TO USE:
  1. Go to https://takeout.google.com  (offline: download first, then run)
  2. Select only Gmail → download the .mbox file
  3. Put the .mbox file in the same folder as this script
  4. Set YOUR_EMAIL below
  5. Run:  python parse_emails.py
"""

import mailbox
import email
import quopri
import base64
import re
import os
from pathlib import Path
from html.parser import HTMLParser

# ── CONFIG ──────────────────────────────────────────────────────────────────
YOUR_EMAIL = "youremail@gmail.com"   # ← change this
MBOX_FILE  = "mail.mbox"             # ← name of your exported file
OUTPUT_FILE = "my_email_messages.txt"
MIN_LENGTH = 30                       # ignore very short replies/auto-responses
MAX_LENGTH = 3000                     # ignore huge forwarded threads
# ────────────────────────────────────────────────────────────────────────────


class HTMLStripper(HTMLParser):
    """Simple HTML → plain text."""
    def __init__(self):
        super().__init__()
        self.text = []
    def handle_data(self, data):
        self.text.append(data)
    def get_text(self):
        return " ".join(self.text)


def strip_html(html: str) -> str:
    s = HTMLStripper()
    s.feed(html)
    return s.get_text()


def decode_payload(part) -> str:
    """Safely decode a message part to a string."""
    payload = part.get_payload(decode=True)
    if not payload:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except Exception:
        return payload.decode("utf-8", errors="replace")


def extract_body(msg) -> str:
    """Pull plain text body from an email message."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain":
                body = decode_payload(part)
                break
            elif ct == "text/html" and not body:
                body = strip_html(decode_payload(part))
    else:
        ct = msg.get_content_type()
        body = decode_payload(msg)
        if ct == "text/html":
            body = strip_html(body)
    return body


def clean_body(text: str) -> str:
    """Remove quoted reply chains, signatures, and noise."""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Stop at quoted reply markers
        if stripped.startswith(">"):
            break
        if re.match(r"^On .+ wrote:$", stripped):
            break
        if stripped.startswith("--"):   # signature separator
            break
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def sender_matches(from_header: str) -> bool:
    """Check if the sender is you."""
    if not from_header:
        return False
    return YOUR_EMAIL.lower() in from_header.lower()


def main():
    mbox_path = Path(MBOX_FILE)
    if not mbox_path.exists():
        print(f"[!] File '{MBOX_FILE}' not found.")
        print(f"    Download your Gmail via Google Takeout and place it here.")
        return

    print(f"[~] Opening {MBOX_FILE} — this may take a minute for large mailboxes...")
    mbox = mailbox.mbox(str(mbox_path))

    messages = []
    total = 0
    for key, msg in mbox.items():
        total += 1
        from_header = msg.get("From", "")
        if not sender_matches(from_header):
            continue

        body = extract_body(msg)
        body = clean_body(body)

        if MIN_LENGTH <= len(body) <= MAX_LENGTH:
            messages.append(body)

    print(f"[✓] Scanned {total} emails, kept {len(messages)} sent by you")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("\n\n---\n\n".join(messages))

    print(f"\n✅ Done! Saved to '{OUTPUT_FILE}'")
    print(f"   You can now run:  python categorize_messages.py")


if __name__ == "__main__":
    main()
