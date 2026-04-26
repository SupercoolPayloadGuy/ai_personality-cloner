"""
parse_whatsapp.py
─────────────────
Extracts ONLY the messages YOU sent from WhatsApp exports.

Supports TWO export formats — set EXPORT_TYPE below:

  "account_data"  ← WhatsApp's full data package (Settings → Account →
                    Request Account Info). Gets ALL your chats at once.
                    You receive a .zip with HTML files inside.

  "chat_export"   ← The per-chat .txt export (open chat → Export Chat).
                    Put all .txt files in the  whatsapp_exports/  folder.

HOW TO USE (account_data):
  1. WhatsApp → Settings → Account → Request Account Info
  2. Wait up to 3 days for the notification
  3. Download and extract the .zip
  4. Find the folder that contains .html chat files
     (usually called "WhatsApp Chat with ..." files)
  5. Set ACCOUNT_DATA_FOLDER to that folder path below
  6. Run:  python parse_whatsapp.py

HOW TO USE (chat_export):
  1. Open any WhatsApp chat → tap name → Export Chat → Without Media
  2. Put all .txt files in a folder called  whatsapp_exports/
  3. Run:  python parse_whatsapp.py
"""

import re
import os
from pathlib import Path
from html.parser import HTMLParser

# ── CONFIG ──────────────────────────────────────────────────────────────────
EXPORT_TYPE = "account_data"        # "account_data"  or  "chat_export"

# For account_data — folder containing the HTML files from the zip
ACCOUNT_DATA_FOLDER = "whatsapp_account_data"

# For chat_export — folder with your per-chat .txt files
CHAT_EXPORT_FOLDER = "whatsapp_exports"

# Your name exactly as it appears in WhatsApp (only needed for chat_export)
YOUR_NAME = "Your Name"

OUTPUT_FILE = "my_whatsapp_messages.txt"
# ────────────────────────────────────────────────────────────────────────────

SKIP_CONTENT = {
    "<Media omitted>", "This message was deleted", "null",
    "audio omitted", "image omitted", "video omitted",
    "sticker omitted", "GIF omitted", "document omitted",
    "Contact card omitted", "missed voice call", "missed video call",
    "voice call", "video call",
}


# ── PARSER: Account Data HTML format ────────────────────────────────────────

class WhatsAppHTMLParser(HTMLParser):
    """
    Parses WhatsApp's account data HTML chat files.

    The HTML structure looks like:
      <div class="message">
        <div class="message-in"> or <div class="message-out">
          <span class="message-text">Hello there</span>
        </div>
      </div>

    "message-out" = messages YOU sent
    "message-in"  = messages received
    """

    def __init__(self):
        super().__init__()
        self.messages = []
        self._in_outgoing = False
        self._in_text = False
        self._current_text = []
        self._depth = 0
        self._outgoing_depth = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        classes = attrs_dict.get("class", "")

        self._depth += 1

        # Detect outgoing message container
        if "message-out" in classes or "outgoing" in classes:
            self._in_outgoing = True
            self._outgoing_depth = self._depth

        # Detect message text span inside outgoing message
        if self._in_outgoing and tag in ("span", "div", "p"):
            if any(c in classes for c in ("message-text", "selectable-text", "_ao3e")):
                self._in_text = True
                self._current_text = []

    def handle_endtag(self, tag):
        if self._in_text and tag in ("span", "div", "p"):
            text = "".join(self._current_text).strip()
            if text and len(text) > 2:
                self.messages.append(text)
            self._in_text = False
            self._current_text = []

        if self._outgoing_depth and self._depth <= self._outgoing_depth:
            self._in_outgoing = False
            self._outgoing_depth = None

        self._depth -= 1

    def handle_data(self, data):
        if self._in_text:
            self._current_text.append(data)


def parse_html_file(filepath: Path) -> list[str]:
    """Parse a single WhatsApp HTML chat file, return your outgoing messages."""
    content = filepath.read_text(encoding="utf-8", errors="replace")

    # Strategy 1: Use the HTML parser for structured files
    parser = WhatsAppHTMLParser()
    parser.feed(content)
    if parser.messages:
        return parser.messages

    # Strategy 2: Fallback — regex scan for common WhatsApp HTML patterns
    # WhatsApp sometimes uses slightly different class names across versions
    messages = []

    # Pattern: text inside outgoing message blocks
    outgoing_blocks = re.findall(
        r'class="[^"]*(?:message-out|outgoing|sent)[^"]*"[^>]*>.*?'
        r'(?:message-text|selectable-text)[^"]*"[^>]*>(.*?)</(?:span|p|div)>',
        content, re.DOTALL | re.IGNORECASE
    )
    for block in outgoing_blocks:
        text = re.sub(r"<[^>]+>", "", block).strip()
        if text and len(text) > 2:
            messages.append(text)

    return messages


def parse_account_data(folder: Path) -> list[str]:
    """Parse all HTML chat files from WhatsApp's account data export."""
    html_files = list(folder.glob("**/*.html"))

    if not html_files:
        print(f"[!] No .html files found in '{folder}'")
        print(f"    Make sure you extracted the .zip and pointed to the right folder.")
        return []

    all_messages = []
    for hf in html_files:
        msgs = parse_html_file(hf)
        # Filter skip content
        msgs = [m for m in msgs if m not in SKIP_CONTENT and len(m) > 2]
        if msgs:
            print(f"  [✓] {hf.name:50s} → {len(msgs):4d} messages")
            all_messages.extend(msgs)
        else:
            print(f"  [~] {hf.name:50s} → (no outgoing messages found)")

    return all_messages


# ── PARSER: Per-chat .txt export format ─────────────────────────────────────

TXT_PATTERNS = [
    re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4},\s[\d:]+\s?[APM]*\s-\s(.+?):\s(.+)$"),
    re.compile(r"^\[\d{1,2}/\d{1,2}/\d{2,4},\s[\d:]+[\s\u202f][APM]*\]\s(.+?):\s(.+)$"),
]

def parse_txt_file(filepath: Path) -> list[str]:
    messages = []
    current_sender = None
    current_text = []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            matched = False
            for pattern in TXT_PATTERNS:
                m = pattern.match(line)
                if m:
                    if current_sender == YOUR_NAME and current_text:
                        messages.append(" ".join(current_text))
                    current_sender = m.group(1).strip()
                    current_text = [m.group(2).strip()]
                    matched = True
                    break
            if not matched and current_sender:
                current_text.append(line.strip())

    if current_sender == YOUR_NAME and current_text:
        messages.append(" ".join(current_text))

    return messages


def parse_chat_exports(folder: Path) -> list[str]:
    txt_files = list(folder.glob("*.txt"))
    if not txt_files:
        print(f"[!] No .txt files found in '{folder}'")
        return []

    all_messages = []
    for f in txt_files:
        msgs = parse_txt_file(f)
        msgs = [m for m in msgs if m not in SKIP_CONTENT and len(m) > 2]
        print(f"  [✓] {f.name:50s} → {len(msgs):4d} messages")
        all_messages.extend(msgs)

    return all_messages


# ── MAIN ────────────────────────────────────────────────────────────────────

def main():
    print(f"── WhatsApp Parser ({EXPORT_TYPE}) ─────────────────────────────")

    if EXPORT_TYPE == "account_data":
        folder = Path(ACCOUNT_DATA_FOLDER)
        if not folder.exists():
            print(f"\n[!] Folder '{ACCOUNT_DATA_FOLDER}' not found.")
            print(f"\n  Steps to get your account data:")
            print(f"  1. WhatsApp → Settings → Account → Request Account Info")
            print(f"  2. Wait up to 3 days for a notification")
            print(f"  3. Download and extract the .zip file")
            print(f"  4. Create a folder called '{ACCOUNT_DATA_FOLDER}' here")
            print(f"  5. Copy the HTML files from the zip into it")
            return
        messages = parse_account_data(folder)

    elif EXPORT_TYPE == "chat_export":
        folder = Path(CHAT_EXPORT_FOLDER)
        if not folder.exists():
            print(f"\n[!] Folder '{CHAT_EXPORT_FOLDER}' not found.")
            print(f"    Create it and put your WhatsApp .txt exports inside.")
            return
        messages = parse_chat_exports(folder)

    else:
        print(f"[!] Unknown EXPORT_TYPE: '{EXPORT_TYPE}'")
        return

    if not messages:
        print("\n[!] No messages extracted.")
        print("    If using account_data: make sure the HTML files are in the folder.")
        print("    If using chat_export: make sure YOUR_NAME matches exactly.")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("\n".join(messages))

    print(f"\n✅ Done! {len(messages)} messages saved to '{OUTPUT_FILE}'")
    print(f"   Run next:  python categorize_messages.py")


if __name__ == "__main__":
    main()
