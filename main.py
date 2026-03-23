import threading
import speech_recognition as sr
import pyttsx3
import pywhatkit
import wikipedia
import webbrowser
import datetime
import os
import time
import re
import eel
import pythoncom  # Needed to prevent Threading crashes on Windows with pyttsx3

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
        if not command:
            return
            
        try:
            if command in ["hello", "hi", "hey", "hello jarvis", "hi jarvis", "hello aura", "hi aura"]:
                self.speak("Greetings. All systems are operating smoothly.")
            elif "how are you" in command:
                self.speak("I am functioning flawlessly. How may I assist?")
            elif "time" in command and "what" in command:
                current_time = datetime.datetime.now().strftime("%I:%M %p")
                self.speak(f"The current time is {current_time}.")
            elif "date" in command and "what" in command:
                current_date = datetime.datetime.now().strftime("%B %d, %Y")
                self.speak(f"Today is {current_date}.")
            
            # G. Wikipedia
            elif "wikipedia" in command:
                query = command.replace("wikipedia", "").replace("search", "").replace("for", "").strip()
                if query:
                    try:
                        self.safe_call_eel("update_knowledge", "Target: " + query.title(), "Fetching data from Wikipedia Servers...")
                        results = wikipedia.summary(query, sentences=3)
                        self.safe_call_eel("update_knowledge", "Wikipedia: " + query.title(), results)
                        self.speak("Data extraction complete. Sent to your intelligence panel.")
                        self.speak(results)
                    except Exception:
                        self.safe_call_eel("update_knowledge", "ERROR", "No definitive results matched.")
                        self.speak("Please provide a more specific query.")
                else:
                    self.speak("What subject shall I query on Wikipedia?")
                    
            # B. Web & Search
            elif "open google" in command:
                self.safe_call_eel("update_knowledge", "Web Automation", "Launching Google Web Interface...")
                self.speak("Accessing Google...")
                webbrowser.open("https://www.google.com")
            elif "open youtube" in command:
                self.safe_call_eel("update_knowledge", "Web Automation", "Launching YouTube Media Interface...")
                self.speak("Opening YouTube...")
                webbrowser.open("https://www.youtube.com")
            elif "search google for" in command or ("search" in command and "google" in command):
                query = re.sub(r'search google for|search for|search|google|on', '', command).strip()
                self.safe_call_eel("update_knowledge", "Web Search API", f"Executing query string: '{query}'")
                self.speak(f"Searching Google for {query}.")
                pywhatkit.search(query)
            elif "play" in command and "youtube" in command:
                query = command.replace("play", "").replace("youtube", "").replace("on", "").strip()
                self.safe_call_eel("update_knowledge", "Media Player", f"Streaming globally: '{query}'")
                self.speak(f"Routing {query} to YouTube.")
                pywhatkit.playonyt(query)

            # E. System Control
            elif "open notepad" in command:
                self.safe_call_eel("update_knowledge", "System Process", "PID Booted: NOTEPAD.EXE")
                self.speak("Accessing notepad.")
                os.system("notepad")
            elif "open calculator" in command:
                self.safe_call_eel("update_knowledge", "System Process", "PID Booted: CALC.EXE")
                self.speak("Deploying calculator.")
                os.system("calc")
            elif "exit assistant" in command or "quit" in command or "sleep" in command or "shut down" in command:
                self.speak("Powering down. Goodbye.")
                global is_listening_global
                is_listening_global = False
                self.safe_call_eel("update_status", "Offline")
                self.safe_call_eel("update_query", "System Shutdown.")

            else:
                self.speak("Command not recognized.")
                
        except Exception as e:
            self.safe_call_eel("update_log", "System", f"Fault: {e}")
            self.speak("A fatal error occurred.")


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