# 🤖 AI Twin Toolkit — Fully Offline

Build a personal AI that writes and talks like you, using your own
WhatsApp and email data. **Nothing leaves your computer.**

---

## 📦 Files in This Toolkit

| File | What it does |
|---|---|
| `parse_whatsapp.py` | Extracts YOUR messages from WhatsApp exports |
| `parse_emails.py` | Extracts YOUR sent emails from Gmail export |
| `categorize_messages.py` | Sorts messages into friends / family / school / work |
| `generate_system_prompt.py` | Uses local AI to write a style prompt for each category |

---

## ⚙️ One-Time Setup

### 1. Install Python
Download from https://python.org (3.10 or newer)

### 2. Install Ollama (the local AI engine)
Download from https://ollama.com
Then open a terminal and run:
```
ollama pull llama3.2
```
This downloads a ~2GB model that runs fully offline.

### 3. Install Open WebUI (optional but recommended — gives you a ChatGPT-like UI)
```
pip install open-webui
open-webui serve
```
Then open http://localhost:8080 in your browser.

---

## 🚀 Step-by-Step Guide

### Step 1 — Export your WhatsApp chats
1. Open WhatsApp on your phone
2. Tap any chat → tap the contact/group name at the top
3. Scroll down → **Export Chat** → **Without Media**
4. Send the .txt file to your computer
5. Create a folder called `whatsapp_exports` next to the scripts
6. Put all .txt files inside it

### Step 2 — Export your Gmail
1. Go to https://takeout.google.com (do this once, download to your computer)
2. Deselect everything → select only **Gmail**
3. Download the .zip → extract it → find the `.mbox` file
4. Place `mail.mbox` next to the scripts

### Step 3 — Configure the scripts
Open `parse_whatsapp.py` and set:
```python
YOUR_NAME = "Your Name"   # exactly as it appears in WhatsApp
```

Open `parse_emails.py` and set:
```python
YOUR_EMAIL = "youremail@gmail.com"
```

### Step 4 — Run the scripts in order

```bash
# Extract your WhatsApp messages
python parse_whatsapp.py

# Extract your sent emails
python parse_emails.py

# Sort them into style categories
python categorize_messages.py

# Generate AI system prompts for each style
python generate_system_prompt.py
```

---

## 📁 What Gets Created

```
whatsapp_exports/          ← your raw WhatsApp .txt files (you put these here)
my_whatsapp_messages.txt   ← your extracted WhatsApp messages
my_email_messages.txt      ← your extracted email messages
categorized/
  friends.txt
  family.txt
  school.txt
  work.txt
  other.txt
system_prompts/
  friends_prompt.txt       ← paste this into your AI when talking to friends
  family_prompt.txt
  school_prompt.txt
  work_prompt.txt
```

---

## 💬 Using Your Style Prompts

### In LM Studio (easiest UI):
1. Download LM Studio: https://lmstudio.ai
2. Download a model (search "llama 3.2" inside the app)
3. Go to the Chat tab
4. Paste the contents of e.g. `friends_prompt.txt` into the System Prompt box
5. Start chatting — the AI now sounds like you

### In Ollama (terminal):
```bash
ollama run llama3.2
>>> /set system YOUR PROMPT TEXT HERE
>>> Now reply to this message for me: "hey are you coming tonight?"
```

### In Open WebUI (browser UI):
1. Run: `open-webui serve`
2. Open http://localhost:8080
3. Create a new chat → set the system prompt

---

## 🔒 Privacy Guarantee

- ✅ All scripts run locally — no internet needed after setup
- ✅ Your messages never leave your computer
- ✅ The AI model runs in your own RAM
- ✅ You can even disconnect from WiFi while running everything

---

## 🛠️ Troubleshooting

**"Ollama is not running"**
→ Open a terminal and run: `ollama serve`

**"No messages found for category X"**
→ Run parse_whatsapp.py and parse_emails.py first

**Script runs slowly**
→ Normal on CPU-only. A GPU speeds things up a lot.
→ Or use a smaller model: `ollama pull llama3.2:1b`

**WhatsApp messages not detected**
→ Make sure YOUR_NAME matches EXACTLY how it appears in the chat file
→ Open the .txt file in a text editor and copy your name precisely

---

## 💡 Tips

- More data = better style mimicry. Export as many chats as you can.
- The `friends` category usually gives the most authentic-sounding results.
- You can manually edit the generated system prompts to fine-tune them.
- Try asking the AI: *"How would I respond to: [message]?"*
