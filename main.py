import threading
import speech_recognition as sr
import pyttsx3
import webbrowser
import datetime
import os
import time
import re
import urllib.parse
import eel
import pythoncom  # Required to prevent COM threading crashes on Windows with pyttsx3

# ── ML Intent Prediction (from predict.py) ───────────────────────────────
# predict_intent(text)  → (tag, confidence)
# get_response(tag)     → random response string from intents.json
from predict import predict_intent, get_response

# Initialize Eel application with the web directory
eel.init('web')

is_listening_global = False

class WebVoiceAssistant:
    def __init__(self):
        self.is_speaking = False
        self.safe_call_eel("update_query", "Systems ready. Click microphone.")
        self.safe_call_eel("update_status", "System Standby")
        
    def safe_call_eel(self, func_name, *args):
        try:
            func = getattr(eel, func_name)
            func(*args)()
        except AttributeError:
            pass
            
    def speak(self, text):
        self.safe_call_eel("update_query", text)
        self.safe_call_eel("update_status", "Speaking...")
        self.safe_call_eel("update_log", "Assistant", text)
        self.is_speaking = True
        
        # Isolate Text-To-Speech inside its own safe process logic
        try:
            pythoncom.CoInitialize()
            engine = pyttsx3.init('sapi5')
            engine.setProperty('rate', 170)
            voices = engine.getProperty('voices')
            
            # Select a female voice (often index 1 on Windows)
            female_voice = None
            for v in voices:
                if "female" in v.name.lower() or "zira" in v.name.lower():
                    female_voice = v.id
                    break
            
            if female_voice:
                engine.setProperty('voice', female_voice)
            elif len(voices) > 1:
                engine.setProperty('voice', voices[1].id)
            elif len(voices) > 0:
                engine.setProperty('voice', voices[0].id)
            engine.say(text)
            engine.runAndWait()
        except RuntimeError:
            pass
                
        self.is_speaking = False
        
        global is_listening_global
        if is_listening_global:
            self.safe_call_eel("update_status", "Listening...")
            self.safe_call_eel("update_query", "Awaiting your command...")
        else:
            self.safe_call_eel("update_status", "System Standby")
            
    def listen_loop(self):
        # We initialize pythoncom COM objects for Windows threading
        pythoncom.CoInitialize()
        
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 2.0 
        global is_listening_global
        
        while is_listening_global:
            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    if not is_listening_global: break
                    self.safe_call_eel("update_status", "Listening...")
                    self.safe_call_eel("update_query", "Analyzing vocal input...")
                    
                    # Listen for audio with a shorter timeout if we want it to check the global flag more often
                    audio = recognizer.listen(source, timeout=12, phrase_time_limit=25)
                    
                if not is_listening_global: break
                self.safe_call_eel("update_status", "Processing...")
                command = recognizer.recognize_google(audio).lower()
                
                # Check again before UI updates
                if not is_listening_global: break
                
                # Show user query
                self.safe_call_eel("update_query", f'"{command}"')
                self.safe_call_eel("update_log", "You", command)
                
                if "jarvis" in command or "aura" in command:
                    command = command.replace("jarvis", "").replace("aura", "").strip()
                    if not command:
                        if is_listening_global: self.speak("At your service.")
                        continue 
                        
                if "hey assistant" in command:
                    command = command.replace("hey assistant", "").strip()
                        
                if is_listening_global:
                    self.process_command(command)
                
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                if is_listening_global:
                    self.speak("Connection to remote server terminated.")
                    self.safe_call_eel("update_log", "System", str(e))
                is_listening_global = False
                self.safe_call_eel("update_status", "System Standby")
                break
            except Exception as e:
                if is_listening_global:
                    self.safe_call_eel("update_log", "System", str(e))
                time.sleep(2)
                continue

    def process_command(self, command):
        """
        ML-Powered Command Processor
        ─────────────────────────────
        Flow:
          Voice input (text)  →  predict_intent()  →  intent tag
                              →  execute action    →  speak response
        """
        if not command:
            return

        try:
            # ── Step 1: Predict intent using the trained ML model ──────────
            tag, confidence = predict_intent(command)
            self.safe_call_eel("update_log", "System",
                               f"Intent: {tag}  (conf: {confidence*100:.1f}%)")

            # ── Step 2: If confidence too low, fall back to web search ─────
            if tag == "unknown":
                self.speak("I'm not sure what you meant. Let me search for that.")
                query = urllib.parse.quote(command)
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return

            # ── Step 3: Fetch a dynamic response from intents.json ─────────
            response = get_response(tag)

            # ── Step 4: Execute the appropriate action for each intent ─────

            # --- Conversational / Social intents ---
            social_intents = {
                "greeting", "about_assistant", "help_user", "thank_you",
                "apology", "jokes_fun", "motivation", "mood_happy",
                "mood_sad", "small_talk", "capabilities", "ai_knowledge",
                "compliments", "creator_info"
            }
            if tag in social_intents:
                self.speak(response)

            # --- Time / Date ---
            elif tag == "time":
                now = datetime.datetime.now()
                t   = now.strftime("%I:%M %p")
                d   = now.strftime("%B %d, %Y")
                self.speak(f"The current time is {t} and today is {d}.")

            # --- Music / YouTube ---
            elif tag == "music":
                # Extract the song/playlist query from the command
                q = re.sub(
                    r'\b(play|music|on|youtube|song|songs|playlist|start|please|any|a)\b',
                    '', command
                ).strip()
                if not q:
                    q = "trending songs"
                self.safe_call_eel("update_knowledge", "Media Control",
                                   f"Streaming: {q}")
                self.speak(response)
                url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(q)}"
                webbrowser.open(url)

            # --- Weather ---
            elif tag == "weather":
                self.speak(response)
                webbrowser.open("https://www.google.com/search?q=weather+today")

            # --- Web / Google Search ---
            elif tag == "search":
                q = re.sub(
                    r'\b(search|for|on|google|internet|web|find|information|look|up|this)\b',
                    '', command
                ).strip()
                if not q:
                    q = command
                self.safe_call_eel("update_knowledge", "Google Search",
                                   f"Query: {q}")
                self.speak(response)
                webbrowser.open(
                    f"https://www.google.com/search?q={urllib.parse.quote(q)}"
                )

            # --- Wikipedia ---
            elif tag == "wikipedia":
                # Strip navigation words to isolate the search topic
                q = re.sub(
                    r'\b(wikipedia|search|for|tell|from|about|open|wiki|find|on|me)\b',
                    '', command
                ).strip()
                self.speak(response)
                if q:
                    try:
                        import wikipedia as wiki_lib
                        results = wiki_lib.summary(q, sentences=2)
                        self.safe_call_eel("update_knowledge",
                                           f"Wikipedia: {q.title()}", results)
                        self.speak(f"According to Wikipedia: {results}")
                    except Exception:
                        self.safe_call_eel("update_knowledge", "Data Error",
                                           "No Wikipedia entry found.")
                        self.speak("I couldn't find an exact Wikipedia article for that.")
                else:
                    self.speak("What subject should I look up on Wikipedia?")

            # --- Open Application / Website ---
            elif tag == "open_app":
                app_name = re.sub(
                    r'\b(open|launch|start|application|browser|the)\b', '', command
                ).strip()

                # Map of website keywords → URLs
                web_map = {
                    "google":    "https://www.google.com",
                    "youtube":   "https://www.youtube.com",
                    "instagram": "https://www.instagram.com",
                    "facebook":  "https://www.facebook.com",
                    "twitter":   "https://www.x.com",
                    "github":    "https://www.github.com",
                    "linkedin":  "https://www.linkedin.com",
                    "whatsapp":  "https://web.whatsapp.com",
                    "gmail":     "https://mail.google.com",
                    "maps":      "https://maps.google.com",
                    "zoom":      "https://zoom.us",
                    "amazon":    "https://www.amazon.in",
                    "flipkart":  "https://www.flipkart.com",
                }
                # Map of desktop app keywords → Windows executables
                app_map = {
                    "notepad":     "notepad",
                    "calculator":  "calc",
                    "paint":       "mspaint",
                    "word":        "winword",
                    "excel":       "excel",
                    "powerpoint":  "powerpnt",
                    "vscode":      "code",
                    "code":        "code",
                    "explorer":    "explorer",
                    "task manager":"taskmgr",
                    "settings":    "ms-settings:",
                    "chrome":      "chrome",
                    "spotify":     "spotify",
                }

                self.speak(response)
                opened = False

                # Check websites first
                for kw, url in web_map.items():
                    if kw in app_name:
                        webbrowser.open(url)
                        opened = True
                        break

                # Then try desktop apps
                if not opened:
                    for kw, exe in app_map.items():
                        if kw in app_name:
                            if ":" in exe:   # protocol URI (e.g. ms-settings:)
                                os.system(f'start "" "{exe}"')
                            else:
                                os.system(exe)
                            opened = True
                            break

                if not opened and app_name:
                    # Last resort: try running it directly
                    os.system(app_name)

            # --- Food Delivery ---
            elif tag == "food":
                self.speak(response)
                if "zomato" in command:
                    webbrowser.open("https://www.zomato.com")
                else:
                    webbrowser.open("https://www.swiggy.com")

            # --- Shopping ---
            elif tag == "shopping":
                self.speak(response)
                if "myntra" in command:
                    webbrowser.open("https://www.myntra.com")
                elif "flipkart" in command:
                    webbrowser.open("https://www.flipkart.com")
                else:
                    webbrowser.open("https://www.amazon.in")

            # --- Exit / Goodbye ---
            elif tag == "exit":
                self.speak(response)
                global is_listening_global
                is_listening_global = False
                self.safe_call_eel("update_status", "Offline")
                self.safe_call_eel("update_query", "System Shutdown.")

            else:
                # Unknown tag returned by model (shouldn't happen often)
                self.speak(response)

        except Exception as e:
            self.safe_call_eel("update_log", "System", f"Fault: {e}")
            self.speak("A system error occurred. Please try again.")


# Init global assistant class
assistant = WebVoiceAssistant()

# Exportable JS command
@eel.expose
def toggle_voice_assistant():
    global is_listening_global
    if not is_listening_global:
        is_listening_global = True
        assistant.safe_call_eel("update_status", "Initializing...")
        threading.Thread(target=assistant.listen_loop, daemon=True).start()
    else:
        is_listening_global = False
        assistant.safe_call_eel("update_status", "System Standby")
        assistant.safe_call_eel("update_query", "Microphone deactivated.")

if __name__ == "__main__":
    try:
        # Use a stable host and port for better reliability on Windows
        # host='0.0.0.0' allows it to be reachable even if localhost mapping is odd
        eel.start('index.html', mode='edge', host='0.0.0.0', port=8000, size=(1150, 720))
    except Exception:
        try:
            eel.start('index.html', mode='default', host='0.0.0.0', port=8000, size=(1150, 720))
        except (SystemExit, MemoryError, KeyboardInterrupt):
            pass