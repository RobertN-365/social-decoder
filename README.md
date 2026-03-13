# The Social Decoder

A Windows desktop app that helps neurodivergent and neurotypical people understand each other's communication styles. Highlight any text, press a hotkey, and get an instant decode of the social subtext and emotional tone.

![Windows](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.12-green)
![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-lightgrey)

## How It Works

1. Highlight any text (email, Slack message, Teams chat, etc.)
2. Press **Ctrl+Shift+D** (configurable)
3. Get an instant popup with:
   - **Neutrality score** (1-10 scale)
   - **Emotional tone** label
   - **What they probably mean** — plain-language explanation
   - **Reassurance** — compassionate reality check
   - **Suggested responses** — ready to copy and use

Right-click any part of the decode to **Clarify** it further or **Copy** the text.

## Two Modes

- **Neurodivergent mode** — Helps ND people (ADHD, Autism) decode neurotypical messages. Addresses rejection sensitivity, explains social conventions, and reframes catastrophic interpretations.
- **Neurotypical mode** — Helps NT people understand neurodivergent communication. Explains directness, info-dumping, literal interpretation, and other ND communication patterns.

Switch between modes anytime in Settings.

## Features

- System tray app — runs quietly in the background
- Global hotkey activation (default: Ctrl+Shift+D)
- Dark and light themes with a gentle, sensory-friendly color palette
- Fade-in/fade-out animations
- Local decode history with search
- Right-click context menu (Copy / Clarify)
- Encrypted API key storage (Windows DPAPI)
- First-run setup wizard

## Quick Start

### Option 1: Download the exe

1. Go to [Releases](../../releases) and download `SocialDecoder.exe`
2. Run it — Windows SmartScreen may warn you; click **More info** > **Run anyway** (or right-click the file > Properties > Unblock)
3. Follow the setup wizard to enter your API key and choose your mode

### Option 2: Run from source

```bash
git clone https://github.com/RobertN-365/social-decoder.git
cd social-decoder
pip install -r requirements.txt
python main.py
```

## Getting a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the key and paste it into the Social Decoder setup wizard

The Gemini API has a generous free tier that should cover typical personal use.

## Building the exe

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name SocialDecoder --add-data "icon.ico;." main.py
```

The exe will be in the `dist/` folder.

## Tech Stack

- Python 3.12 + tkinter
- Google Gemini API (`google-genai` SDK)
- `pystray` for system tray
- `keyboard` for global hotkeys
- `pyperclip` for clipboard access
- Windows DPAPI for encrypted key storage
- PyInstaller for single-file packaging

## Screenshots

*Coming soon — screenshots of the decode popup, settings, and first-run wizard.*

<!-- Add screenshots here:
![Decode popup](screenshots/decode-popup.png)
![Settings](screenshots/settings.png)
![First run](screenshots/first-run.png)
-->
