import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import platform
import subprocess
import threading
import queue
import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'mouse_settings.json')

DEFAULT_SETTINGS = {
    "cursor": {
        "smooth_factor": 5,
        "click_threshold": 40,
        "pinch_threshold": 3,
        "left_click_hold_delay": 0.3
    },
    "gesture": {
        "detection_confidence": 0.7,
        "tracking_confidence": 0.7,
        "hold_time": 0.5
    },
    "control": {
        "box_size": 0.6,
        "box_from_top": 0.45,
        "volume_step": 0.05,
        "scroll_amount": 150,
        "acceleration_threshold": 1.5,
        "acceleration_multiplier": 2
    }
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(DEFAULT_SETTINGS, f, indent=2)
        return DEFAULT_SETTINGS
    
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        return settings
    except (json.JSONDecodeError, IOError):
        return DEFAULT_SETTINGS

class GestureMouseController:
    def __init__(self):
        self.settings = load_settings()
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=self.settings["gesture"]["detection_confidence"],
            min_tracking_confidence=self.settings["gesture"]["tracking_confidence"]
        )
        
        self.screen_width, self.screen_height = pyautogui.size()
        
        self.prev_x, self.prev_y = 0, 0
        self.smooth_factor = self.settings["cursor"]["smooth_factor"]
        
        self.click_threshold = self.settings["cursor"]["click_threshold"]
        self.left_click_hold_delay = self.settings["cursor"].get("left_click_hold_delay", 0.3)
        self.is_clicking = False
        self.left_button_down = False
        self.click_cooldown = 0
        self.last_pinch_state = False
        self.pinch_frame_count = 0
        self.pinch_threshold = self.settings["cursor"]["pinch_threshold"]
        self.left_click_hold_start = 0
        
        self.prev_gesture = None
        self.gesture_start_time = 0
        self.gesture_hold_time = self.settings["gesture"]["hold_time"]
        
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.cmd_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self.command_worker, daemon=True)
        self.worker_thread.start()
        
        self.gesture_hold_start = 0
        self.current_held_gesture = None
        self.last_cmd_time = 0
        self.last_hand_y = 0
        
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0
        
    def get_distance(self, point1, point2):
        return np.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)
    
    def get_distance_3d(self, point1, point2):
        return np.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2 + (point1.z - point2.z)**2)
    
    def detect_gesture(self, landmarks):
        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]
        index_tip = landmarks[8]
        index_mcp = landmarks[5]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        wrist = landmarks[0]
        self.current_pinch_dist = self.get_distance_3d(thumb_tip, index_tip)
        
        fingers = []
        wrist_lm = landmarks[0]
        
        thumb_dist = self.get_distance(landmarks[4], landmarks[17])
        thumb_open = 1 if thumb_dist > 0.15 else 0
        fingers.append(thumb_open)
        
        finger_tips = [8, 12, 16, 20]
        finger_pips = [6, 10, 14, 18]
        for tip, pip in zip(finger_tips, finger_pips):
            dist_tip = self.get_distance(wrist_lm, landmarks[tip])
            dist_pip = self.get_distance(wrist_lm, landmarks[pip])
            fingers.append(1 if dist_tip > dist_pip else 0)
        
        num_fingers = sum(fingers)
        index_open, middle_open, ring_open, pinky_open = fingers[1], fingers[2], fingers[3], fingers[4]

        if fingers[0] == 1 and sum(fingers[1:]) == 0:
            if thumb_tip.y < thumb_mcp.y:
                return "thumbs_up"
            elif thumb_tip.y > thumb_mcp.y:
                return "thumbs_down"

        if not hasattr(self, 'pending_gesture'): self.pending_gesture = "none"
        if not hasattr(self, 'click_frame_count'): self.click_frame_count = 0

        current_candidate = "none"

        if index_open and middle_open and ring_open and not pinky_open:
            current_candidate = "double_pinch"
        elif index_open and middle_open and not ring_open:
            current_candidate = "right_click"
        if index_open and middle_open and ring_open and pinky_open and not fingers[0]:
            current_candidate = "scroll"
        elif index_open and fingers[0] and not middle_open and not ring_open and not pinky_open:
            current_candidate = "left_click"
        elif index_open and not fingers[0] and not middle_open and not ring_open and not pinky_open:
            current_candidate = "move"

        if current_candidate != self.pending_gesture:
            self.pending_gesture = current_candidate
            self.click_frame_count = 0
            if current_candidate in ["move", "none"]:
                return current_candidate
            return "none"

        self.click_frame_count += 1
        
        if current_candidate in ["move", "scroll", "none"]:
            return current_candidate

        if self.click_frame_count == self.pinch_threshold:
            if current_candidate == "left_click": self.last_left_state = True
            if current_candidate == "right_click": self.last_right_state = True
            if current_candidate == "double_pinch": self.last_double_state = True
            return current_candidate
        
        if self.click_frame_count > 0 and self.click_frame_count < self.pinch_threshold:
            return "clicking"

        if self.click_frame_count > self.pinch_threshold:
            return f"{current_candidate}_held"
            
        if current_candidate in ["none", "move"]:
            self.last_left_state = False
            self.last_right_state = False
            self.last_double_state = False

        return "none"
    
    def smooth_coordinates(self, x, y):
        smooth_x = self.prev_x + (x - self.prev_x) / self.smooth_factor
        smooth_y = self.prev_y + (y - self.prev_y) / self.smooth_factor
        self.prev_x, self.prev_y = smooth_x, smooth_y
        return int(smooth_x), int(smooth_y)
    
    def command_worker(self):
        while True:
            try:
                cmd_type, action, amount = self.cmd_queue.get()
                if cmd_type == "volume":
                    self._do_change_volume(action, amount)
                elif cmd_type == "scroll":
                    pyautogui.scroll(int(amount))
                self.cmd_queue.task_done()
            except:
                pass

    def execute_gesture(self, gesture):
        current_time = time.time()

        # left click transition handling (short click vs hold/release)
        if getattr(self, 'prev_gesture', None) == "left_click" and gesture != "left_click":
            elapsed = current_time - self.left_click_hold_start
            if self.left_button_down:
                pyautogui.mouseUp()
                self.left_button_down = False
            else:
                if elapsed < self.left_click_hold_delay:
                    pyautogui.click()
            self.left_click_hold_start = 0

        if gesture == "left_click" and getattr(self, 'prev_gesture', None) != "left_click":
            self.left_click_hold_start = current_time

        self.prev_gesture = gesture

        if gesture == self.current_held_gesture and gesture != "none":
            hold_duration = current_time - self.gesture_hold_start
            multiplier = self.settings["control"]["acceleration_multiplier"] if hold_duration > self.settings["control"]["acceleration_threshold"] else 1
        else:
            self.current_held_gesture = gesture
            self.gesture_hold_start = current_time
            multiplier = 1

        if gesture in ["thumbs_up", "thumbs_down", "scroll_up", "scroll_down"]:
            cooldown = 0.05 if "scroll" in gesture else 0.15
            
            if current_time - self.last_cmd_time > cooldown:
                self.last_cmd_time = current_time
                
                if gesture == "thumbs_up":
                    self.cmd_queue.put(("volume", "increase", self.settings["control"]["volume_step"] * multiplier))
                elif gesture == "thumbs_down":
                    self.cmd_queue.put(("volume", "decrease", self.settings["control"]["volume_step"] * multiplier))
                elif gesture == "scroll_up":
                    self.cmd_queue.put(("scroll", None, self.settings["control"]["scroll_amount"] * multiplier))
                elif gesture == "scroll_down":
                    self.cmd_queue.put(("scroll", None, -self.settings["control"]["scroll_amount"] * multiplier))
            
            return
        
        if gesture == "right_click":
            pyautogui.click(button='right')
            return
            
        elif gesture == "left_click":
            # Start tracking left click timing on first detection
            if self.current_held_gesture != "left_click":
                self.left_click_hold_start = current_time
            
            # Only trigger mouseDown after the hold delay threshold
            if not self.left_button_down:
                hold_elapsed = current_time - self.left_click_hold_start
                if hold_elapsed >= self.left_click_hold_delay:
                    pyautogui.mouseDown(button='left')
                    self.left_button_down = True
            return
            
        elif gesture == "double_pinch":
            pyautogui.doubleClick()
            return
    
    def _do_change_volume(self, action, amount):
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
        except:
            pass
    
    def run(self):
        while True:
            success, frame = self.cap.read()
            if not success:
                break
            
            frame = cv2.flip(frame, 1)
            h, w, c = frame.shape
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)

            if self.click_cooldown > 0:
                self.click_cooldown -= 1
            
            screen_aspect = self.screen_width / self.screen_height
            
            base_percent = self.settings["control"]["box_size"]
            from_top = self.settings["control"]["box_from_top"]
            if (w / h) > screen_aspect:
                box_h = h * base_percent
                box_w = box_h * screen_aspect
            else:
                box_w = w * base_percent
                box_h = box_w / screen_aspect
            
            x1_box = int((w - box_w) / 2)
            y1_box = int((h - box_h) * from_top)
            y2_box = int(y1_box + box_h)
            x2_box = int(x1_box + box_w)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    landmarks = hand_landmarks.landmark
                    index_tip = landmarks[8]
                    
                    raw_x = index_tip.x * w
                    raw_y = index_tip.y * h
                    
                    screen_x = np.interp(raw_x, (x1_box, x2_box), (0, self.screen_width))
                    screen_y = np.interp(raw_y, (y1_box, y2_box), (0, self.screen_height))
                    
                    screen_x = np.clip(screen_x, 5, self.screen_width - 5)
                    screen_y = np.clip(screen_y, 5, self.screen_height - 5)
                    
                    smooth_x, smooth_y = self.smooth_coordinates(int(screen_x), int(screen_y))
                    
                    gesture = self.detect_gesture(landmarks)
                    
                    if gesture == "scroll":
                        y_mid = (y1_box + y2_box) // 2
                        indicator_y = int(np.interp(smooth_y, (0, self.screen_height), (y1_box, y2_box)))
                        if indicator_y < y_mid:
                            self.execute_gesture("scroll_up")
                        else:
                            self.execute_gesture("scroll_down")
                    
                    if gesture in ["move", "none", "left_click", "left_click_held"]:
                        pyautogui.moveTo(smooth_x, smooth_y, duration=0)
                    
                    if self.left_button_down and gesture not in ["left_click", "left_click_held", "clicking"]:
                        pyautogui.mouseUp(button='left')
                        self.left_button_down = False

                    if gesture not in ["move", "none", "scroll"]:
                        if "clicking" not in gesture and "held" not in gesture:
                            self.execute_gesture(gesture)
            
            cv2.waitKey(1)
        
        self.cap.release()

if __name__ == "__main__":
    controller = GestureMouseController()
    controller.run()
