import os
import sys
import time
import json
import asyncio
import threading
import subprocess
import webbrowser
import psutil
import uvicorn
from starlette.applications import Starlette
from starlette.routing import WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.responses import FileResponse

import config
from voice import VoiceEngine
from automation import AutomationEngine
from brain import BrainEngine

# ==========================================
# Globals & State
# ==========================================
connected_websockets = set()
loop = None

def broadcast_sync(message_dict):
    """Safely broadcast JSON message to all connected UI clients."""
    if not loop:
        return
    msg_str = json.dumps(message_dict)
    for ws in list(connected_websockets):
        try:
            asyncio.run_coroutine_threadsafe(ws.send_text(msg_str), loop)
        except Exception:
            pass

def on_status_change(status: str, text: str = ""):
    """Callback when voice engine changes status."""
    broadcast_sync({
        "type": "status",
        "status": status,
        "text": text
    })

# Initialize Engines
voice = VoiceEngine(on_status_change=on_status_change)
automation = AutomationEngine(voice_engine=voice)
brain = BrainEngine()

# ==========================================
# Command Processor Logic
# ==========================================
def process_command(cmd: str):
    """Determine user intent and execute appropriate action."""
    if not cmd:
        return

    cmd_raw = cmd.strip()
    cmd_clean = cmd_raw.lower()
    print(f"[Command Processor]: Received '{cmd_raw}'")

    # Broadcast user query to UI transcript
    broadcast_sync({
        "type": "transcript",
        "sender": "user",
        "text": cmd_raw
    })

    # Check if user simply greeted or called Jarvis
    if cmd_clean in ["jarvis", "hey jarvis", "hi jarvis", "hello jarvis", "ok jarvis", "jar", "hi jar", "hey jar"]:
        resp = f"Yes, Sir {config.USER_NAME}? I am online and listening. How can I help you?"
        broadcast_sync({"type": "transcript", "sender": "jarvis", "text": resp})
        voice.speak(resp)
        return

    # Strip wake word prefixes and suffixes
    import re
    cleaned_intent = re.sub(r'^(jarvis|hey jarvis|hi jarvis|hello jarvis|ok jarvis)[,\s]*', '', cmd_clean).strip()
    cleaned_intent = re.sub(r'[,\s]*(jarvis|jar)$', '', cleaned_intent).strip()
    if not cleaned_intent:
        cleaned_intent = cmd_clean

    # Clean filler words common in Hindi/Hinglish (e.g., "bhai", "yaar", "please", "ek baar", "zara", "theek hai")
    cleaned_intent = re.sub(r'\b(bhai|yaar|please|zara|ek baar|achha|theek hai|accha theek hai|sun|suno)\b', '', cleaned_intent).strip()
    cleaned_intent = re.sub(r'^[,\s\.\?!]+|[,\s\.\?!]+$', '', cleaned_intent).strip()

    # 1. Check App / Website Launching (English + Hindi: "open karo", "kholo", "chalao", "start karo")
    # Matches patterns like: "open youtube", "youtube kholo", "youtube open karo", "chrome start karo"
    open_match = re.search(r'^(?:open|launch|start)\s+([a-zA-Z0-9\.\s]+)', cleaned_intent)
    if not open_match:
        open_match = re.search(r'([a-zA-Z0-9\.\s]+?)\s+(?:kholo|open karo|chala do|chalao|start karo|shuru karo)$', cleaned_intent)
    
    if open_match:
        target = open_match.group(1).strip()
        # Clean extra prepositions
        target = re.sub(r'\b(app|application|website|site)\b', '', target).strip()
        if target in config.WEBSITE_SHORTCUTS or target.endswith(".com") or target.endswith(".org") or target == "youtube":
            automation.open_website(target)
            msg = f"Opening {target}, Sir {config.USER_NAME}."
            broadcast_sync({"type": "transcript", "sender": "jarvis", "text": msg})
            return
        elif target in config.APP_SHORTCUTS:
            automation.open_app(target)
            msg = f"Opening {target}, Sir {config.USER_NAME}."
            broadcast_sync({"type": "transcript", "sender": "jarvis", "text": msg})
            return
        else:
            success = automation.open_app(target)
            if success:
                msg = f"Opening {target}, Sir {config.USER_NAME}."
                broadcast_sync({"type": "transcript", "sender": "jarvis", "text": msg})
                return

    # 2. YouTube Playback (English + Hindi: "mere liye ek music bajao", "gana bajao", "play ... on youtube")
    # Patterns: "gana bajao", "music bajao", "song chalao", "youtube par song bajao"
    yt_play = False
    song_query = ""

    if re.search(r'\b(music bajao|gana bajao|gaana bajao|gana chalao|song bajao|song chala do|music chalao|song lagao|music lagao)\b', cleaned_intent):
        yt_play = True
        # Extract song name if specified
        m = re.search(r'(?:gana|song|track|music)\s*(?:bajao|chalao|lagao)?\s*(?:mein|pe|par)?\s*(.+)', cleaned_intent)
        song_query = m.group(1).strip() if m else ""
        song_query = re.sub(r'\b(youtube|se|pe|par|ek|koi|achha|accha|mere liye|bajao|chalao|lagao)\b', '', song_query).strip()
        if not song_query:
            song_query = "top trending songs"

    elif "play" in cleaned_intent:
        yt_play = True
        song_query = cleaned_intent.replace("play", "").replace("on youtube", "").replace("youtube", "").strip()
        if not song_query:
            song_query = "top hit songs"

    if yt_play:
        automation.play_youtube(song_query)
        msg = f"Playing {song_query} on YouTube, Sir."
        broadcast_sync({"type": "transcript", "sender": "jarvis", "text": msg})
        return

    # 3. Google Search (English + Hindi: "google par search karo", "search karo")
    if re.search(r'(?:search google for|search on google|google par search karo|google pe dhundo|search karo|search)\s+(.+)', cleaned_intent):
        m = re.search(r'(?:search google for|search on google|google par search karo|google pe dhundo|search karo|search)\s+(.+)', cleaned_intent)
        q = m.group(1).replace("google par", "").replace("google pe", "").strip() if m else ""
        if q:
            automation.search_google(q)
            msg = f"Searching Google for {q}, Sir."
            broadcast_sync({"type": "transcript", "sender": "jarvis", "text": msg})
            return

    # 4. Volume Controls (English + Hindi: "volume badhao", "kam karo", "mute karo")
    if any(k in cleaned_intent for k in ["volume", "mute", "unmute", "awaaz badhao", "awaz kam karo", "awaaz kam"]):
        automation.adjust_volume(cleaned_intent)
        broadcast_sync({"type": "transcript", "sender": "jarvis", "text": "Volume adjusted, Sir."})
        return

    # 5. Screenshot (English + Hindi: "screenshot lo", "photo khicho")
    if any(k in cleaned_intent for k in ["screenshot", "capture screen", "screenshot lo", "screen capture"]):
        filepath = automation.take_screenshot()
        broadcast_sync({"type": "transcript", "sender": "jarvis", "text": f"Screenshot saved at {filepath}"})
        return

    # 6. Time and Date (English + Hindi: "kya samay hua hai", "time kya hai", "aaj konsi date hai")
    if any(k in cleaned_intent for k in ["time", "date", "samay", "tarikh", "tareekh", "waqt"]):
        t_res = automation.get_time_and_date(cleaned_intent)
        broadcast_sync({"type": "transcript", "sender": "jarvis", "text": t_res})
        return

    # 7. System / Battery / CPU Status (English + Hindi: "pc ka hal kya hai", "battery kitni hai")
    if any(k in cleaned_intent for k in ["system status", "battery", "cpu", "ram", "battery kitni", "pc status"]):
        metrics = automation.get_system_status()
        status_text = f"CPU: {metrics['cpu']}%, RAM: {metrics['ram']}%"
        if metrics['battery']:
            status_text += f", Battery: {metrics['battery']}%"
        broadcast_sync({"type": "transcript", "sender": "jarvis", "text": status_text})
        return

    # 8. Lock PC (English + Hindi: "pc lock karo", "computer band karo")
    if any(k in cleaned_intent for k in ["lock pc", "lock computer", "lock screen", "pc lock karo", "screen lock karo"]):
        broadcast_sync({"type": "transcript", "sender": "jarvis", "text": "Locking workstation, Sir."})
        automation.lock_pc()
        return

    # 9. General Question / AI Brain
    answer = brain.think_and_answer(cmd_raw)
    if answer:
        broadcast_sync({
            "type": "transcript",
            "sender": "jarvis",
            "text": answer
        })
        voice.speak(answer)

def process_image_command(prompt: str, image_b64: str, mime_type: str = "image/png"):
    """Handle multimodal queries where the user uploads an image/screenshot."""
    import base64
    try:
        image_bytes = base64.b64decode(image_b64)
        answer = brain.think_and_answer_image(prompt, image_bytes, mime_type)
        if answer:
            broadcast_sync({
                "type": "transcript",
                "sender": "jarvis",
                "text": answer
            })
            voice.speak(answer)
    except Exception as e:
        err_msg = f"Sir, I could not process the attached file: {e}"
        broadcast_sync({
            "type": "transcript",
            "sender": "jarvis",
            "text": err_msg
        })
        voice.speak(err_msg)

# ==========================================
# Continuous Voice Listening Loop
# ==========================================
def continuous_voice_listener():
    """Background listener that continuously captures voice queries."""
    # Brief initial pause to allow startup greeting to complete
    time.sleep(3)
    print("[Voice Listener Thread] Activated and listening.")

    while True:
        try:
            query = voice.listen(timeout=5, phrase_time_limit=8)
            if query:
                process_command(query)
        except Exception as e:
            print(f"[Voice Listener] Error in loop: {e}")
            time.sleep(1)

# ==========================================
# Metrics Broadcast Loop
# ==========================================
async def metrics_broadcast_loop():
    """Periodically send CPU & RAM stats to HUD."""
    while True:
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            broadcast_sync({
                "type": "metrics",
                "cpu": int(cpu),
                "ram": int(ram)
            })
        except Exception:
            pass
        await asyncio.sleep(2.5)

# ==========================================
# Starlette Web App & WebSocket Routes
# ==========================================
async def index_endpoint(scope, receive, send):
    ui_dir = os.path.join(os.path.dirname(__file__), "ui")
    response = FileResponse(os.path.join(ui_dir, "index.html"))
    await response(scope, receive, send)

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.add(websocket)
    print("[WebSocket] Client connected.")

    try:
        # Send initial AI brain status to the UI
        initial_status = "GEMINI ONLINE" if brain.gemini_available else "LOCAL BRAIN"
        await websocket.send_text(json.dumps({
            "type": "ai_status",
            "status": initial_status
        }))

        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            msg_type = msg.get("type")
            if msg_type == "command":
                cmd_text = msg.get("text", "").strip()
                # Run command processing in background thread to avoid blocking WebSocket loop
                threading.Thread(target=process_command, args=(cmd_text,), daemon=True).start()
            elif msg_type == "image_command":
                prompt_text = msg.get("text", "").strip()
                image_b64 = msg.get("image", "")
                mime_type = msg.get("mime_type", "image/png")
                threading.Thread(target=process_image_command, args=(prompt_text, image_b64, mime_type), daemon=True).start()
            elif msg_type == "save_api_key":
                api_key = msg.get("key", "").strip()
                success = brain.reload_api_key(api_key)
                if success:
                    resp_text = "Gemini AI Brain successfully activated, Sir. I am now at maximum intelligence."
                    voice.speak(resp_text)
                    broadcast_sync({
                        "type": "api_key_status",
                        "success": True,
                        "message": "Gemini AI Connected!"
                    })
                    broadcast_sync({
                        "type": "ai_status",
                        "status": "GEMINI ONLINE"
                    })
                    broadcast_sync({
                        "type": "transcript",
                        "sender": "jarvis",
                        "text": resp_text
                    })
                else:
                    broadcast_sync({
                        "type": "api_key_status",
                        "success": False,
                        "message": "Invalid API Key or connection failed."
                    })
            elif msg_type == "shutdown":
                farewell = f"Goodbye Sir {config.USER_NAME}. Systems shutting down."
                broadcast_sync({"type": "transcript", "sender": "jarvis", "text": farewell})
                voice.speak(farewell)
                time.sleep(1.5)
                os.kill(os.getpid(), 9)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
    finally:
        connected_websockets.remove(websocket)
        print("[WebSocket] Client disconnected.")

import contextlib

@contextlib.asynccontextmanager
async def lifespan(app):
    global loop
    loop = asyncio.get_running_loop()
    asyncio.create_task(metrics_broadcast_loop())
    
    # Get local Wi-Fi IP address
    import socket
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    print(f"\n[Server] Local PC URL:  http://127.0.0.1:{config.SERVER_PORT}")
    print(f"[Server] Phone Wi-Fi URL: http://{local_ip}:{config.SERVER_PORT}\n")
    yield

# Setup static files directory & routes
ui_dir = os.path.join(os.path.dirname(__file__), "ui")

routes = [
    WebSocketRoute("/ws", endpoint=websocket_endpoint),
    Mount("/", app=StaticFiles(directory=ui_dir, html=True), name="ui"),
]

app = Starlette(routes=routes, lifespan=lifespan)

# ==========================================
# Application Startup & Browser Launch
# ==========================================
def launch_app_window():
    """Launch Microsoft Edge in App mode or fallback to standard browser."""
    time.sleep(2.0)
    url = f"http://127.0.0.1:{config.SERVER_PORT}"
    try:
        # Launch borderless sleek app window via Edge
        subprocess.Popen(f'start msedge --app="{url}"', shell=True)
    except Exception:
        webbrowser.open(url)

def trigger_startup_greeting():
    """Greet Aditya on PC startup as requested."""
    time.sleep(3.0)
    greeting = "Hello Sir, how are you? and how can I help you?"
    broadcast_sync({
        "type": "transcript",
        "sender": "jarvis",
        "text": greeting
    })
    voice.speak(greeting)

def main():
    print("=" * 50)
    print("   J.A.R.V.I.S — MARK VII SYSTEM BOOTING")
    print(f"   User: Sir {config.USER_NAME}")
    print("=" * 50)

    # Start browser window thread
    threading.Thread(target=launch_app_window, daemon=True).start()

    # Start startup greeting thread
    threading.Thread(target=trigger_startup_greeting, daemon=True).start()

    # Start continuous microphone listening thread
    listener_thread = threading.Thread(target=continuous_voice_listener, daemon=True)
    listener_thread.start()

    # Run Uvicorn HTTP & WebSocket server
    try:
        uvicorn.run(
            app,
            host=config.SERVER_HOST,
            port=config.SERVER_PORT,
            log_level="warning"
        )
    except (KeyboardInterrupt, SystemExit):
        print("\n[J.A.R.V.I.S] Shutting down systems gracefully.")
        voice.stop()

if __name__ == "__main__":
    main()
