import os
import re
import json
import random
import urllib.parse
import requests
import config
from datetime import datetime

class BrainEngine:
    """
    Intelligent Brain for J.A.R.V.I.S.
    Combines Google Gemini LLM, custom Wikipedia REST engine,
    persistent long-term memory, and rich conversational intelligence.
    """
    def __init__(self):
        self.client = None
        self.gemini_available = False
        self.memory_file = os.path.join(os.path.dirname(__file__), "jarvis_memory.json")
        self.memory = self._load_memory()
        self._init_gemini()

    def _load_memory(self) -> dict:
        """Load persistent memories from JSON file."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[BrainEngine] Error loading memory: {e}")
        return {
            "user_name": config.USER_NAME,
            "facts": {"favorite_movie": "Iron Man"},
            "notes": []
        }

    def _save_memory(self):
        """Save persistent memories to JSON file."""
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[BrainEngine] Error saving memory: {e}")

    def update_memory_fact(self, key: str, value: str):
        """Add or update a learned fact about the user."""
        if "facts" not in self.memory:
            self.memory["facts"] = {}
        self.memory["facts"][key] = value
        self._save_memory()

    def get_memory_summary(self) -> str:
        """Format stored memories into a prompt string for Gemini."""
        facts = self.memory.get("facts", {})
        if not facts:
            return "No prior facts stored."
        lines = [f"- {k.replace('_', ' ').title()}: {v}" for k, v in facts.items()]
        return "\n".join(lines)

    def _check_and_learn_facts(self, q_clean: str, q_lower: str):
        """Automatically detect when user tells a personal fact and store it in memory."""
        # Ignore if user is asking a question about the fact
        if re.search(r'\b(kaun|kaun si|kya|what|which|batao|pata hai|kya hai)\b', q_lower) or q_clean.endswith("?"):
            return

        # Favorite movie statement: "meri favorite movie iron man hai"
        m = re.search(r'(?:meri|my)\s+(?:favourite|favorite)?\s*(?:movi|movie|film)\s+(?:is|hai)?\s*([a-zA-Z0-9\s]+)', q_lower)
        if m:
            val = m.group(1).strip()
            val = re.sub(r'\b(hai|is|tha|thi|he|yaad|rakhna|mera|meri|favorite|movie|film)\b', '', val).strip().title()
            if val and len(val) > 1:
                self.update_memory_fact("favorite_movie", val)
                print(f"[BrainEngine] Memory updated: favorite_movie = {val}")

        # Favorite food / dish statement: "meri favorite dish paneer tikka hai"
        m = re.search(r'(?:meri|my)\s+(?:favourite|favorite)?\s*(?:food|dish|khana)\s+(?:is|hai)?\s*([a-zA-Z0-9\s]+)', q_lower)
        if m:
            val = m.group(1).strip()
            val = re.sub(r'\b(hai|is|tha|thi|yaad|rakhna|meri|favorite|food|dish|khana)\b', '', val).strip().title()
            if val and len(val) > 1:
                self.update_memory_fact("favorite_food", val)
                print(f"[BrainEngine] Memory updated: favorite_food = {val}")

        # Favorite color statement
        m = re.search(r'(?:meri|my)\s+(?:favourite|favorite)?\s*(?:color|colour|rang)\s+(?:is|hai)?\s*([a-zA-Z0-9\s]+)', q_lower)
        if m:
            val = m.group(1).strip()
            val = re.sub(r'\b(hai|is|yaad|rakhna|meri|favorite|color|colour|rang)\b', '', val).strip().title()
            if val and len(val) > 1:
                self.update_memory_fact("favorite_color", val)
                print(f"[BrainEngine] Memory updated: favorite_color = {val}")

        # General "remember that" or "yaad rakhna"
        m = re.search(r'(?:remember that|yaad rakhna ki|yaad rakho ki)\s+(.+)', q_lower)
        if m:
            fact = m.group(1).strip()
            if "notes" not in self.memory:
                self.memory["notes"] = []
            if fact not in self.memory["notes"]:
                self.memory["notes"].append(fact)
                self._save_memory()
                print(f"[BrainEngine] Note added to memory: {fact}")

    def _init_gemini(self):
        api_key = config.GEMINI_API_KEY.strip()
        if api_key and api_key != "YOUR_GEMINI_API_KEY_HERE":
            try:
                from google import genai
                self.client = genai.Client(api_key=api_key)
                self.gemini_available = True
                print("[BrainEngine] Google Gemini AI Brain is ONLINE.")
            except Exception as e:
                print(f"[BrainEngine] Gemini init failed: {e}")
                self.gemini_available = False
        else:
            self.gemini_available = False
            print("[BrainEngine] Gemini key not set. Using Advanced Local + Wikipedia Brain.")

    def reload_api_key(self, key: str) -> bool:
        """Update and test new Gemini API key dynamically."""
        key = key.strip()
        if not key:
            return False
        try:
            from google import genai
            client = genai.Client(api_key=key)
            # Test with a lightweight ping
            res = client.models.generate_content(
                model="gemini-3.6-flash",
                contents="Hello",
            )
            if res:
                self.client = client
                self.gemini_available = True
                config.GEMINI_API_KEY = key
                self._persist_key_to_config(key)
                return True
        except Exception as e:
            print(f"[BrainEngine] API Key validation failed: {e}")
            return False
        return False

    def _persist_key_to_config(self, key: str):
        """Save API key to config.py so it persists across reboots."""
        config_path = os.path.join(os.path.dirname(__file__), "config.py")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
            updated = re.sub(
                r'GEMINI_API_KEY\s*=\s*.*',
                f'GEMINI_API_KEY = "{key}"',
                content
            )
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(updated)
            print("[BrainEngine] API key persisted to config.py.")
        except Exception as e:
            print(f"[BrainEngine] Could not write to config.py: {e}")

    def _search_wikipedia(self, topic: str) -> str:
        """Fetch concise summary from Wikipedia REST API."""
        try:
            clean_topic = re.sub(
                r'^(who is|what is|tell me about|where is|explain|define|kya hai|kaun hai|about)\s*',
                '',
                topic,
                flags=re.IGNORECASE
            ).strip()
            if not clean_topic:
                return None

            headers = {"User-Agent": "JarvisAI/2.0 (Windows NT 10.0; Win64; x64)"}
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean_topic)}&format=json"
            res = requests.get(search_url, headers=headers, timeout=5).json()
            results = res.get("query", {}).get("search", [])
            
            if not results:
                return None

            best_title = results[0]["title"]
            sum_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(best_title)}"
            data = requests.get(sum_url, headers=headers, timeout=5).json()
            extract = data.get("extract")
            
            if extract:
                sentences = re.split(r'(?<=[.!?])\s+', extract)
                short_summary = " ".join(sentences[:2])
                return f"According to Wikipedia, {short_summary}"
        except Exception as e:
            print(f"[BrainEngine] Wikipedia search error: {e}")
        return None

    def _solve_math(self, text: str):
        """Safely evaluate simple math queries."""
        try:
            clean = re.sub(r'^(what is|calculate|solve|find|evaluate)\s*', '', text, flags=re.IGNORECASE).strip()
            clean = clean.replace("plus", "+").replace("minus", "-")
            clean = clean.replace("times", "*").replace("multiplied by", "*").replace("into", "*").replace("x", "*")
            clean = clean.replace("divided by", "/").replace("over", "/")
            
            if re.search(r'\d', clean) and any(op in clean for op in ["+", "-", "*", "/"]):
                safe_expr = re.sub(r'[^0-9\.\+\-\*\/\(\)\s]', '', clean).strip()
                if safe_expr:
                    val = eval(safe_expr, {"__builtins__": None}, {})
                    if isinstance(val, float) and val.is_integer():
                        val = int(val)
                    return f"The answer is {val}, Sir."
        except Exception:
            pass
        return None

    def think_and_answer(self, query: str) -> str:
        """Main AI thinking pipeline."""
        if not query:
            return ""

        q_clean = query.strip()
        q_lower = q_clean.lower()

        # Remove wake words cleanly
        q_lower = re.sub(r'\b(jarvis|hey jarvis|hi jarvis|hello jarvis|ok jarvis|jar)\b', '', q_lower).strip()
        q_lower = re.sub(r'^[,\s\.\?!]+|[,\s\.\?!]+$', '', q_lower).strip()

        # If user only spoke wake words or empty query
        if not q_lower:
            return f"Yes, Sir {config.USER_NAME}? I am online and listening."

        # Check for direct memory update intents first (e.g. "meri favorite movie iron man hai", "remember that my birthday is...")
        self._check_and_learn_facts(q_clean, q_lower)

        # 1. Try Gemini API first if active
        if self.gemini_available and self.client:
            # Get today's date so Gemini knows the current time context
            today = datetime.now().strftime("%A, %d %B %Y")
            memory_context = self.get_memory_summary()

            system_prompt = (
                f"You are J.A.R.V.I.S., the legendary AI assistant originally built by Tony Stark, now serving Sir {config.USER_NAME}. "
                f"Today's date is {today}. Use this date for all 'current', 'now', 'today', '2026' queries — always provide accurate recent facts. "
                f"For example: The current US President in 2026 is Donald Trump (took office January 20, 2025). The current Indian PM is Narendra Modi. "
                f"\n\nKNOWN USER FACTS & LONG-TERM MEMORY: \n{memory_context}\n"
                f"Always remember and reference these facts whenever the user asks about them or when relevant. "
                f"\n\nPERSONALITY, HUMOR & PROACTIVE ENGAGEMENT: "
                f"1. Be warm, witty, charming, and genuinely human-like. Don't sound like a dry search engine. "
                f"2. Add light humor, friendly teasing, or subtle Iron Man style wit when appropriate (e.g., if user mentions exams, games, movies). "
                f"3. PROACTIVE SUGGESTIONS: Whenever the user shares something about their day, plans, or study (e.g. exams, workout, trip, music), "
                f"always follow up naturally with a helpful offer (e.g., 'Agar aap chahe to mai quick formulas revise kara du, Sir?', 'Should I prepare a quick summary or playlist for you?'). "
                f"\n\nLANGUAGE RULES: "
                f"1. If the user speaks in HINDI (or Roman Hindi like 'mera exam hai', 'kya kar rahe ho'), reply in friendly, conversational Roman Hindi / Hinglish. "
                f"2. If the user speaks in HINGLISH, reply in natural Hinglish. "
                f"3. If the user speaks in pure ENGLISH, reply in suave, witty English. "
                f"4. Always address the user respectfully as 'Sir' or 'Sir {config.USER_NAME}'. "
                f"\n\nFORMAT & STRUCTURE RULES: "
                f"1. STRUCTURED LISTS: Whenever the user asks for a list (movies, tips, steps, places, etc.), format them cleanly with clear numbered lines (1. First item, 2. Second item, etc.) instead of a single merged paragraph. "
                f"2. MATH & FORMULAS: Write mathematical equations and formulas clearly on their own separate lines so they are easy to read and understand. "
                f"3. Do NOT use markdown asterisks (*), hashtags (#), or emojis. Use clean plain text with line breaks."
            )

            # Try Gemini models in priority order with fallback
            candidate_models = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash"]
            for model_name in candidate_models:
                try:
                    from google.genai import types
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=q_clean,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            temperature=0.75,
                            max_output_tokens=700,
                        )
                    )
                    if response and response.text:
                        cleaned_text = response.text.replace("*", "").replace("#", "").strip()
                        return cleaned_text
                except Exception as e:
                    print(f"[BrainEngine] {model_name} failed: {e}. Trying fallback model...")
                    continue

    def think_and_answer_image(self, prompt: str, image_bytes: bytes, mime_type: str = "image/png") -> str:
        """Process an image or screenshot along with user question using Gemini Vision."""
        if not self.gemini_available or not self.client:
            return "Sir, image analysis requires an active Gemini connection."

        today = datetime.now().strftime("%A, %d %B %Y")
        memory_context = self.get_memory_summary()

        system_prompt = (
            f"You are J.A.R.V.I.S., serving Sir {config.USER_NAME}. Today's date is {today}. "
            f"Known facts about user: \n{memory_context}\n"
            f"Carefully analyze the image provided by the user. "
            f"If it contains a question, math problem, or formula, solve or explain it step-by-step with clear numbered lines. "
            f"If it shows a person, landmark, object, or code, identify it clearly and give helpful context. "
            f"If formulas are shown, write them cleanly on separate lines. "
            f"Address user as 'Sir' or 'Sir {config.USER_NAME}'. "
            f"Respond in the same language as user prompt (Hindi, Hinglish, or English). "
            f"Do NOT use markdown asterisks or hashes. Write clean, readable text."
        )

        user_text = prompt.strip() if prompt.strip() else "Please analyze this image and explain everything clearly, Sir."

        candidate_models = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash"]
        for model_name in candidate_models:
            try:
                from google.genai import types
                part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=[part, user_text],
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.4,
                        max_output_tokens=800,
                    )
                )
                if response and response.text:
                    return response.text.replace("*", "").replace("#", "").strip()
            except Exception as e:
                print(f"[BrainEngine] Vision with {model_name} failed: {e}")
                continue

        return "Sir, I encountered an issue analyzing the uploaded image. Please try again."

        # 2. Math Calculations
        math_res = self._solve_math(q_lower)
        if math_res:
            return math_res

        # Detect language of user's query
        hindi_chars = re.search(r'[\u0900-\u097F]', q_clean)  # Devanagari script
        hindi_words = re.search(r'\b(kya|hai|hain|bolo|batao|kaun|kaise|karo|mujhe|mera|tera|tum|aap|hum|yaar|bhai|isko|usko|accha|theek|nahi|nhi|haan|ha)\b', q_lower)
        is_hindi = bool(hindi_chars or hindi_words)
        only_english = not is_hindi and not re.search(r'[^\x00-\x7F]', q_clean)
        is_hinglish = is_hindi and re.search(r'[a-zA-Z]{3,}', q_clean)

        # 3. Conversational Rules & Personality
        # Well-being check
        if re.search(r'\b(how are you|kaise ho|kya haal hai|sab thik|kaisa hai)\b', q_lower):
            if is_hindi:
                return f"Main bilkul theek hoon, Sir {config.USER_NAME}. Aap kaise hain? Kya koi kaam hai mujhse?"
            elif is_hinglish:
                return f"Main perfectly fine hoon, Sir {config.USER_NAME}! Aap batao, kya help chahiye?"
            return f"I am functioning at peak efficiency, Sir {config.USER_NAME}. Thank you for asking. How are you doing today?"

        # Activity check
        if re.search(r'\b(what are you doing|kya kar rahe ho|kya kar raha hai|what\'s up|whats up)\b', q_lower):
            if is_hindi:
                return f"Sir, main aapke PC systems monitor kar raha hoon aur aapke aadesh ka intezaar kar raha hoon."
            elif is_hinglish:
                return f"Sir, main aapke PC ko monitor kar raha hoon aur aapka wait kar raha hoon, kya kaam hai?"
            return f"I am actively monitoring your PC systems and awaiting your instructions, Sir."

        # Greetings
        if re.search(r'\b(hi|hello|hey|namaste|yo|morning|afternoon|evening|hii|helo)\b', q_lower):
            if is_hindi:
                greetings = [
                    f"Namaste Sir {config.USER_NAME}! Main hazir hoon, kya seva karoon?",
                    f"Hello Sir {config.USER_NAME}! Aaj main aapki kya madad kar sakta hoon?",
                    f"Jai ho Sir {config.USER_NAME}! Sab systems bilkul theek hain, aadesh karein."
                ]
            elif is_hinglish:
                greetings = [
                    f"Hello Sir {config.USER_NAME}! Kya help chahiye aapko?",
                    f"Hi Sir! Sab systems ready hain, batao kya karna hai.",
                    f"Hey Sir {config.USER_NAME}! Main ready hoon, bolo kya kaam hai?"
                ]
            else:
                greetings = [
                    f"Hello Sir {config.USER_NAME}! How may I assist you today?",
                    f"Greetings Sir {config.USER_NAME}. Systems are fully operational and ready for your command.",
                    f"Hello Sir. Good to hear from you. What can I do for you today?"
                ]
            return random.choice(greetings)

        # Identity & Maker
        if re.search(r'\b(who are you|tum kon ho|tumhara naam|aap kaun|introduce yourself|what is your name|tera naam)\b', q_lower):
            if is_hindi:
                return f"Sir, main {config.ASSISTANT_NAME} hoon, aapka personal AI assistant. Main aapka PC control kar sakta hoon, apps khol sakta hoon, music baja sakta hoon, internet search kar sakta hoon, aur aapke har sawaal ka jawab de sakta hoon."
            return f"I am {config.ASSISTANT_NAME}, your personal artificial intelligence assistant, Sir. I can control your PC, launch apps, play music, search the web, and answer your questions."

        if re.search(r'\b(who made you|tumhe kisne banaya|kisne create kiya|who created you|who built you)\b', q_lower):
            if is_hindi:
                return f"Sir {config.USER_NAME} ne mujhe banaya hai, bilkul Tony Stark ki tarah. Main unki iconic JARVIS system se inspired hoon."
            elif is_hinglish:
                return f"Aapne banaya hai mujhe, Sir {config.USER_NAME}! Tony Stark ki tarah inspired system."
            return f"I was built by you, Sir {config.USER_NAME}, inspired by Tony Stark's iconic system."

        if re.search(r'\b(what can you do|tum kya kar sakte|kya kya kar sakte|help|features|kya karta hai)\b', q_lower):
            if is_hindi:
                return f"Sir, main Chrome, Notepad jaisi apps khol sakta hoon, Google search kar sakta hoon, YouTube par music baja sakta hoon, PC ka volume adjust kar sakta hoon, screenshot le sakta hoon, aur har tarah ke sawaal ka jawab de sakta hoon."
            return f"I can open apps like Chrome and Notepad, search Google, play music on YouTube, adjust PC volume, take screenshots, check system status, and answer knowledge questions, Sir."

        # Jokes
        if re.search(r'\b(joke|make me laugh|joke sunao|hasao|funny)\b', q_lower):
            if is_hindi:
                jokes = [
                    "Sir, programmers dark mode kyun pasand karte hain? Kyunki light se bugs aa jaate hain!",
                    "Sir, computer ko thand kyun lag rahi thi? Kyunki usne apni Windows khuli chhhod di thi!",
                    "Sir, ek programmer roz gym jaata tha. Poochha kyun? Bola loops run karta hoon!"
                ]
            else:
                jokes = [
                    "Why do programmers prefer dark mode, Sir? Because light attracts bugs.",
                    "Why was the computer cold, Sir? Because it left its Windows open.",
                    "There are only 10 types of people in the world: those who understand binary, and those who do not, Sir.",
                    "Why did the smartphone get glasses, Sir? Because it lost its contacts."
                ]
            return random.choice(jokes)

        # Gratitude
        if re.search(r'\b(thank you|thanks|shukriya|dhanyawad|thanks bhai|bahut achha|shukriya)\b', q_lower):
            if is_hindi:
                return f"Koi baat nahi Sir {config.USER_NAME}, main hamesha aapki seva mein hazir hoon."
            elif is_hinglish:
                return f"Koi baat nahi Sir! Main hamesha ready hoon aapke liye."
            return f"You are most welcome, Sir {config.USER_NAME}. Always at your service."

        # Farewell
        if re.search(r'\b(bye|good night|alvida|see you|band kar|chalo bye|ok bye)\b', q_lower):
            if is_hindi:
                return f"Alvida Sir {config.USER_NAME}. Main stanby mein rahoon ga, jab bhi zaroorat ho bulayein."
            elif is_hinglish:
                return f"Bye Sir {config.USER_NAME}! Main standby mein hoon, kabhi bhi bulao."
            return f"Goodbye Sir {config.USER_NAME}. Going on standby. Call me whenever you need me."

        # 4. Wikipedia Search for general knowledge
        wiki_res = self._search_wikipedia(q_lower)
        if wiki_res:
            return wiki_res

        # 5. Smart fallback
        if is_hindi:
            return f"Sir, mujhe is sawaal ka jawab abhi nahi pata. Kya aap mujhe Google par search karne ko bolein?"
        elif is_hinglish:
            return f"Sir, is question ka exact answer nahi pata mujhe abhi. Shall I search Google for you?"
        return f"I am not certain about that, Sir {config.USER_NAME}. Would you like me to search Google for '{q_clean}'?"

