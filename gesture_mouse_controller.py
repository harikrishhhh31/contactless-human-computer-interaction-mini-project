import cv2
import mediapipe as mp
import pyautogui
import numpy as np
from collections import deque

# -------- CONFIGURATION --------
SMOOTHING = 1.5
SENSITIVITY = 0.5
HISTORY_LENGTH = 5
DEAD_ZONE = 2
CLICK_THRESHOLD = 40
DOUBLE_CLICK_THRESHOLD = 30
SCROLL_THRESHOLD = 50
PINCH_THRESHOLD = 40
CRUSH_THRESHOLD = 30

# Initialize pyautogui fail-safe
pyautogui.FAILSAFE = False

# Mediapipe hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Screen size
SCREEN_W, SCREEN_H = pyautogui.size()

# Position history for smoothing
positions = deque(maxlen=HISTORY_LENGTH)
prev_click = False
prev_double_click = False
selecting = False

# Start camera
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    if result.multi_hand_landmarks:
        hand = result.multi_hand_landmarks[0]

        # Landmarks
        thumb_tip = hand.landmark[mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        middle_tip = hand.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        ring_tip = hand.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
        pinky_tip = hand.landmark[mp_hands.HandLandmark.PINKY_TIP]
        wrist = hand.landmark[mp_hands.HandLandmark.WRIST]

        # Convert to screen coordinates
        x = int(index_tip.x * SCREEN_W * SENSITIVITY)
        y = int(index_tip.y * SCREEN_H * SENSITIVITY)

        # Smoothing
        positions.append((x, y))
        avg_x = int(np.mean([p[0] for p in positions]))
        avg_y = int(np.mean([p[1] for p in positions]))
        if positions:
            if abs(avg_x - positions[-1][0]) < DEAD_ZONE:
                avg_x = positions[-1][0]
            if abs(avg_y - positions[-1][1]) < DEAD_ZONE:
                avg_y = positions[-1][1]

        pyautogui.moveTo(avg_x, avg_y)

        # Distances
        dist_thumb_index = np.hypot((thumb_tip.x - index_tip.x) * SCREEN_W,
                                    (thumb_tip.y - index_tip.y) * SCREEN_H)
        dist_thumb_middle = np.hypot((thumb_tip.x - middle_tip.x) * SCREEN_W,
                                     (thumb_tip.y - middle_tip.y) * SCREEN_H)

        # -------- CLICK & DOUBLE CLICK --------
        if dist_thumb_index < CLICK_THRESHOLD:
            if not prev_click:
                pyautogui.click()
                prev_click = True
        else:
            prev_click = False

        if dist_thumb_middle < DOUBLE_CLICK_THRESHOLD:
            if not prev_double_click:
                pyautogui.doubleClick()
                prev_double_click = True
        else:
            prev_double_click = False

        # -------- SCROLL --------
        if len(positions) > 1:
            dy = positions[-1][1] - positions[0][1]
            if abs(dy) > SCROLL_THRESHOLD:
                pyautogui.scroll(-int(dy / 5))
                positions.clear()

        # -------- SELECTIVE COPY-PASTE --------
        # Pinch = select text
        if dist_thumb_index < PINCH_THRESHOLD:
            if not selecting:
                pyautogui.mouseDown()  # start selection
                selecting = True
        else:
            if selecting:
                pyautogui.mouseUp()  # end selection
                selecting = False

        # Crush = copy/paste
        dist_thumb_pinky = np.hypot((thumb_tip.x - pinky_tip.x) * SCREEN_W,
                                    (thumb_tip.y - pinky_tip.y) * SCREEN_H)
        if dist_thumb_pinky < CRUSH_THRESHOLD:
            pyautogui.hotkey('ctrl', 'c')  # copy if selection active
            pyautogui.hotkey('ctrl', 'v')  # paste at current cursor

        # -------- VOLUME CONTROL --------
        # Thumbs up = volume up
        if index_tip.y < wrist.y and thumb_tip.y < wrist.y:
            pyautogui.press('volumeup')
        # Thumbs down = volume down
        if index_tip.y > wrist.y and thumb_tip.y > wrist.y:
            pyautogui.press('volumedown')

        # -------- WINDOW CONTROL --------
        # Open/close hand = maximize/minimize
        if all(f.y < wrist.y for f in [thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip]):
            pyautogui.hotkey('win', 'up')  # maximize
        if all(f.y > wrist.y for f in [thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip]):
            pyautogui.hotkey('win', 'down')  # minimize

        # Draw landmarks
        mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

    cv2.imshow("Gesture Mouse Controller", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()
