import os
import re
import queue
import threading
import time
try:
    import speech_recognition as sr
except Exception as e_sr:
    sr = None
import config

class VoiceEngine:
    """
    Handles speech synthesis (speaking) and speech recognition (listening)
    using native Windows SAPI.SpVoice for 100% guaranteed reliable speech,
    with thread-safety and status callbacks for the UI.
    """
    def __init__(self, on_status_change=None):
        self.on_status_change = on_status_change
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.stop_requested = False

        # Initialize Recognizer
        if sr:
            try:
                self.recognizer = sr.Recognizer()
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.8
            except Exception:
                self.recognizer = None
        else:
            self.recognizer = None

        # Start TTS background worker
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()

    def _tts_worker(self):
        """Dedicated thread with COM initialized for native Windows SAPI speech."""
        try:
            import pythoncom
            import win32com.client

            pythoncom.CoInitialize()
            speaker = win32com.client.Dispatch("SAPI.SpVoice")

            # Try to load Windows OneCore Voices first (e.g., Microsoft Ravi - English India)
            selected_voice = None
            try:
                category = win32com.client.Dispatch("SAPI.SpObjectTokenCategory")
                category.SetId(r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices", False)
                onecore_tokens = category.EnumerateTokens()
                preferred = getattr(config, "PREFERRED_VOICE", "Ravi").lower()

                # Find preferred voice in OneCore tokens
                for i in range(onecore_tokens.Count):
                    token = onecore_tokens.Item(i)
                    desc = token.GetDescription().lower()
                    if preferred in desc:
                        selected_voice = token
                        break

                # Fallback to any Indian accent voice if specific preferred not found
                if not selected_voice and preferred in ["ravi", "heera", "india"]:
                    for i in range(onecore_tokens.Count):
                        token = onecore_tokens.Item(i)
                        desc = token.GetDescription().lower()
                        if "india" in desc or "ravi" in desc:
                            selected_voice = token
                            break
            except Exception as e_onecore:
                print(f"[VoiceEngine] OneCore voice lookup: {e_onecore}")

            # If OneCore found, assign it; otherwise fallback to classic SAPI voices
            if selected_voice:
                speaker.Voice = selected_voice
            else:
                voices = speaker.GetVoices()
                preferred = getattr(config, "PREFERRED_VOICE", "David").lower()
                for v in voices:
                    if preferred in v.GetDescription().lower():
                        speaker.Voice = v
                        break

            # Rate: -10 to +10 (0 or 1 is natural pace)
            speaker.Rate = 0
            speaker.Volume = 100
            print(f"[VoiceEngine] Active Voice: {speaker.Voice.GetDescription()}")
        except Exception as e:
            print(f"[VoiceEngine] Native SAPI init failed: {e}. Falling back to pyttsx3.")
            speaker = None
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate', config.VOICE_RATE)
            except Exception as e2:
                print(f"[VoiceEngine] pyttsx3 fallback failed: {e2}")
                engine = None

        while not self.stop_requested:
            try:
                text = self.speech_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if text is None:
                break

            try:
                self.is_speaking = True
                if self.on_status_change:
                    self.on_status_change("SPEAKING", text)

                print(f"[JARVIS Speaks]: {text}")
                
                # Clean text: remove asterisks, hash signs, URLs, or markdown
                clean_speech = re.sub(r'https?://\S+', 'link', text)
                clean_speech = clean_speech.replace("*", "").replace("#", "").replace("_", " ").strip()

                if speaker:
                    speaker.Speak(clean_speech)
                elif engine:
                    engine.say(clean_speech)
                    engine.runAndWait()
            except Exception as e:
                print(f"[VoiceEngine] Speech playback error: {e}")
            finally:
                self.is_speaking = False
                if self.on_status_change:
                    self.on_status_change("STANDBY", "")
                self.speech_queue.task_done()

    def speak(self, text: str):
        """Queue text to be spoken by JARVIS."""
        if not text:
            return
        self.speech_queue.put(text)

    def speak_and_wait(self, text: str):
        """Speak text and wait until speech finishes."""
        self.speak(text)
        self.speech_queue.join()

    def listen(self, timeout=5, phrase_time_limit=8) -> str:
        """
        Listen through the microphone and return transcribed text.
        Returns empty string if speech was not detected or understood.
        """
        if not sr or not self.recognizer or self.is_speaking:
            return ""

        try:
            with sr.Microphone() as source:
                if self.on_status_change:
                    self.on_status_change("LISTENING", "Listening...")

                # Adjust for ambient background noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.25)

                try:
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                except sr.WaitTimeoutError:
                    if self.on_status_change:
                        self.on_status_change("STANDBY", "")
                    return ""

                if self.on_status_change:
                    self.on_status_change("PROCESSING", "Understanding command...")

                try:
                    query = self.recognizer.recognize_google(audio, language="en-IN")
                    print(f"[User Said]: {query}")
                    return query
                except sr.UnknownValueError:
                    return ""
                except sr.RequestError as e:
                    print(f"[VoiceEngine] STT Service Error: {e}")
                    return ""
                finally:
                    if self.on_status_change:
                        self.on_status_change("STANDBY", "")
        except Exception as e:
            print(f"[VoiceEngine] Microphone error: {e}")
            if self.on_status_change:
                self.on_status_change("STANDBY", "")
            return ""

    def stop(self):
        self.stop_requested = True
        self.speech_queue.put(None)
