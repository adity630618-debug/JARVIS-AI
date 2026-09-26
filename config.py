import os

# ==========================================
# J.A.R.V.I.S Configuration File
# ==========================================

# Personal Details
USER_NAME = "Aditya"
ASSISTANT_NAME = "JARVIS"

# Google Gemini API Key
# You can get a free key from https://aistudio.google.com/app/apikey
# Paste it between the quotes below:
GEMINI_API_KEY = "AQ.Ab8RN6JnGzW3TcI_ODLzrwPiXDpsqrVl5VWBh9yMaKKMpROb7g"

# Voice Engine Settings
VOICE_RATE = 175        # Speed of speech (words per minute, 150-200 is ideal)
VOICE_VOLUME = 1.0      # Volume (0.0 to 1.0)
PREFERRED_VOICE = "Ravi"  # Options: "Ravi" (Male - Indian accent), "Heera" (Female - Indian), "David" (US Male)

# Network & Server Settings
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 7890

# Predefined App Shortcuts (Windows commands or paths)
APP_SHORTCUTS = {
    "chrome": "start chrome",
    "google chrome": "start chrome",
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "command prompt": "start cmd",
    "terminal": "start cmd",
    "file explorer": "explorer",
    "my computer": "explorer",
    "task manager": "taskmgr",
    "vs code": "code",
    "visual studio code": "code",
    "settings": "start ms-settings:",
    "paint": "mspaint",
    "wordpad": "write",
}

# Predefined Website Shortcuts
WEBSITE_SHORTCUTS = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://www.github.com",
    "instagram": "https://www.instagram.com",
    "whatsapp": "https://web.whatsapp.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://twitter.com",
    "chatgpt": "https://chat.openai.com",
    "gmail": "https://mail.google.com",
}
