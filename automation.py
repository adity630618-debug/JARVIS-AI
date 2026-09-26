import os
import sys
import subprocess
import webbrowser
import urllib.parse
import datetime
import psutil
import pyautogui
import config

class AutomationEngine:
    """
    Handles Windows PC automation: opening apps, web searches,
    media controls, screenshots, and system metrics.
    """
    def __init__(self, voice_engine=None):
        self.voice = voice_engine

    def speak(self, text):
        if self.voice:
            self.voice.speak(text)
        else:
            print(f"[Automation] {text}")

    def open_app(self, app_name: str) -> bool:
        """Open a locally installed application or Windows utility."""
        app_name_clean = app_name.lower().strip()

        # Check known shortcuts
        if app_name_clean in config.APP_SHORTCUTS:
            cmd = config.APP_SHORTCUTS[app_name_clean]
            try:
                subprocess.Popen(cmd, shell=True)
                self.speak(f"Opening {app_name}, Sir.")
                return True
            except Exception as e:
                self.speak(f"Failed to open {app_name}. {e}")
                return False

        # Try generic Windows start command
        try:
            subprocess.Popen(f"start {app_name_clean}", shell=True)
            self.speak(f"Launching {app_name}, Sir.")
            return True
        except Exception:
            self.speak(f"Sorry Sir, I could not find the application {app_name}.")
            return False

    def open_website(self, site_name: str) -> bool:
        """Open a website shortcut or URL."""
        site_name_clean = site_name.lower().strip()
        if site_name_clean in config.WEBSITE_SHORTCUTS:
            url = config.WEBSITE_SHORTCUTS[site_name_clean]
            webbrowser.open(url)
            self.speak(f"Opening {site_name}, Sir.")
            return True

        if not site_name_clean.startswith("http"):
            url = f"https://www.{site_name_clean}.com"
        else:
            url = site_name_clean

        webbrowser.open(url)
        self.speak(f"Opening {site_name}, Sir.")
        return True

    def search_google(self, query: str):
        """Perform a Google search in default browser."""
        if not query:
            return
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded}"
        webbrowser.open(url)
        self.speak(f"Here is what I found on Google for {query}, Sir.")

    def play_youtube(self, song_name: str):
        """Search and play a video or music on YouTube."""
        if not song_name:
            return
        encoded = urllib.parse.quote_plus(song_name)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        webbrowser.open(url)
        self.speak(f"Playing {song_name} on YouTube, Sir.")

    def adjust_volume(self, action: str):
        """Volume control: 'up', 'down', 'mute'."""
        if "up" in action or "increase" in action:
            for _ in range(5):
                pyautogui.press("volumeup")
            self.speak("Volume increased, Sir.")
        elif "down" in action or "decrease" in action:
            for _ in range(5):
                pyautogui.press("volumedown")
            self.speak("Volume decreased, Sir.")
        elif "mute" in action or "unmute" in action:
            pyautogui.press("volumemute")
            self.speak("Volume toggled, Sir.")

    def take_screenshot(self) -> str:
        """Capture screen and save to a screenshots directory."""
        screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")
        pyautogui.screenshot(filepath)
        self.speak("Screenshot captured and saved, Sir.")
        return filepath

    def get_time_and_date(self, query: str = "time") -> str:
        """Returns and speaks current time or date."""
        now = datetime.datetime.now()
        if "date" in query.lower():
            date_str = now.strftime("%A, %B %d, %Y")
            self.speak(f"Today is {date_str}, Sir.")
            return date_str
        else:
            time_str = now.strftime("%I:%M %p")
            self.speak(f"The current time is {time_str}, Sir.")
            return time_str

    def get_system_status(self) -> dict:
        """Check CPU, RAM and Battery health."""
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        battery_info = psutil.sensors_battery()

        status_msg = f"CPU usage is at {cpu} percent. Memory usage is at {ram} percent."
        if battery_info:
            percent = battery_info.percent
            plugged = "plugged in" if battery_info.power_plugged else "on battery"
            status_msg += f" Battery is at {percent} percent and {plugged}."
        
        self.speak(status_msg + ", Sir.")
        return {"cpu": cpu, "ram": ram, "battery": battery_info.percent if battery_info else None}

    def lock_pc(self):
        """Lock the Windows workstation."""
        self.speak("Locking your PC, Sir. Have a great day!")
        os.system("rundll32.exe user32.dll,LockWorkStation")
