import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import platform
import subprocess
import threading
import queue

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
        self.pinch_threshold = 5  # Number of consecutive frames to confirm pinch
        
        # Gesture state
        self.prev_gesture = None
        self.gesture_start_time = 0
        self.gesture_hold_time = 0.5  # seconds
        
        # Camera setup
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Command Queue for Background Execution (Fix Latency)
        self.cmd_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self.command_worker, daemon=True)
        self.worker_thread.start()
        
        # Acceleration logic
        self.gesture_hold_start = 0
        self.current_held_gesture = None
        self.last_cmd_time = 0
        self.last_hand_y = 0
        
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
        """Count number of extended fingers using distance-based logic (rotation-invariant)"""
        fingers = []
        wrist = landmarks[0]
        
        # Thumb: Use distance between thumb tip and pinky base (MCP)
        thumb_tip = landmarks[4]
        pinky_mcp = landmarks[17]
        thumb_dist = self.get_distance(thumb_tip, pinky_mcp)
        
        # Heuristic: if thumb is far from pinky base, it's extended
        # This works better across rotations than X-coordinate checks
        if thumb_dist > 0.15: 
            fingers.append(1)
        else:
            fingers.append(0)
        
        # Other fingers: Compare distance from Wrist to Tip vs Wrist to PIP
        finger_tips = [8, 12, 16, 20]
        finger_pips = [6, 10, 14, 18]
        
        for tip, pip in zip(finger_tips, finger_pips):
            dist_tip = self.get_distance(wrist, landmarks[tip])
            dist_pip = self.get_distance(wrist, landmarks[pip])
            
            if dist_tip > dist_pip:
                fingers.append(1)
            else:
                fingers.append(0)
        
        return sum(fingers)
    
    def detect_gesture(self, landmarks):
        """Detect hand gestures with improved exclusivity and state management"""
        # Get key points
        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]
        index_tip = landmarks[8]
        index_mcp = landmarks[5]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        wrist = landmarks[0]
        
        # Count fingers using distance-based logic
        fingers = []
        wrist_lm = landmarks[0]
        
        # Thumb
        thumb_dist = self.get_distance(landmarks[4], landmarks[17])
        thumb_open = 1 if thumb_dist > 0.15 else 0
        fingers.append(thumb_open)
        
        # Other fingers
        finger_tips = [8, 12, 16, 20]
        finger_pips = [6, 10, 14, 18]
        for tip, pip in zip(finger_tips, finger_pips):
            dist_tip = self.get_distance(wrist_lm, landmarks[tip])
            dist_pip = self.get_distance(wrist_lm, landmarks[pip])
            fingers.append(1 if dist_tip > dist_pip else 0)
        
        num_fingers = sum(fingers)
        index_open, middle_open, ring_open, pinky_open = fingers[1], fingers[2], fingers[3], fingers[4]

        # 1. Thumbs Up/Down (Volume)
        # ONLY if thumb is out and all other fingers are closed
        if fingers[0] == 1 and sum(fingers[1:]) == 0:
            if thumb_tip.y < thumb_mcp.y:
                return "thumbs_up"
            elif thumb_tip.y > thumb_mcp.y:
                return "thumbs_down"

        # 3. Palm Open/Close (Maximize/Minimize)
        if not hasattr(self, 'hand_state'):
            self.hand_state = "neutral"
        
        if num_fingers >= 4:
            if self.hand_state == "fist":
                self.hand_state = "open"
                return "palm_open"
            self.hand_state = "open"
        elif num_fingers == 0:
            if self.hand_state == "open":
                self.hand_state = "fist"
                return "palm_close"
            self.hand_state = "fist"
        elif num_fingers == 1 and index_open:
            self.hand_state = "neutral"

        # 4. Double Click (Exactly 3 Fingers: Index+Middle+Ring)
        if index_open and middle_open and ring_open and not pinky_open:
            if not getattr(self, 'last_double_state', False):
                self.last_double_state = True
                return "double_pinch"
            return "none"
        else:
            self.last_double_state = False

        # 5. Right Click (Exactly 2 Fingers: Index+Middle)
        if index_open and middle_open and not ring_open:
            if not getattr(self, 'last_right_state', False):
                self.last_right_state = True
                return "right_click"
            return "none"
        else:
            self.last_right_state = False

        # 6. Left Click/Drag (Pinch: Thumb + Index)
        # Use 3D distance between thumb and index tips
        thumb_index_dist = self.get_distance_3d(landmarks[4], landmarks[8])
        if thumb_index_dist < 0.05:
            self.pinch_frame_count += 1
            if self.pinch_frame_count >= self.pinch_threshold:
                if not self.last_pinch_state:
                    self.last_pinch_state = True
                    return "pinch"
                return "pinch_hold"
            return "none"
        
        # Handle release of left click/drag
        if self.last_pinch_state:
            self.last_pinch_state = False
            self.pinch_frame_count = 0
            return "pinch_release"

        # 6. Scroll (Exactly 4 fingers: Index+Middle+Ring+Pinky)
        if index_open and middle_open and ring_open and pinky_open and not fingers[0]:
            return "scroll"
        
        self.last_hand_y = wrist.y

        # 7. Move (Exactly 1 Finger: Index)
        if index_open and not middle_open and not ring_open and not pinky_open:
            return "move"

        return "none"
    
    def smooth_coordinates(self, x, y):
        """Smooth mouse movement"""
        smooth_x = self.prev_x + (x - self.prev_x) / self.smooth_factor
        smooth_y = self.prev_y + (y - self.prev_y) / self.smooth_factor
        self.prev_x, self.prev_y = smooth_x, smooth_y
        return int(smooth_x), int(smooth_y)
    
    def command_worker(self):
        """Background thread worker to execute system commands without blocking the main loop"""
        while True:
            try:
                cmd_type, action, amount = self.cmd_queue.get()
                if cmd_type == "volume":
                    self._do_change_volume(action, amount)
                elif cmd_type == "minimize":
                    self._do_minimize()
                elif cmd_type == "maximize":
                    self._do_maximize()
                elif cmd_type == "scroll":
                    pyautogui.scroll(int(amount))
                self.cmd_queue.task_done()
            except Exception as e:
                print(f"Worker error: {e}")

    def execute_gesture(self, gesture):
        """Handle gesture execution with background processing and 8x acceleration"""
        current_time = time.time()
        
        # 1. Acceleration Logic
        if gesture == self.current_held_gesture and gesture != "none":
            # Gesture is being held
            hold_duration = current_time - self.gesture_hold_start
            # If held for more than 1.5 seconds, use 8x multiplier
            multiplier = 8 if hold_duration > 1.5 else 1
        else:
            # New gesture started
            self.current_held_gesture = gesture
            self.gesture_hold_start = current_time
            multiplier = 1

        # 2. Command Throttling
        if gesture in ["thumbs_up", "thumbs_down", "palm_open", "palm_close", "scroll_up", "scroll_down"]:
            # Scrolling needs faster response for smoothness
            cooldown = 0.05 if "scroll" in gesture else 0.15
            
            if current_time - self.last_cmd_time > cooldown:
                self.last_cmd_time = current_time
                
                if gesture == "thumbs_up":
                    self.cmd_queue.put(("volume", "increase", 0.05 * multiplier))
                    print(f"Volume Up {'(x8)' if multiplier > 1 else ''}")
                
                elif gesture == "thumbs_down":
                    self.cmd_queue.put(("volume", "decrease", 0.05 * multiplier))
                    print(f"Volume Down {'(x8)' if multiplier > 1 else ''}")
                
                elif gesture == "palm_open":
                    self.cmd_queue.put(("maximize", None, None))
                    print("Maximize Window")
                
                elif gesture == "palm_close":
                    self.cmd_queue.put(("minimize", None, None))
                    print("Minimize Window")
                
                elif gesture == "scroll_up":
                    self.cmd_queue.put(("scroll", None, 150 * multiplier))
                    print(f"Scroll Up {'(x8)' if multiplier > 1 else ''}")
                
                elif gesture == "scroll_down":
                    self.cmd_queue.put(("scroll", None, -150 * multiplier))
                    print(f"Scroll Down {'(x8)' if multiplier > 1 else ''}")
            
            return
        
        # 3. Click execution (Drag Support)
        if gesture == "pinch":
            pyautogui.mouseDown(button='left')
            print("Left Click (Down)")
            return
        
        elif gesture == "pinch_release":
            pyautogui.mouseUp(button='left')
            print("Left Click (Release)")
            return
            
        elif gesture == "right_click":
            pyautogui.click(button='right')
            print("Right Click")
            return
            
        elif gesture == "double_pinch":
            pyautogui.doubleClick()
            print("Double Click")
            return
    
    def _do_change_volume(self, action, amount):
        """Internal volume control implementation"""
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
                    volume.SetMasterVolumeLevelScalar(min(current + amount, 1.0), None)
                else:
                    volume.SetMasterVolumeLevelScalar(max(current - amount, 0.0), None)
                    
            elif "Darwin" in system or "macOS" in system:
                step = int(amount * 100)
                if action == "increase":
                    subprocess.run(['osascript', '-e', f'set volume output volume (output volume of (get volume settings) + {step})'])
                else:
                    subprocess.run(['osascript', '-e', f'set volume output volume (output volume of (get volume settings) - {step})'])
                    
            elif "Linux" in system:
                step = int(amount * 100)
                if action == "increase":
                    subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', f'{step}%+'])
                else:
                    subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', f'{step}%-'])
        except Exception as e:
            print(f"Volume error: {e}")

    def _do_minimize(self): self.minimize_window()
    def _do_maximize(self): self.maximize_window()
    
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
        print("- Pinch (Thumb + Index): Left Click / Drag")
        print("- Two fingers up (Index + Middle): Right Click")
        print("- Three fingers up (Index + Middle + Ring): Double Click")
        print("- Four fingers up: Scroll (Upper box = Up, Lower box = Down)")
        print("- Thumbs Up: Volume increase")
        print("- Thumbs Down: Volume decrease")
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
            
            # Screen aspect ratio for box calculation
            screen_aspect = self.screen_width / self.screen_height
            
            # Calculate box dimensions centered in frame
            # Use 70% of the relevant dimension
            base_percent = 0.6
            # how much the box should be below from the top 
            from_top = 0.45
            if (w / h) > screen_aspect:
                # Frame is wider than screen
                box_h = h * base_percent
                box_w = box_h * screen_aspect
            else:
                # Frame is taller than screen
                box_w = w * base_percent
                box_h = box_w / screen_aspect
            
            x1_box = int((w - box_w) / 2)
            # Use from_top to position vertically (0.0 = top, 1.0 = bottom)
            y1_box = int((h - box_h) * from_top)
            y2_box = int(y1_box + box_h)
            x2_box = int(x1_box + box_w)
            
            # Draw boundary box (always visible)
            cv2.rectangle(frame, (x1_box, y1_box), (x2_box, y2_box), (255, 0, 0), 2)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Get landmarks
                    landmarks = hand_landmarks.landmark

                    # MANUALLY Draw hand landmarks with custom colors
                    # 1. Palm Connections (Yellow)
                    palm_conn = [
                        (0, 1), (1, 2), (2, 5), (5, 9), (9, 13), (13, 17), (17, 0), # Base of palm
                        (5, 0), (9, 0), (13, 0) # Connections to wrist for stability
                    ]
                    for start, end in palm_conn:
                        p1 = (int(landmarks[start].x * w), int(landmarks[start].y * h))
                        p2 = (int(landmarks[end].x * w), int(landmarks[end].y * h))
                        cv2.line(frame, p1, p2, (0, 255, 255), 2) # Yellow in BGR
                        
                    # 2. Finger Connections (Green)
                    fingers_conn = [
                        (2, 3), (3, 4), # Thumb
                        (5, 6), (6, 7), (7, 8), # Index
                        (9, 10), (10, 11), (11, 12), # Middle
                        (13, 14), (14, 15), (15, 16), # Ring
                        (17, 18), (18, 19), (19, 20) # Pinky
                    ]
                    for start, end in fingers_conn:
                        p1 = (int(landmarks[start].x * w), int(landmarks[start].y * h))
                        p2 = (int(landmarks[end].x * w), int(landmarks[end].y * h))
                        cv2.line(frame, p1, p2, (0, 255, 0), 2) # Green in BGR
                    
                    # 3. Draw Nodes (Dots)
                    for lm in landmarks:
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        cv2.circle(frame, (cx, cy), 4, (255, 255, 255), -1) # White dots
                    
                    # Get index finger tip position (clamped to box for mapping)
                    index_tip = landmarks[8]
                    
                    # Map finger coordinates from box space to screen space
                    # Use np.interp for clean mapping
                    raw_x = index_tip.x * w
                    raw_y = index_tip.y * h
                    
                    screen_x = np.interp(raw_x, (x1_box, x2_box), (0, self.screen_width))
                    screen_y = np.interp(raw_y, (y1_box, y2_box), (0, self.screen_height))
                    
                    # Clamp coordinates slightly inside the visible screen to prevent hiding
                    # Stay 5 pixels away from absolute edges for better visibility
                    screen_x = np.clip(screen_x, 5, self.screen_width - 5)
                    screen_y = np.clip(screen_y, 5, self.screen_height - 5)
                    
                    # Final cursor coordinates
                    x, y = int(screen_x), int(screen_y)
                    
                    # Draw virtual cursor indicator (reflects mapped desktop screen)
                    # This shows where the mouse is on your actual monitor within the blue box
                    indicator_x = int(np.interp(screen_x, (0, self.screen_width), (x1_box, x2_box)))
                    indicator_y = int(np.interp(screen_y, (0, self.screen_height), (y1_box, y2_box)))
                    cv2.circle(frame, (indicator_x, indicator_y), 8, (0, 0, 255), -1) # Red dot for virtual cursor
                    
                    # Detect gesture
                    gesture = self.detect_gesture(landmarks)
                    
                    # Special Case: scrolling with two regions
                    if gesture == "scroll":
                        # Split box into two 50% height regions
                        y_mid = (y1_box + y2_box) // 2
                        
                        # Draw the regions (red boxes) only when scrolling
                        # Upper box
                        cv2.rectangle(frame, (x1_box, y1_box), (x2_box, y_mid), (0, 0, 255), 2)
                        # Lower box
                        cv2.rectangle(frame, (x1_box, y_mid), (x2_box, y2_box), (0, 0, 255), 2)
                        
                        # Labels for the boxes
                        cv2.putText(frame, "Scroll Up", (x1_box + 5, y1_box + 25), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
                        cv2.putText(frame, "Scroll Down", (x1_box + 5, y_mid + 25), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
                        
                        # Determine direction based on virtual cursor position
                        if indicator_y < y_mid:
                            self.execute_gesture("scroll_up")
                        else:
                            self.execute_gesture("scroll_down")
                    
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
                    
                    # Move cursor if in move mode or clicking/dragging
                    if gesture in ["move", "pinch", "pinch_hold"]:
                        smooth_x, smooth_y = self.smooth_coordinates(x, y)
                        pyautogui.moveTo(smooth_x, smooth_y, duration=0)
                    
                    # Execute other gestures
                    elif gesture != "scroll":
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