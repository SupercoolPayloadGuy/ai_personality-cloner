"""
parse_discord.py
────────────────
Reads your Discord data export (.json) and extracts ONLY messages YOU sent,
then saves them to my_discord_messages.txt

HOW TO USE:
  Option A — Official export (all messages):
    1. Discord → User Settings → Privacy & Safety → Request all my Data
    2. Wait up to 30 days for the email download link
    3. Extract the zip → find  messages/index.json  and  messages/ folder
    4. Set DISCORD_EXPORT_TYPE = "official" below
    5. Set DISCORD_MESSAGES_FOLDER to the path of the messages/ folder

  Option B — DiscordChatExporter (faster, specific servers/DMs):
    1. Download: https://github.com/Tyrrrz/DiscordChatExporter
    2. Export chats as JSON
    3. Put all .json files in a folder called "discord_exports"
    4. Set DISCORD_EXPORT_TYPE = "chatexporter" below

  Then run:  python parse_discord.py
"""

import json
import os
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────────────────
DISCORD_EXPORT_TYPE = "chatexporter"   # "official" or "chatexporter"

# For "chatexporter" — folder with your exported .json files
CHATEXPORTER_FOLDER = "discord_exports"

# For "official" — the messages/ folder from Discord's data package
OFFICIAL_MESSAGES_FOLDER = "discord_data/messages"

YOUR_DISCORD_USERNAME = "yourusername"  # ← your Discord username (without #0000)

OUTPUT_FILE = "my_discord_messages.txt"
MIN_LENGTH = 2    # Discord messages can be short ("lol", "yes", "fr")
# ────────────────────────────────────────────────────────────────────────────

SKIP_CONTENT = {
    "", "👍", "👎", "❤️", "😂", "🔥", "💀", "✅", "❌",
}

def clean_message(text: str) -> str:
    """Remove mentions, channel refs, and links."""
    import re
    text = re.sub(r"<@!?\d+>", "@someone", text)      # user mentions
    text = re.sub(r"<#\d+>", "#channel", text)         # channel mentions
    text = re.sub(r"https?://\S+", "[link]", text)     # URLs
    text = re.sub(r"<:\w+:\d+>", "", text)             # custom emojis
    return text.strip()


# ── PARSER: DiscordChatExporter format ──────────────────────────────────────

def parse_chatexporter(folder: Path) -> list[str]:
    messages = []
    json_files = list(folder.glob("*.json"))

    if not json_files:
        print(f"[!] No .json files found in '{folder}'")
        return messages

    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"[!] Could not parse {jf.name} — skipping")
                continue

        msg_list = data.get("messages", [])
        for msg in msg_list:
            author = msg.get("author", {})
            name = author.get("name", "") or author.get("nickname", "")
            if YOUR_DISCORD_USERNAME.lower() not in name.lower():
                continue
            content = msg.get("content", "").strip()
            content = clean_message(content)
            if len(content) >= MIN_LENGTH and content not in SKIP_CONTENT:
                messages.append(content)

        print(f"[✓] {jf.name} → {len(messages)} messages so far")

    return messages


# ── PARSER: Official Discord export format ──────────────────────────────────

def parse_official(folder: Path) -> list[str]:
    """
    Official export structure:
      messages/
        index.json          { "channel_id": "channel name", ... }
        c<channel_id>/
          messages.csv      id, timestamp, contents, attachments
    """
    messages = []

    if not folder.exists():
        print(f"[!] Folder '{folder}' not found.")
        return messages

    import csv

    channel_dirs = [d for d in folder.iterdir() if d.is_dir()]
    print(f"[~] Found {len(channel_dirs)} channel folders")

    for ch_dir in channel_dirs:
        csv_file = ch_dir / "messages.csv"
        if not csv_file.exists():
            continue
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                content = row.get("Contents", "").strip()
                content = clean_message(content)
                if len(content) >= MIN_LENGTH and content not in SKIP_CONTENT:
                    messages.append(content)

    # Official export only contains YOUR messages, so no username filter needed
    print(f"[✓] Extracted {len(messages)} messages from official export")
    return messages


# ── MAIN ────────────────────────────────────────────────────────────────────

def main():
    if DISCORD_EXPORT_TYPE == "chatexporter":
        folder = Path(CHATEXPORTER_FOLDER)
        if not folder.exists():
            print(f"[!] Folder '{CHATEXPORTER_FOLDER}' not found.")
            print(f"    Create it and put your Discord .json exports inside.")
            return
        messages = parse_chatexporter(folder)

    elif DISCORD_EXPORT_TYPE == "official":
        messages = parse_official(Path(OFFICIAL_MESSAGES_FOLDER))

    else:
        print(f"[!] Unknown DISCORD_EXPORT_TYPE: '{DISCORD_EXPORT_TYPE}'")
        return

    if not messages:
        print("[!] No messages extracted. Check your settings above.")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("\n".join(messages))

    print(f"\n✅ Done! {len(messages)} Discord messages saved to '{OUTPUT_FILE}'")
    print(f"   Run next:  python categorize_messages.py")


if __name__ == "__main__":
    main()
