# Voice Assistant Application

A completely functional desktop Voice Assistant built in Python. Features include voice recognition, text-to-speech, web search, social media automation, and PC control.

## Requirements
1. **Python 3.7+** installed on your Windows machine.
2. A fast **internet connection** (required for `SpeechRecognition` library to access Google engines).
3. A functional **microphone**.

---

## Setup Instructions

1. **Verify Location**
   Ensure `main.py` and `requirements.txt` are placed in the same project directory.

2. **Install Dependencies**
   Open your Command Prompt or Terminal, navigate to the project directory, and run the following command to automatically install all required packages:
   
   ```bash
   pip install -r requirements.txt
   ```
   
   *Tip: PyAudio can sometimes be tricky to install on Windows. If the above command fails to install `pyaudio`, run:*
   ```bash
   pip install pipwin
   pipwin install pyaudio
   ```

3. **Run the Application**
   Start your voice assistant with:
   ```bash
   python main.py
   ```

---

## How to use

1. Launch the application, and wait for the "Status: Sleeping" prompt.
2. Click the **"Start Listening"** button to activate the microphone.
3. The assistant will detect the **Wake Word** ("Hey Assistant"). You can say `"Hey Assistant, what is the time?"`.
4. You can optionally bypass the wake word and state commands directly while listening is active. All interactions will be logged in `command_history.log`.

### Example Commands:

- **Basic**: "hello", "what is the time?", "how are you?", "what is the date?"
- **Web & Search**: "Open Google", "Open YouTube", "Search Google for Python Tutorials", "Play [Song Name] on YouTube"
- **Social Media**: "Open Instagram", "Open Instagram profile of cristiano", "Open WhatsApp Web"
- **WhatsApp Tasks**: 
  - "Open WhatsApp chat for 1234567890" (Requires valid phone number with correct length)
  - "Send WhatsApp message to +1234567890 saying hello there"
- **Computer Controls**: "Open Notepad", "Open Calculator", "Open Default Browser"
- **Music**: "Play music" (Will pick up top trending songs on YT)
- **Knowledge**: "Wikipedia Artificial Intelligence"
- **Quit**: "Exit Assistant"

---

## Common Errors & Fixes
- **`ALSA lib` / `PyAudio` terminal warnings**: These are ignorable. PyAudio throws multiple verbose warnings upon loading devices, but it generally functions perfectly fine.
- **Microphone Error / No Sound Recognised**: Windows may be blocking terminal microphone access. Go to Settings > Privacy > Microphone, and allow desktop apps.
- **RequestError**: Check your internet connection. Speech-to-Text requires Google's internet APIs to transcribe audio perfectly.
- **Timeout or Delay**: Sometimes `PyWhatKit` functions take roughly 10-15 seconds to load website elements. Specifically, WhatsApp sending utilizes browser automation and may require you to already be logged in to WhatsApp Web on your default browser.
