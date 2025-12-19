import re
from utils.systemMonitor import SystemMonitor
from utils.keyboardInput import KeyboardInput

class CommandManager(SystemMonitor , KeyboardInput):
    
    def __init__(self):
        super().__init__()
    
    def process_command(self, command):
        print("-"*10)
        print(f"Processing command: {command}")
        print("-"*10)
        """Process voice commands"""

        # if True or "hello" in command or "hi" in command:
        #     keyboard_input = KeyboardInput()
        #     keyboard_input.start_writing()
            

        if "play" in command and ("youtube" in command or "video" in command):
            # Extract video name
            query = command.replace("play", "").replace("on youtube", "").replace("youtube", "").replace("video", "").strip()
            if query:
                self.play_youtube_direct(query)
            else:
                self.speak("What would you like me to play?")
        
        elif "open" in command and "chrome" in command:
            # Extract what to open in Chrome
            query = command.replace("open", "").replace("in chrome", "").replace("chrome", "").strip()
            if query:
                self.open_in_chrome(query)
            else:
                self.open_application("chrome")
        
        elif "chrome" in command and ("search" in command or "google" in command):
            query = command.replace("chrome", "").replace("search", "").replace("google", "").strip()
            self.open_in_chrome(query)
            
        elif "open" in command:
            app = command.replace("open", "").strip()
            self.open_application(app)
            
        elif "search" in command or "google" in command:
            query = command.replace("search", "").replace("google", "").strip()
            self.search_web(query)
            
        elif "time" in command:
            self.get_time()
            
        elif "date" in command:
            self.get_date()
            
        elif "create file" in command:
            filename = command.replace("create file", "").strip()
            if filename:
                self.create_file(filename)
            else:
                self.speak("Please specify a filename")
                
        elif "list files" in command:
            self.list_files()
        
        elif "brightness" in command:
            if "increase" in command or "up" in command or "higher" in command:
                self.change_brightness("increase")
            elif "decrease" in command or "down" in command or "lower" in command:
                self.change_brightness("decrease")
            elif "set" in command or "to" in command:
                # Extract number from command
                match = re.search(r'\d+', command)
                if match:
                    value = int(match.group())
                    self.change_brightness("set", value)
                else:
                    self.speak("Please specify a brightness level")
            else:
                self.speak("Please specify increase, decrease, or set brightness")
        
        elif "volume" in command or "sound" in command:
            if "increase" in command or "up" in command or "higher" in command or "louder" in command:
                self.change_volume("increase")
            elif "decrease" in command or "down" in command or "lower" in command or "quieter" in command:
                self.change_volume("decrease")
            elif "mute" in command:
                self.change_volume("mute")
            elif "unmute" in command:
                self.change_volume("unmute")
            elif "set" in command or "to" in command:
                # Extract number from command
                match = re.search(r'\d+', command)
                if match:
                    value = int(match.group())
                    self.change_volume("set", value)
                else:
                    self.speak("Please specify a volume level")
            else:
                self.speak("Please specify increase, decrease, mute, or set volume")
        
        elif "minimize" in command or ("minimise" in command):
            self.minimize_window()
        
        elif "maximize" in command or ("maximise" in command) or "full screen" in command:
            self.maximize_window()
        
        elif "close window" in command:
            self.close_window()
        
        elif "switch window" in command or "next window" in command or "change window" in command:
            self.switch_window()
            
        elif "shutdown" in command:
            self.shutdown_system()
            
        elif "stop" in command or "exit" in command or "quit" in command:
            self.speak("Goodbye!")
            return False
            
        else:
            self.speak("I'm not sure how to help with that")
        
        return True
    