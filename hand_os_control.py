import cv2
import mediapipe as mp
import pyautogui
import math
import time

# ------------------------- SETTINGS -------------------------
pyautogui.FAILSAFE = True  # Keep fail-safe enabled
SCREEN_BUFFER = 20         # Pixels from screen edges where cursor won't go
SMOOTHING = 0.2            # Cursor smoothing factor (0-1, higher = smoother)

screen_width, screen_height = pyautogui.size()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

prev_x, prev_y = 0, 0
click_state = False
double_click_time = 0.3
last_click_time = 0

# ------------------------- HELPER FUNCTIONS -------------------------
def distance(p1, p2):
    return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

def move_cursor(x, y):
    global prev_x, prev_y
    # Smooth the cursor movement
    new_x = prev_x + (x - prev_x) * SMOOTHING
    new_y = prev_y + (y - prev_y) * SMOOTHING

    # Keep cursor away from screen corners
    new_x = max(SCREEN_BUFFER, min(screen_width - SCREEN_BUFFER, new_x))
    new_y = max(SCREEN_BUFFER, min(screen_height - SCREEN_BUFFER, new_y))

    pyautogui.moveTo(new_x, new_y)
    prev_x, prev_y = new_x, new_y

# ------------------------- MAIN LOOP -------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)  # Mirror image
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Get tip of index finger and thumb
            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]

            # Convert to screen coordinates
            x = int(index_tip.x * screen_width)
            y = int(index_tip.y * screen_height)
            move_cursor(x, y)

            # Detect pinch for click
            pinch_distance = distance(
                (index_tip.x * frame.shape[1], index_tip.y * frame.shape[0]),
                (thumb_tip.x * frame.shape[1], thumb_tip.y * frame.shape[0])
            )

            if pinch_distance < 40:  # Adjust threshold if needed
                current_time = time.time()
                if current_time - last_click_time < double_click_time:
                    pyautogui.doubleClick()
                    last_click_time = 0
                else:
                    pyautogui.click()
                    last_click_time = current_time

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    cv2.imshow("Hand Control", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
        break

cap.release()
cv2.destroyAllWindows()
