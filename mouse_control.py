import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import platform
import subprocess

class GestureMouseController:
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Smoothing variables
        self.prev_x, self.prev_y = 0, 0
        self.smooth_factor = 5
        
        # Click detection
        self.click_threshold = 40
        self.is_clicking = False
        self.click_cooldown = 0
        self.last_pinch_state = False
        self.pinch_frame_count = 0
        self.pinch_threshold = 3  # Number of consecutive frames to confirm pinch
        
        # Gesture state
        self.prev_gesture = None
        self.gesture_start_time = 0
        self.gesture_hold_time = 0.5  # seconds
        
        # Camera setup
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Performance settings
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0
        
    def get_distance(self, point1, point2):
        """Calculate Euclidean distance between two points"""
        return np.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)
    
    def get_distance_3d(self, point1, point2):
        """Calculate 3D Euclidean distance between two points"""
        return np.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2 + (point1.z - point2.z)**2)
    
    def count_fingers(self, landmarks):
        """Count number of extended fingers"""
        fingers = []
        
        # Thumb
        if landmarks[4].x < landmarks[3].x:  # Right hand
            fingers.append(1)
        else:
            fingers.append(0)
        
        # Other fingers
        finger_tips = [8, 12, 16, 20]
        finger_pips = [6, 10, 14, 18]
        
        for tip, pip in zip(finger_tips, finger_pips):
            if landmarks[tip].y < landmarks[pip].y:
                fingers.append(1)
            else:
                fingers.append(0)
        
        return sum(fingers)
    
    def detect_gesture(self, landmarks):
        """Detect hand gestures"""
        # Get key points
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        index_tip = landmarks[8]
        index_mcp = landmarks[5]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        wrist = landmarks[0]
        
        # Calculate distances
        thumb_index_dist = self.get_distance(thumb_tip, index_tip)
        
        # Count fingers
        num_fingers = self.count_fingers(landmarks)
        
        # Thumbs Up Detection (Volume Up)
        # Thumb pointing up, other fingers closed
        if (thumb_tip.y < thumb_mcp.y < wrist.y and 
            index_tip.y > index_mcp.y and
            middle_tip.y > landmarks[10].y):
            return "thumbs_up"
        
        # Thumbs Down Detection (Volume Down)
        # Thumb pointing down, other fingers closed
        elif (thumb_tip.y > thumb_mcp.y > wrist.y and
              index_tip.y > index_mcp.y and
              middle_tip.y > landmarks[10].y):
            return "thumbs_down"
        
        # Palm Rotation Detection for Brightness
        # Calculate palm orientation using wrist and middle finger base
        palm_vector_x = landmarks[9].x - wrist.x
        palm_vector_y = landmarks[9].y - wrist.y
        
        # Check if palm is stationary (not rotating) for maximize/minimize
        if not hasattr(self, 'palm_stationary_start'):
            self.palm_stationary_start = time.time()
            self.last_palm_fingers = num_fingers
        
        # Detect palm state change (open to close or close to open)
        if abs(num_fingers - self.last_palm_fingers) >= 3:
            time_stationary = time.time() - self.palm_stationary_start
            
            # Palm opening (Maximize Window)
            if num_fingers >= 4 and self.last_palm_fingers <= 1 and time_stationary < 1.0:
                self.last_palm_fingers = num_fingers
                self.palm_stationary_start = time.time()
                return "palm_open"
            
            # Palm closing (Minimize Window)
            elif num_fingers <= 1 and self.last_palm_fingers >= 4 and time_stationary < 1.0:
                self.last_palm_fingers = num_fingers
                self.palm_stationary_start = time.time()
                return "palm_close"
        
        self.last_palm_fingers = num_fingers
        
        # Open palm detection (all fingers extended) for rotation
        if num_fingers >= 4:
            # Calculate angle of palm
            angle = np.arctan2(palm_vector_y, palm_vector_x) * 180 / np.pi
            
            # Store angle for rotation detection
            if not hasattr(self, 'prev_angle'):
                self.prev_angle = angle
                self.rotation_sum = 0
            
            angle_diff = angle - self.prev_angle
            
            # Handle angle wraparound
            if angle_diff > 180:
                angle_diff -= 360
            elif angle_diff < -180:
                angle_diff += 360
            
            self.rotation_sum += angle_diff
            self.prev_angle = angle
            
            # Only detect rotation if palm is stable (not just opened)
            if hasattr(self, 'palm_stationary_start'):
                time_stable = time.time() - self.palm_stationary_start
                if time_stable > 0.5:  # Palm must be open for 0.5s before rotation counts
                    # Clockwise rotation (increase brightness)
                    if self.rotation_sum > 15:
                        self.rotation_sum = 0
                        return "rotate_clockwise"
                    
                    # Counter-clockwise rotation (decrease brightness)
                    elif self.rotation_sum < -15:
                        self.rotation_sum = 0
                        return "rotate_counterclockwise"
        else:
            # Reset rotation tracking when palm closes
            if hasattr(self, 'prev_angle'):
                delattr(self, 'prev_angle')
                self.rotation_sum = 0
        
        # Pinch Detection (Click) - IMPROVED
        # Use 3D distance for better accuracy
        thumb_index_dist_3d = self.get_distance_3d(thumb_tip, index_tip)
        
        # More relaxed threshold for easier pinching
        is_pinched = thumb_index_dist_3d < 0.08
        
        if is_pinched:
            self.pinch_frame_count += 1
            
            # Confirm pinch after consecutive frames
            if self.pinch_frame_count >= self.pinch_threshold:
                if not self.last_pinch_state:
                    # New pinch detected
                    self.last_pinch_state = True
                    
                    # Check for double pinch
                    if not hasattr(self, 'last_pinch_time'):
                        self.last_pinch_time = time.time()
                        self.pinch_click_count = 1
                        return "pinch"
                    else:
                        time_since_last = time.time() - self.last_pinch_time
                        if time_since_last < 0.6:  # Double click window
                            self.pinch_click_count += 1
                            if self.pinch_click_count == 2:
                                self.pinch_click_count = 0
                                return "double_pinch"
                        else:
                            self.last_pinch_time = time.time()
                            self.pinch_click_count = 1
                            return "pinch"
                
                return "pinch_hold"
        else:
            # Reset when fingers separate
            self.pinch_frame_count = 0
            if self.last_pinch_state:
                self.last_pinch_state = False
                self.last_pinch_time = time.time()
        
        # Move: Index finger up only
        if num_fingers == 1 and landmarks[8].y < landmarks[6].y:
            return "move"
        
        return "none"
    
    def smooth_coordinates(self, x, y):
        """Smooth mouse movement"""
        smooth_x = self.prev_x + (x - self.prev_x) / self.smooth_factor
        smooth_y = self.prev_y + (y - self.prev_y) / self.smooth_factor
        self.prev_x, self.prev_y = smooth_x, smooth_y
        return int(smooth_x), int(smooth_y)
    
    def execute_gesture(self, gesture):
        """Execute the detected gesture"""
        current_time = time.time()
        
        # Immediate execution for some gestures
        if gesture in ["thumbs_up", "thumbs_down", "rotate_clockwise", "rotate_counterclockwise", 
                       "palm_open", "palm_close"]:
            if gesture == "thumbs_up":
                self.change_volume("increase")
                print("Volume Up")
            
            elif gesture == "thumbs_down":
                self.change_volume("decrease")
                print("Volume Down")
            
            elif gesture == "rotate_clockwise":
                self.change_brightness("increase")
                print("Brightness Up")
            
            elif gesture == "rotate_counterclockwise":
                self.change_brightness("decrease")
                print("Brightness Down")
            
            elif gesture == "palm_open":
                self.maximize_window()
                print("Maximize Window")
            
            elif gesture == "palm_close":
                self.minimize_window()
                print("Minimize Window")
            
            return
        
        # Improved click execution - immediate response
        if gesture == "pinch" and self.click_cooldown == 0:
            pyautogui.click()
            self.click_cooldown = 20
            print("Click")
            return
        
        elif gesture == "double_pinch" and self.click_cooldown == 0:
            pyautogui.doubleClick()
            self.click_cooldown = 25
            print("Double Click")
            return
    
    def change_volume(self, action):
        """Change system volume"""
        system = platform.platform()
        try:
            if "Windows" in system:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                
                current = volume.GetMasterVolumeLevelScalar()
                if action == "increase":
                    volume.SetMasterVolumeLevelScalar(min(current + 0.05, 1.0), None)
                else:
                    volume.SetMasterVolumeLevelScalar(max(current - 0.05, 0.0), None)
                    
            elif "Darwin" in system or "macOS" in system:
                if action == "increase":
                    subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume settings) + 5)'])
                else:
                    subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume settings) - 5)'])
                    
            elif "Linux" in system:
                if action == "increase":
                    subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', '5%+'])
                else:
                    subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', '5%-'])
        except Exception as e:
            print(f"Volume control error: {e}")
    
    def change_brightness(self, action):
        """Change screen brightness"""
        system = platform.platform()
        try:
            if "Windows" in system:
                if action == "increase":
                    subprocess.run(['powershell', '-Command', 
                        '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,((Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness + 5))'],
                        capture_output=True)
                else:
                    subprocess.run(['powershell', '-Command', 
                        '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,((Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness - 5))'],
                        capture_output=True)
                    
            elif "Darwin" in system or "macOS" in system:
                result = subprocess.run(['osascript', '-e', 'tell application "System Events" to get the brightness of display 1'],
                                      capture_output=True, text=True)
                current = float(result.stdout.strip())
                
                if action == "increase":
                    new_brightness = min(current + 0.05, 1.0)
                else:
                    new_brightness = max(current - 0.05, 0.0)
                    
                subprocess.run(['osascript', '-e', f'tell application "System Events" to set brightness of display 1 to {new_brightness}'])
                    
            elif "Linux" in system:
                result = subprocess.run(['xrandr', '--current'], capture_output=True, text=True)
                display = result.stdout.split('\n')[0].split()[0]
                
                result = subprocess.run(['xrandr', '--verbose'], capture_output=True, text=True)
                current = 1.0
                for line in result.stdout.split('\n'):
                    if 'Brightness:' in line:
                        current = float(line.split(':')[1].strip())
                        break
                
                if action == "increase":
                    new_brightness = min(current + 0.05, 1.0)
                else:
                    new_brightness = max(current - 0.05, 0.1)
                    
                subprocess.run(['xrandr', '--output', display, '--brightness', str(new_brightness)])
        except Exception as e:
            print(f"Brightness control error: {e}")
    
    def minimize_window(self):
        """Minimize the active window"""
        system_name = platform.system()
        try:
            if system_name == "Windows":
                try:
                    import pyautogui as pag
                    pag.hotkey('win', 'down')
                except ImportError:
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
                    
            elif system_name == "Darwin":
                subprocess.run(['osascript', '-e', 
                    'tell application "System Events" to set miniaturized of window 1 of (first process whose frontmost is true) to true'])
                
            elif system_name == "Linux":
                subprocess.run(['xdotool', 'getactivewindow', 'windowminimize'])
                
        except Exception as e:
            print(f"Minimize error: {e}")
    
    def maximize_window(self):
        """Maximize the active window"""
        system_name = platform.system()
        try:
            if system_name == "Windows":
                try:
                    import pyautogui as pag
                    pag.hotkey('win', 'up')
                except ImportError:
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
                    
            elif system_name == "Darwin":
                subprocess.run(['osascript', '-e', 
                    'tell application "System Events" to tell (first process whose frontmost is true) to set value of attribute "AXFullScreen" of window 1 to true'])
                
            elif system_name == "Linux":
                subprocess.run(['wmctrl', '-r', ':ACTIVE:', '-b', 'add,maximized_vert,maximized_horz'])
                
        except Exception as e:
            print(f"Maximize error: {e}")
    
    def run(self):
        """Main loop"""
        print("Gesture Mouse Controller Started!")
        print("\nGestures:")
        print("- Index finger up: Move cursor")
        print("- Pinch (thumb + index): Click")
        print("- Double Pinch: Double click")
        print("- Thumbs Up: Volume increase")
        print("- Thumbs Down: Volume decrease")
        print("- Open palm rotate clockwise: Brightness increase")
        print("- Open palm rotate counter-clockwise: Brightness decrease")
        print("- Open palm (fist to open): Maximize window")
        print("- Close palm (open to fist): Minimize window")
        print("\nPress 'q' to quit")
        
        while True:
            success, frame = self.cap.read()
            if not success:
                break
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            h, w, c = frame.shape
            
            # Convert to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame
            results = self.hands.process(rgb_frame)
            
            # Cooldown management
            if self.click_cooldown > 0:
                self.click_cooldown -= 1
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw hand landmarks
                    self.mp_draw.draw_landmarks(
                        frame, 
                        hand_landmarks, 
                        self.mp_hands.HAND_CONNECTIONS
                    )
                    
                    # Get landmarks
                    landmarks = hand_landmarks.landmark
                    
                    # Get index finger tip position
                    index_tip = landmarks[8]
                    x = int(index_tip.x * self.screen_width)
                    y = int(index_tip.y * self.screen_height)
                    
                    # Detect gesture
                    gesture = self.detect_gesture(landmarks)
                    
                    # Display gesture on screen
                    gesture_color = (0, 255, 0) if gesture == "move" else (0, 255, 255)
                    if gesture in ["pinch", "double_pinch"]:
                        gesture_color = (255, 0, 255)  # Pink for clicks
                    
                    cv2.putText(frame, f"Gesture: {gesture}", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, gesture_color, 2)
                    
                    # Show pinch distance for debugging
                    if hasattr(self, 'pinch_frame_count'):
                        cv2.putText(frame, f"Pinch: {self.pinch_frame_count}", (10, 70),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                    
                    # Move cursor if in move mode
                    if gesture == "move":
                        smooth_x, smooth_y = self.smooth_coordinates(x, y)
                        pyautogui.moveTo(smooth_x, smooth_y, duration=0)
                        
                        # Draw cursor position indicator
                        cv2.circle(frame, 
                                 (int(index_tip.x * w), int(index_tip.y * h)),
                                 10, (0, 255, 0), -1)
                    
                    # Execute other gestures
                    else:
                        self.execute_gesture(gesture)
            
            # Display frame
            cv2.imshow("Gesture Mouse Controller", frame)
            
            # Exit on 'q' press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Cleanup
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    controller = GestureMouseController()
    controller.run()