from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import threading
import subprocess
import re
import os
import time
import datetime
import webbrowser
import urllib.parse
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from predict import predict_intent, get_response

import speech_recognition as sr
import pyttsx3
import pythoncom

# ==============================================================
# GLOBAL SHARED STATE (thread-safe with a lock)
# ==============================================================
_state_lock = threading.Lock()
_state = {
    "status": "System Standby",
    "query":  "Click the microphone to start...",
    "logs": [],
    "knowledge": {
        "title":   "Awaiting Query...",
        "content": "Ask a question or say a command to extract data."
    },
    "is_listening": False,
}

def _set(**kwargs):
    with _state_lock:
        _state.update(kwargs)

def _log(speaker, text):
    with _state_lock:
        _state["logs"].append({"speaker": speaker, "text": text})
    print(f"[{speaker}] {text}")   # also print to terminal for debugging


# ==============================================================
# OPEN APPLICATIONS & URLS — using subprocess for reliability
# ==============================================================

def open_url(url, label=""):
    """Open any URL in the default browser (works from any thread)."""
    try:
        _log("System", f"Opening URL: {url}")
        webbrowser.open(url)
        return True
    except Exception as e:
        _log("System", f"URL open failed: {e}")
        return False


def open_application(app_name):
    """
    Universal app launcher — multi-strategy, reliable on Windows.
    Returns True if launched successfully, False if app not found.
    """
    # Known name → executable mappings
    mappings = {
        "word": "winword",
        "microsoft word": "winword",
        "ms word": "winword",
        "powerpoint": "powerpnt",
        "microsoft powerpoint": "powerpnt",
        "ppt": "powerpnt",
        "ms powerpoint": "powerpnt",
        "excel": "excel",
        "microsoft excel": "excel",
        "ms excel": "excel",
        "notepad": "notepad",
        "calc": "calc",
        "calculator": "calc",
        "paint": "mspaint",
        "ms paint": "mspaint",
        "code": "code",
        "vscode": "code",
        "vs code": "code",
        "visual studio code": "code",
        "figma": "figma://",
        "spotify": "spotify",
        "explorer": "explorer",
        "file explorer": "explorer",
        "task manager": "taskmgr",
        "taskmgr": "taskmgr",
        "settings": "ms-settings:",
        "windows settings": "ms-settings:",
        "cmd": "cmd",
        "command prompt": "cmd",
        "chrome": "chrome",
        "google chrome": "chrome",
        "edge": "msedge",
        "microsoft edge": "msedge",
        "snippingtool": "SnippingTool",
        "snipping tool": "SnippingTool",
    }

    app_id = app_name.lower().strip()
    target = mappings.get(app_id, app_name.strip())  # fallback to original casing

    _log("System", f"Attempting launch: '{target}'")

    # Strategy 1: If it's a protocol URI (e.g., ms-settings: figma://)
    if ":" in target:
        try:
            subprocess.Popen(["cmd", "/c", "start", "", target], shell=False)
            return True
        except Exception as e:
            _log("System", f"Protocol launch failed: {e}")
            return False

    # Strategy 2: Use `cmd /c start "" <target>` — the correct Windows shell syntax
    # The empty string "" is the window title, required when passing args with start
    try:
        subprocess.Popen(["cmd", "/c", "start", "", target], shell=False)
        _log("System", f"Launched via cmd start: {target}")
        return True
    except Exception as e:
        _log("System", f"cmd start failed: {e}")

    # Strategy 3: Fall back to os.startfile
    try:
        os.startfile(target)
        _log("System", f"Launched via os.startfile: {target}")
        return True
    except Exception as e:
        _log("System", f"os.startfile failed: {e}")

    return False


def google_search(query):
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    open_url(url, f"Google: {query}")


def youtube_play(query):
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    open_url(url, f"YouTube: {query}")


# ==============================================================
# VOICE ASSISTANT CLASS
# ==============================================================

class VoiceAssistant:

    # ---------- TTS ----------
    def speak(self, text):
        _set(query=text, status="Speaking...")
        _log("Assistant", text)

        try:
            pythoncom.CoInitialize()
            engine = pyttsx3.init('sapi5')
            engine.setProperty('rate', 165)
            voices = engine.getProperty('voices')
            
            # Select a female voice (often index 1 on Windows)
            female_voice = None
            if voices:
                for v in voices:
                    name_lower = v.name.lower()
                    if "female" in name_lower or "zira" in name_lower or "hazel" in name_lower:
                        female_voice = v.id
                        break
                
                if female_voice:
                    engine.setProperty('voice', female_voice)
                elif len(voices) > 1:
                    engine.setProperty('voice', voices[1].id)

            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            _log("System", f"TTS error: {e}")

        with _state_lock:
            still_on = _state["is_listening"]
        if still_on:
            _set(status="Listening...", query="Say a command...")
        else:
            _set(status="System Standby", query="Click microphone to start...")

    # ---------- LISTEN LOOP ----------
    def listen_loop(self):
        pythoncom.CoInitialize()
        recognizer = sr.Recognizer()

        # ── Tuning for full-sentence capture ──────────────────
        # How many seconds of silence = end of phrase (was 1.2 — too short)
        recognizer.pause_threshold = 2.0
        # Minimum silence that counts as the end of a word
        recognizer.non_speaking_duration = 0.8
        # Fixed energy threshold — dynamic mode was cutting speech off early
        recognizer.dynamic_energy_threshold = False
        recognizer.energy_threshold = 400   # raise if room is noisy

        _log("System", "Microphone array initialized.")

        while True:
            with _state_lock:
                if not _state["is_listening"]:
                    break
            try:
                with sr.Microphone() as source:
                    # Short calibration so listening starts fast
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    _set(status="Listening...", query="Awaiting vocal input...")
                    try:
                        # timeout=15 waits 15s for you to start speaking
                        # phrase_time_limit=30 allows up to 30s per command
                        audio = recognizer.listen(source, timeout=15, phrase_time_limit=30)
                    except sr.WaitTimeoutError:
                        continue

                _set(status="Processing...")
                try:
                    command = recognizer.recognize_google(audio).lower().strip()
                except sr.UnknownValueError:
                    _set(query="Could not understand audio...")
                    continue
                except sr.RequestError as e:
                    _log("System", f"Google STT error: {e}")
                    _set(query="Network error. Check your connection.")
                    self.speak("Network error. Could not process speech.")
                    continue

                _log("You", command)
                _set(query=f'"{command}"')

                # Strip wake words
                for w in ["marry", "aura", "hey aura", "hey marry", "assistant"]:
                    command = command.replace(w, "").strip()

                if command:
                    self.process_command(command)

            except OSError as e:
                _log("System", f"Microphone OS error: {e}")
                time.sleep(1)
            except Exception as e:
                _log("System", f"Loop error: {e}")
                time.sleep(1)

        _log("System", "Listening loop ended.")
        _set(status="System Standby", query="Click microphone to start...")

    # ---------- COMMAND PROCESSOR ----------
    def process_command(self, cmd):
        _log("System", f"Processing: '{cmd}'")

        try:

            # Machine Learning Intent Prediction
            tag, confidence = predict_intent(cmd)
            
            if tag == 'unknown':
                self.speak("Sorry, I didn't understand that.")
                # Fallback Search
                _set(knowledge={"title": "Fallback Search", "content": f"Query: {cmd}"})
                google_search(cmd)
                return
                
            response = get_response(tag)

            social_intents = [
                'greeting', 'about_assistant', 'help_user', 'thank_you', 
                'apology', 'jokes_fun', 'motivation', 'mood_happy', 
                'mood_sad', 'small_talk', 'capabilities', 'ai_knowledge', 
                'compliments', 'creator_info'
            ]

            if tag in social_intents:
                self.speak(response)

            elif tag == 'time':
                t = datetime.datetime.now().strftime("%I:%M %p")
                self.speak(f"{response}. It is {t}.")

            elif tag == 'music':
                q = re.sub(r'(play|on youtube|youtube|music|a song|songs|playlist|start|please|any)', '', cmd).strip()
                if not q:
                    q = "trending songs"
                _set(knowledge={"title": "Media Control", "content": f"Streaming: {q}"})
                self.speak(response)
                youtube_play(q)

            elif tag == 'weather':
                self.speak(response)
                google_search("weather today")

            elif tag == 'search':
                m = re.sub(r'(search|for|on|google|internet|web|find|information|look up|this)', '', cmd).strip()
                if not m:
                    m = cmd
                _set(knowledge={"title": "Google Search", "content": f"Query: {m}"})
                self.speak(response)
                google_search(m)

            elif tag == 'wikipedia':
                q = cmd.replace("wikipedia", "").replace("search", "").replace("for", "").replace("tell", "").replace("from", "").replace("about", "").replace("open", "").replace("wiki", "").replace("find", "").replace("on", "").strip()
                self.speak(response)
                if q:
                    try:
                        import wikipedia
                        results = wikipedia.summary(q, sentences=2)
                        _set(knowledge={"title": f"Wikipedia: {q.title()}", "content": results})
                        self.speak(f"According to Wikipedia, {results}")
                    except Exception:
                        _set(knowledge={"title": "Data Error", "content": "No matches found."})
                        self.speak("I couldn't find a specific Wikipedia entry for that.")
                else:
                    self.speak("What subject should I lookup on Wikipedia?")

            elif tag == 'open_app':
                app_to_open = re.sub(r'\b(open|launch|start|application|browser)\b', '', cmd).strip()
                if not app_to_open:
                    self.speak(response)
                else:
                    web_mappings = {
                        "google": "https://www.google.com",
                        "youtube": "https://www.youtube.com",
                        "instagram": "https://www.instagram.com",
                        "facebook": "https://www.facebook.com",
                        "twitter": "https://www.x.com",
                        "x.com": "https://www.x.com",
                        "github": "https://www.github.com",
                        "linkedin": "https://www.linkedin.com",
                        "whatsapp": "https://web.whatsapp.com",
                        "gmail": "https://mail.google.com",
                        "maps": "https://maps.google.com"
                    }
                    self.speak(response)
                    found_web = False
                    for kw, url in web_mappings.items():
                        if kw in app_to_open:
                            open_url(url)
                            found_web = True
                            break
                    if not found_web:
                        success = open_application(app_to_open)
                        if not success:
                            self.speak(f"I'm sorry, I couldn't find {app_to_open} on your system.")

            elif tag == 'food':
                self.speak(response)
                if "zomato" in cmd:
                    open_url("https://www.zomato.com")
                else:
                    open_url("https://www.swiggy.com")

            elif tag == 'shopping':
                self.speak(response)
                if "myntra" in cmd:
                    open_url("https://www.myntra.com")
                elif "flipkart" in cmd:
                    open_url("https://www.flipkart.com")
                else:
                    open_url("https://www.amazon.in")

            elif tag == 'exit':
                self.speak(response)
                _set(is_listening=False, status="Offline", query="System shutdown complete.")

        except Exception as e:
            _log("System", f"process_command exception: {e}")
            self.speak("An unexpected error occurred.")


# Singleton
_assistant = VoiceAssistant()


# ==============================================================
# DJANGO VIEWS
# ==============================================================

def index_view(request):
    from django.views.static import serve
    return serve(request, document_root='.', path='/web/index.html')


@csrf_exempt
def toggle_listen(request):
    with _state_lock:
        currently = _state["is_listening"]

    if not currently:
        _set(is_listening=True, status="Initializing...", query="Starting microphone...")
        _log("System", "Voice recognition activated.")
        t = threading.Thread(target=_assistant.listen_loop, daemon=True)
        t.start()
    else:
        _set(is_listening=False)
        _log("System", "Voice recognition deactivated.")

    with _state_lock:
        new_state = _state["is_listening"]
    return JsonResponse({"status": "ok", "is_listening": new_state})


@csrf_exempt
def send_command(request):
    import json
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cmd = data.get('command', '').lower().strip()
            if cmd:
                _log("You", cmd)
                _set(query=f'"{cmd}"')
                # Run processor in a thread to not block the request
                threading.Thread(target=_assistant.process_command, args=(cmd,), daemon=True).start()
                return JsonResponse({"status": "ok", "message": f"Processing '{cmd}'"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "POST required"}, status=405)


def get_state(request):
    with _state_lock:
        logs = list(_state["logs"])
        _state["logs"].clear()
        return JsonResponse({
            "status":       _state["status"],
            "query":        _state["query"],
            "knowledge":    dict(_state["knowledge"]),
            "new_logs":     logs,
            "is_listening": _state["is_listening"],
        })
