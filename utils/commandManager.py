import re
import os
import subprocess
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


        if command in ["kc", "casey", "kay see", "kc mode", "dictation mode"]:
            self.start_dictation_mode()
            return True

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
            if not self.open_system_software(app):
                self.speak(f"no software in the name {app}")
            
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
        
        elif "close" in command:
            app = command.replace("close", "").strip()
            if not app or app == "window":
                self.close_window()
            elif not self.close_system_software(app):
                self.speak(f"no running software in the name {app}")
        
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

    def open_system_software(self, app_name):
        """Open system software by name"""
        # clean app name
        app_name = app_name.lower().strip()
        
        # 1. Try Windows Start Menu shortcuts
        paths = [
            os.path.join(os.environ.get('ProgramData', ''), r'Microsoft\Windows\Start Menu\Programs'),
            os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs')
        ]
        
        # Common apps mapping that might not be direct names
        common_apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe", 
            "paint": "mspaint.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "explorer": "explorer.exe",
            "task manager": "taskmgr.exe",
            "control panel": "control.exe",
            "vs code": "code",
            "visual studio code": "code"
        }
        
        if app_name in common_apps:
            try:
                os.startfile(common_apps[app_name])
                self.speak(f"Opening {app_name}")
                return True
            except:
                pass

        # Search in Start Menu
        found_matches = []
        app_name_nospace = app_name.replace(" ", "")
        
        for path in paths:
            if not os.path.exists(path):
                continue
                
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.lower().endswith(".lnk"):
                        try:
                            filename = file.lower().replace(".lnk", "")
                            filename_nospace = filename.replace(" ", "")
                            
                            # Exact match
                            if filename == app_name:
                                os.startfile(os.path.join(root, file))
                                self.speak(f"Opening {app_name}")
                                return True
                            
                            # Space-insensitive exact match (e.g. "antigravity" -> "Anti Gravity")
                            if app_name_nospace == filename_nospace:
                                os.startfile(os.path.join(root, file))
                                self.speak(f"Opening {app_name}")
                                return True
                            
                            # Partial match
                            if app_name in filename or app_name_nospace in filename_nospace:
                                found_matches.append((len(filename), os.path.join(root, file)))
                        except:
                            continue

        # If exact match not found, try the best partial match
        if found_matches:
            # Sort by length (shortest match likely most relevant)
            found_matches.sort(key=lambda x: x[0])
            try:
                os.startfile(found_matches[0][1])
                self.speak(f"Opening {app_name}")
                return True
            except:
                pass

        # 2. Try Windows Store Apps (e.g. WhatsApp, Calculator, Photos) via PowerShell
        try:
            # Get list of installed apps with their AppIDs
            ps_cmd = 'Get-StartApps | ConvertTo-Json'
            output = subprocess.check_output(['powershell', '-Command', ps_cmd], text=True)
            
            # Simple parsing of the JSON or text output
            import json
            apps = json.loads(output)
            
            app_name_nospace = app_name.replace(" ", "")
            
            for app in apps:
                name = app.get('Name', '').lower()
                appid = app.get('AppID', '')
                
                name_nospace = name.replace(" ", "")
                
                # Check for match
                if (app_name == name or 
                    app_name_nospace == name_nospace or 
                    app_name in name):
                    
                    self.speak(f"Opening {app.get('Name')}")
                    # Launch using shell:AppsFolder
                    subprocess.run(f'start shell:AppsFolder\\{appid}', shell=True)
                    return True
                    
        except Exception as e:
            # PowerShell method failed, continue to next method
            pass
                
        # Try direct command
        try:
            os.startfile(app_name)
            self.speak(f"Opening {app_name}")
            return True
        except:
            pass

        return False

    def list_available_software(self):
        """List all available software applications"""
        print("\n" + "="*60)
        print(f"{'SOFTWARE NAME':<30} | {'VOICE COMMAND':<30}")
        print("="*60)
        
        # 1. Common Apps
        common_apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe", 
            "paint": "mspaint.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "explorer": "explorer.exe",
            "task manager": "taskmgr.exe",
            "control panel": "control.exe",
            "vs code": "code",
            "visual studio code": "code"
        }
        
        print(f"\n[Common System Apps]")
        for name in common_apps:
            print(f"{name:<30} -> Say: \"open {name}\"")
            
        # 2. Start Menu Apps
        paths = [
            os.path.join(os.environ.get('ProgramData', ''), r'Microsoft\Windows\Start Menu\Programs'),
            os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs')
        ]
        
        print(f"\n[Installed Applications]")
        seen_apps = set()
        
        for path in paths:
            if not os.path.exists(path):
                continue
                
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.lower().endswith(".lnk"):
                        try:
                            # limit name length for cleaner output
                            name = file.replace(".lnk", "")
                            if name.lower() not in seen_apps:
                                print(f"{name:<30} -> Say: \"open {name}\"")
                                seen_apps.add(name.lower())
                        except:
                            continue
        print("="*60 + "\n")
        
        # 3. Running Apps (User-level only)
        print(f"\n[Currently Running Applications]")
        try:
            # Get list of running tasks
            cmd = 'tasklist /fi "STATUS eq RUNNING" /fo CSV /nh'
            output = subprocess.check_output(cmd, shell=True).decode('oem')  # decode using 'oem' for Windows
            
            # Common system processes to ignore
            ignore_list = [
                "svchost.exe", "ctfmon.exe", "explorer.exe", "csrss.exe", 
                "winlogon.exe", "services.exe", "lsass.exe", "smss.exe", 
                "wininit.exe", "spoolsv.exe", "taskhostw.exe", "RuntimeBroker.exe",
                "python.exe", "cmd.exe", "conhost.exe", "ApplicationFrameHost.exe",
                "System Idle Process", "System", "Registry", "Memory Compression",
                "SearchHost.exe", "StartMenuExperienceHost.exe", "ShellExperienceHost.exe",
                "TextInputHost.exe", "dllhost.exe", "sihost.exe", "fontdrvhost.exe",
                "audiodg.exe", "wlanext.exe", "dasHost.exe", "dwm.exe", "nvcontainer.exe"
            ]
            
            seen_running = set()
            for line in output.split('\n'):
                if not line.strip(): continue
                # Parse CSV line - name is the first element
                parts = line.split(',')
                if len(parts) > 0:
                    proc_name = parts[0].strip('"')
                    
                    # Filter out system processes and duplicates
                    if (proc_name not in ignore_list and 
                        not proc_name.lower().startswith("service") and
                        proc_name not in seen_running):
                        
                        clean_name = proc_name.replace(".exe", "")
                        print(f"{clean_name:<30} -> Say: \"close {clean_name}\"")
                        seen_running.add(proc_name)
        except Exception as e:
            print(f"Error listing running apps: {e}")
            
        print("="*60 + "\n")

    def close_system_software(self, app_name):
        """Close running software by name"""
        app_name = app_name.lower().strip()
        
        try:
            # 1. Get running processes to match name
            cmd = 'tasklist /fi "STATUS eq RUNNING" /fo CSV /nh'
            output = subprocess.check_output(cmd, shell=True).decode('oem')
            
            matches = []
            for line in output.split('\n'):
                if not line.strip(): continue
                parts = line.split(',')
                if len(parts) > 0:
                    proc_name = parts[0].strip('"')
                    proc_clean = proc_name.lower().replace(".exe", "")
                    
                    # Exact match
                    if app_name == proc_clean:
                        matches.append(proc_name)
                    # Partial match
                    elif app_name in proc_clean:
                        matches.append(proc_name)
            
            if matches:
                # Prioritize exact match or shortest match
                target = min(matches, key=len)
                os.system(f"taskkill /f /im \"{target}\"")
                self.speak(f"Closing {target.replace('.exe', '')}")
                return True
                
        except Exception as e:
            print(f"Error closing app: {e}")
            
        return False

    def start_dictation_mode(self):
        """Enter dictation mode where speech is typed directly"""
        self.speak("Dictation mode on")
        
        while True:
            # Check if listen method exists (it's in the child class VoiceAssistant)
            if hasattr(self, 'listen'):
                text = self.listen()
                if not text:
                    continue
                    
                # Check for exit command
                if text in ["kc end", "casey end", "kay see end", "stop dictation", "end dictation"]:
                    self.speak("Dictation mode off")
                    break
                
                # Type the text
                self.type_text(text)
            else:
                print("Error: listen method not found")
                break
    