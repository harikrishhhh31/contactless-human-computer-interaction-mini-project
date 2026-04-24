import datetime
import os
import platform
import subprocess
from urllib.parse import quote
import webbrowser
import pywhatkit

class SystemMonitor:
    def open_application(self, app_name):
        """Open applications based on OS"""
        system = platform.system()
        
        # Common websites that should open in browser
        websites = {
            "youtube": "https://www.youtube.com",
            "gmail": "https://mail.google.com",
            "facebook": "https://www.facebook.com",
            "twitter": "https://www.twitter.com",
            "instagram": "https://www.instagram.com",
            "reddit": "https://www.reddit.com",
            "github": "https://www.github.com",
            "linkedin": "https://www.linkedin.com",
            "netflix": "https://www.netflix.com",
            "spotify": "https://open.spotify.com",
            "whatsapp": "https://web.whatsapp.com",
            "discord": "https://discord.com/app",
            "perplexity": "https://www.perplexity.ai",
            "chatgpt": "https://chat.openai.com",
            "claude": "https://claude.ai"
        }
        
        # Check if it's a website first
        if app_name in websites:
            webbrowser.open(websites[app_name])
            self.speak(f"Opening {app_name}")
            return
        
        try:
            if system == "Windows":
                apps = {
                    "notepad": "notepad.exe",
                    "calculator": "calc.exe",
                    "paint": "mspaint.exe",
                    "explorer": "explorer.exe",
                    "chrome": "chrome.exe",
                    "firefox": "firefox.exe",
                    "edge": "msedge.exe",
                    "word": "winword.exe",
                    "excel": "excel.exe",
                    "powerpoint": "powerpnt.exe",
                    "vscode": "code.cmd",
                    "visual studio code": "code.cmd"
                }
                if app_name in apps:
                    os.startfile(apps[app_name])
                    self.speak(f"Opening {app_name}")
                else:
                    # Try to open as executable
                    os.startfile(app_name)
                    self.speak(f"Opening {app_name}")
                    
            elif system == "Darwin":  # macOS
                apps = {
                    "safari": "Safari",
                    "chrome": "Google Chrome",
                    "firefox": "Firefox",
                    "notes": "Notes",
                    "calculator": "Calculator",
                    "finder": "Finder",
                    "vscode": "Visual Studio Code",
                    "visual studio code": "Visual Studio Code",
                    "spotify": "Spotify",
                    "zoom": "zoom.us"
                }
                app = apps.get(app_name, app_name.title())
                subprocess.run(["open", "-a", app])
                self.speak(f"Opening {app_name}")
                
            elif system == "Linux":
                apps = {
                    "firefox": "firefox",
                    "chrome": "google-chrome",
                    "calculator": "gnome-calculator",
                    "files": "nautilus",
                    "vscode": "code",
                    "visual studio code": "code"
                }
                app = apps.get(app_name, app_name)
                subprocess.Popen([app])
                self.speak(f"Opening {app_name}")
        except Exception as e:
            self.speak(f"Couldn't open {app_name}. Please make sure it's installed")
    
    def search_web(self, query):
        """Search the web using default browser"""
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        self.speak(f"Searching for {query}")
    
    def open_in_chrome(self, query):
        """Open a URL or search in Chrome specifically"""
        chrome_path = None
        system = platform.system()
        
        # Find Chrome executable
        if system == "Windows":
            chrome_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
            ]
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_path = path
                    break
        elif system == "Darwin":
            chrome_path = "open -a /Applications/Google\ Chrome.app"
        elif system == "Linux":
            chrome_path = "google-chrome"
        
        if chrome_path:
            # Check if query is a URL or search term
            if "." in query and " " not in query:
                # Likely a URL
                url = query if query.startswith("http") else f"https://{query}"
            else:
                # Search query
                url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            
            try:
                if system == "Darwin":
                    subprocess.Popen([chrome_path.split()[0], chrome_path.split()[2], url])
                else:
                    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
                    webbrowser.get('chrome').open(url)
                self.speak(f"Opening in Chrome")
            except Exception as e:
                self.speak("Chrome not found. Using default browser")
                webbrowser.open(url)
        else:
            self.speak("Chrome not found. Using default browser")
            url = f"https://www.google.com/search?q={query}" if " " in query else f"https://{query}"
            webbrowser.open(url)
    
    def play_youtube(self, query):
        """Search and play a video on YouTube"""
        try:
            search_query = quote(query)
            url = f"https://www.youtube.com/results?search_query={search_query}"
            webbrowser.open(url)
            self.speak(f"Searching YouTube for {query}")
        except Exception as e:
            self.speak(f"Couldn't open YouTube. {str(e)}")
    
    def play_youtube_direct(self, query):
        """Play first YouTube video result directly (requires pywhatkit)"""
        try:
            self.speak(f"Playing {query} on YouTube")
            pywhatkit.playonyt(query)
        except ImportError:
            # Fallback to search method
            self.speak(f"Searching YouTube for {query}")
            self.play_youtube(query)
        except Exception as e:
            self.speak(f"Couldn't play video. {str(e)}")
    
    def get_time(self):
        """Get current time"""
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        self.speak(f"The time is {time_str}")
    
    def get_date(self):
        """Get current date"""
        now = datetime.datetime.now()
        date_str = now.strftime("%B %d, %Y")
        self.speak(f"Today is {date_str}")
    
    def create_file(self, filename):
        """Create a new file"""
        try:
            with open(filename, 'w') as f:
                f.write("")
            self.speak(f"Created file {filename}")
        except Exception as e:
            self.speak(f"Couldn't create file. {str(e)}")
    
    def list_files(self):
        """List files in current directory"""
        files = os.listdir()
        self.speak(f"There are {len(files)} items here")
        for f in files[:5]:
            print(f"- {f}")
    
    def shutdown_system(self):
        """Shutdown the computer"""
        self.speak("Shutting down the system")
        system = platform.system()
        if system == "Windows":
            os.system("shutdown /s /t 1")
        elif system == "Darwin":
            os.system("sudo shutdown -h now")
        elif system == "Linux":
            os.system("sudo shutdown -h now")
    
    def change_brightness(self, action, value=None):
        """Change screen brightness"""
        system = platform.system()
        try:
            if system == "Windows":
                # Use PowerShell to control brightness
                if action == "increase":
                    # Increase by 10%
                    subprocess.run(['powershell', '-Command', 
                        '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,((Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness + 10))'],
                        capture_output=True)
                    self.speak("Increasing brightness")
                elif action == "decrease":
                    # Decrease by 10%
                    subprocess.run(['powershell', '-Command', 
                        '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,((Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness - 10))'],
                        capture_output=True)
                    self.speak("Decreasing brightness")
                elif action == "set" and value:
                    subprocess.run(['powershell', '-Command', 
                        f'(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{value})'],
                        capture_output=True)
                    self.speak(f"Setting brightness to {value} percent")
                    
            elif system == "Darwin":  # macOS
                # Get current brightness
                result = subprocess.run(['osascript', '-e', 'tell application "System Events" to get the brightness of display 1'],
                                      capture_output=True, text=True)
                current = float(result.stdout.strip())
                
                if action == "increase":
                    new_brightness = min(current + 0.1, 1.0)
                    subprocess.run(['osascript', '-e', f'tell application "System Events" to set brightness of display 1 to {new_brightness}'])
                    self.speak("Increasing brightness")
                elif action == "decrease":
                    new_brightness = max(current - 0.1, 0.0)
                    subprocess.run(['osascript', '-e', f'tell application "System Events" to set brightness of display 1 to {new_brightness}'])
                    self.speak("Decreasing brightness")
                elif action == "set" and value:
                    brightness_val = value / 100.0
                    subprocess.run(['osascript', '-e', f'tell application "System Events" to set brightness of display 1 to {brightness_val}'])
                    self.speak(f"Setting brightness to {value} percent")
                    
            elif system == "Linux":
                # Using xrandr for Linux
                # Get display name
                result = subprocess.run(['xrandr', '--current'], capture_output=True, text=True)
                display = result.stdout.split('\n')[0].split()[0]
                
                # Get current brightness
                result = subprocess.run(['xrandr', '--verbose'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'Brightness:' in line:
                        current = float(line.split(':')[1].strip())
                        break
                
                if action == "increase":
                    new_brightness = min(current + 0.1, 1.0)
                    subprocess.run(['xrandr', '--output', display, '--brightness', str(new_brightness)])
                    self.speak("Increasing brightness")
                elif action == "decrease":
                    new_brightness = max(current - 0.1, 0.1)
                    subprocess.run(['xrandr', '--output', display, '--brightness', str(new_brightness)])
                    self.speak("Decreasing brightness")
                elif action == "set" and value:
                    brightness_val = value / 100.0
                    subprocess.run(['xrandr', '--output', display, '--brightness', str(brightness_val)])
                    self.speak(f"Setting brightness to {value} percent")
                    
        except Exception as e:
            self.speak(f"Couldn't change brightness. {str(e)}")
    
    def change_volume(self, action, value=None):
        """Change system volume"""
        system = platform.system()
        try:
            if system == "Windows":
                # Install: pip install pycaw comtypes
                try:
                    from ctypes import cast, POINTER
                    from comtypes import CLSCTX_ALL
                    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                    
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    volume = cast(interface, POINTER(IAudioEndpointVolume))
                    
                    if action == "increase":
                        current = volume.GetMasterVolumeLevelScalar()
                        volume.SetMasterVolumeLevelScalar(min(current + 0.1, 1.0), None)
                        self.speak("Increasing volume")
                    elif action == "decrease":
                        current = volume.GetMasterVolumeLevelScalar()
                        volume.SetMasterVolumeLevelScalar(max(current - 0.1, 0.0), None)
                        self.speak("Decreasing volume")
                    elif action == "set" and value:
                        volume.SetMasterVolumeLevelScalar(value / 100.0, None)
                        self.speak(f"Setting volume to {value} percent")
                    elif action == "mute":
                        volume.SetMute(1, None)
                        self.speak("Muting volume")
                    elif action == "unmute":
                        volume.SetMute(0, None)
                        self.speak("Unmuting volume")
                except ImportError:
                    self.speak("Please install pycaw: pip install pycaw comtypes")
                    
            elif system == "Darwin":  # macOS
                if action == "increase":
                    subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume settings) + 10)'])
                    self.speak("Increasing volume")
                elif action == "decrease":
                    subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume settings) - 10)'])
                    self.speak("Decreasing volume")
                elif action == "set" and value:
                    subprocess.run(['osascript', '-e', f'set volume output volume {value}'])
                    self.speak(f"Setting volume to {value} percent")
                elif action == "mute":
                    subprocess.run(['osascript', '-e', 'set volume with output muted'])
                    self.speak("Muting volume")
                elif action == "unmute":
                    subprocess.run(['osascript', '-e', 'set volume without output muted'])
                    self.speak("Unmuting volume")
                    
            elif system == "Linux":
                # Using amixer for Linux
                if action == "increase":
                    subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', '10%+'])
                    self.speak("Increasing volume")
                elif action == "decrease":
                    subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', '10%-'])
                    self.speak("Decreasing volume")
                elif action == "set" and value:
                    subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', f'{value}%'])
                    self.speak(f"Setting volume to {value} percent")
                elif action == "mute":
                    subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', 'mute'])
                    self.speak("Muting volume")
                elif action == "unmute":
                    subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', 'unmute'])
                    self.speak("Unmuting volume")
                    
        except Exception as e:
            self.speak(f"Couldn't change volume. {str(e)}")
    
    def target_window_under_cursor(self):
        """Find and focus the window directly under the mouse cursor"""
        system = platform.system()
        try:
            if system == "Windows":
                import win32gui
                import pyautogui
                # Get current cursor position
                pos = pyautogui.position()
                # Find window handle at that position
                hwnd = win32gui.WindowFromPoint((pos.x, pos.y))
                # If found, bring it to the foreground
                if hwnd:
                    # Handle child windows (like controls inside a window)
                    hwnd = win32gui.GetAncestor(hwnd, 2) # GA_ROOT
                    win32gui.SetForegroundWindow(hwnd)
                    return True
            
            elif system == "Darwin":  # macOS
                subprocess.run(['osascript', '-e', 
                    'tell application "System Events" to set frontmost of (first process whose frontmost is false and (count of windows) > 0) to true'])
                return True
                
            elif system == "Linux":
                # Use xdotool to get window under mouse and focus it
                result = subprocess.run(['xdotool', 'getmouselocation', '--shell'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if line.startswith('WINDOW='):
                        window_id = line.split('=')[1]
                        if window_id:
                            subprocess.run(['xdotool', 'windowactivate', window_id])
                            return True
        except Exception as e:
            print(f"Error targeting window: {e}")
        return False

    def minimize_window(self):
        """Minimize the window under the cursor"""
        self.target_window_under_cursor()
        system = platform.system()
        try:
            if system == "Windows":
                # Use pyautogui or win32gui
                try:
                    import pyautogui
                    pyautogui.hotkey('win', 'down')
                    self.speak("Minimizing window")
                except ImportError:
                    # Alternative using PowerShell
                    subprocess.run(['powershell', '-Command', 
                        '''Add-Type @"
                        using System;
                        using System.Runtime.InteropServices;
                        public class Window {
                            [DllImport("user32.dll")]
                            public static extern IntPtr GetForegroundWindow();
                            [DllImport("user32.dll")]
                            public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
                        }
"@
[Window]::ShowWindow([Window]::GetForegroundWindow(), 6)'''], capture_output=True)
                    self.speak("Minimizing window")
                    
            elif system == "Darwin":  # macOS
                subprocess.run(['osascript', '-e', 
                    'tell application "System Events" to set miniaturized of window 1 of (first process whose frontmost is true) to true'])
                self.speak("Minimizing window")
                
            elif system == "Linux":
                # Using xdotool
                subprocess.run(['xdotool', 'getactivewindow', 'windowminimize'])
                self.speak("Minimizing window")
                
        except Exception as e:
            self.speak(f"Couldn't minimize window. You may need to install pyautogui or xdotool")
    
    def maximize_window(self):
        """Maximize the window under the cursor"""
        self.target_window_under_cursor()
        system = platform.system()
        try:
            if system == "Windows":
                try:
                    import pyautogui
                    pyautogui.hotkey('win', 'up')
                    self.speak("Maximizing window")
                except ImportError:
                    # Alternative using PowerShell
                    subprocess.run(['powershell', '-Command', 
                        '''Add-Type @"
                        using System;
                        using System.Runtime.InteropServices;
                        public class Window {
                            [DllImport("user32.dll")]
                            public static extern IntPtr GetForegroundWindow();
                            [DllImport("user32.dll")]
                            public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
                        }
"@
[Window]::ShowWindow([Window]::GetForegroundWindow(), 3)'''], capture_output=True)
                    self.speak("Maximizing window")
                    
            elif system == "Darwin":  # macOS
                subprocess.run(['osascript', '-e', 
                    'tell application "System Events" to tell (first process whose frontmost is true) to set value of attribute "AXFullScreen" of window 1 to true'])
                self.speak("Maximizing window")
                
            elif system == "Linux":
                # Using wmctrl
                subprocess.run(['wmctrl', '-r', ':ACTIVE:', '-b', 'add,maximized_vert,maximized_horz'])
                self.speak("Maximizing window")
                
        except Exception as e:
            self.speak(f"Couldn't maximize window. You may need to install pyautogui or wmctrl")
    
    def close_window(self):
        """Close the window under the cursor"""
        self.target_window_under_cursor()
        system = platform.system()
        try:
            if system == "Windows":
                try:
                    import pyautogui
                    pyautogui.hotkey('alt', 'f4')
                    self.speak("Closing window")
                except ImportError:
                    subprocess.run(['powershell', '-Command', 
                        '(New-Object -ComObject WScript.Shell).SendKeys("%{F4}")'])
                    self.speak("Closing window")
                    
            elif system == "Darwin":  # macOS
                subprocess.run(['osascript', '-e', 
                    'tell application "System Events" to tell (first process whose frontmost is true) to set visible to false'])
                self.speak("Closing window")
                
            elif system == "Linux":
                subprocess.run(['xdotool', 'getactivewindow', 'windowclose'])
                self.speak("Closing window")
                
        except Exception as e:
            self.speak(f"Couldn't close window. You may need to install pyautogui or xdotool")
    
    def switch_window(self):
        """Switch between windows"""
        system = platform.system()
        try:
            if system == "Windows":
                try:
                    import pyautogui
                    pyautogui.hotkey('alt', 'tab')
                    self.speak("Switching window")
                except ImportError:
                    subprocess.run(['powershell', '-Command', 
                        '(New-Object -ComObject WScript.Shell).SendKeys("%{TAB}")'])
                    self.speak("Switching window")
                    
            elif system == "Darwin":  # macOS
                subprocess.run(['osascript', '-e', 
                    'tell application "System Events" to keystroke tab using command down'])
                self.speak("Switching window")
                
            elif system == "Linux":
                subprocess.run(['xdotool', 'key', 'alt+Tab'])
                self.speak("Switching window")
                
        except Exception as e:
            self.speak(f"Couldn't switch window. You may need to install pyautogui or xdotool")
    