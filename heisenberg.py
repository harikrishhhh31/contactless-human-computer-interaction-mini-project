import speech_recognition as sr
import pyttsx3

from utils.commandManager import CommandManager
class VoiceAssistant (CommandManager):
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.setup_voice()
        
    def setup_voice(self):
        """Configure text-to-speech settings"""
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[0].id)
        self.engine.setProperty('rate', 175)
        self.engine.setProperty('volume', 0.9)
    
    def speak(self, text):
        """Convert text to speech"""
        print(f"Assistant: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
    
    """Listen for voice input and convert to text"""
    def listen(self):
        with sr.Microphone() as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5)
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text.lower()
            except sr.WaitTimeoutError:
                return ""
            except sr.UnknownValueError:
                self.speak("Sorry, I didn't catch that.")
                return ""
            except sr.RequestError:
                self.speak("Sorry, speech service is unavailable.")
                return ""
    
    
    def run(self):
        """Main loop"""
        self.speak("Voice assistant activated. How can I help you?")
        
        while True:
            command = self.listen()
            if command:
                if not self.process_command(command):
                    break

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()