# 🤖 J.A.R.V.I.S — Mark VII (Aditya's Personal AI Assistant)

Iron Man Inspired Voice Assistant with a Holographic Arc Reactor HUD UI, PC Automation, and Google Gemini AI Brain.

---

## 🚀 How to Run J.A.R.V.I.S (कैसे चलाएं)

### 1. बस एक क्लिक में चलाएं:
* फोल्डर में मौजूद **`run_jarvis.bat`** फाइल पर डबल-क्लिक (Double Click) करें!
* आपके सामने Iron Man स्टाइल का **Futuristic Arc Reactor HUD** ऐप खुल जाएगा।
* JARVIS तुरंत आपको ग्रीट करेगा:  
  🗣️ *"Hello Sir, how are you? and how can I help you?"*

---

## ⚡ PC Auto-Start (कंप्यूटर चालू होते ही JARVIS खुद शुरू होगा)
यह फीचर **पहले से ही चालू (Enabled) कर दिया गया है!**  
अब जब भी आप अपना PC ऑन या रीस्टार्ट करेंगे, JARVIS बैकग्राउंड में स्टार्ट होकर आपको अपनी आवाज़ में ग्रीट करेगा और कमांड्स के लिए तैयार रहेगा।

* यदि कभी इसे बंद करना हो, तो टर्मिनल में चलाएं:  
  `python setup_startup.py disable`
* दोबारा चालू करने के लिए:  
  `python setup_startup.py`

---

## 🎙️ Commands You Can Speak or Type (आप क्या बोल सकते हैं)

### 1. ऐप्स और सॉफ्टवेयर खोलना:
* *"Jarvis, open Chrome"* (या Google Chrome)
* *"Jarvis, open Notepad"*
* *"Jarvis, open Calculator"*
* *"Jarvis, open VS Code"*
* *"Jarvis, open Task Manager"*
* *"Jarvis, open Settings"*
* *"Jarvis, open Command Prompt"*

### 2. YouTube और Google:
* *"Jarvis, play Faded on YouTube"*
* *"Jarvis, play Iron Man theme song"*
* *"Jarvis, search Google for Python tutorials"*
* *"Jarvis, open Instagram"* / *"open WhatsApp"* / *"open GitHub"*

### 3. PC कंट्रोल:
* *"Jarvis, volume up"* / *"volume down"* / *"mute"*
* *"Jarvis, take screenshot"* (स्क्रीनशॉट `screenshots` फोल्डर में सेव हो जाएगा)
* *"Jarvis, lock PC"* (कंप्यूटर स्क्रीन लॉक हो जाएगी)

### 4. सिस्टम जानकारी:
* *"Jarvis, what time is it?"*
* *"Jarvis, what is the date?"*
* *"Jarvis, system status"* (CPU, RAM और बैटरी की स्थिति बताएगा)

### 5. सामान्य बातचीत और AI प्रश्न:
* *"Jarvis, who are you?"*
* *"Jarvis, how are you?"*
* *"Jarvis, who is Elon Musk?"*
* *"Jarvis, tell me about Black Hole"*

---

## 🧠 Super AI Brain (Google Gemini API Key जोड़ना)
JARVIS बिना API Key के भी ऐप्स खोल सकता है, गाने चला सकता है और Wikipedia से जानकारी दे सकता है।  
अगर आप चाहते हैं कि यह दुनिया के किसी भी कठिन सवाल का समझदारी से जवाब दे (जैसे ChatGPT/Gemini):

1. [Google AI Studio](https://aistudio.google.com/app/apikey) पर जाएं और अपना फ्री API Key कॉपी करें।
2. **`config.py`** फाइल खोलें।
3. `GEMINI_API_KEY = ""` के अंदर अपना Key पेस्ट कर दें:
   ```python
   GEMINI_API_KEY = "AIzaSy..."
   ```
4. फाइल सेव करें। अब JARVIS का पूरा AI दिमाग एक्टिव हो जाएगा!

---

## 🎨 Futuristic HUD UI की खासियतें:
* **Glowing Arc Reactor:** बीच में घूमता हुआ नियॉन आर्क रिएक्टर जो JARVIS के बोलने पर पल्स करता है।
* **Audio Waveform:** जब आप बोलते हैं या JARVIS जवाब देता है, तो स्क्रीन पर साउंड वेव तरंगे लहराती हैं।
* **Live Transcript Feed:** जो आप बोलते हैं और JARVIS जो जवाब देता है, वह सब स्क्रीन पर लाइव दिखता है।
* **Directives & Quick Buttons:** अगर कभी माइक का इस्तेमाल न करना हो, तो आप स्क्रीन पर टाइप भी कर सकते हैं या बटन्स क्लिक कर सकते हैं।
