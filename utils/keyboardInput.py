import pyautogui
import speech_recognition as sr

class KeyboardInput:
   
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def type_text(self, text, interval=0.02):
        print(text)
        pyautogui.write(text, interval=interval)

    def start_writing(self):
        with sr.Microphone() as source:
            print("bala is Listening you ...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=20)
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {text}")
                self.type_text(text.lower())
            except sr.WaitTimeoutError:
                return ""
            except sr.UnknownValueError:
                self.speak("Sorry, I didn't catch that.")
                return ""
            except sr.RequestError:
                self.speak("Sorry, speech service is unavailable.")
                return ""
    