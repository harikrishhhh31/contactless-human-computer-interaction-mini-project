import cv2
import mediapipe as mp
import pyautogui
import time
import math

# Initialize mediapipe hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2)
mp_draw = mp.solutions.drawing_utils

# Screen size
screen_width, screen_height = pyautogui.size()

# Camera
cap = cv2.VideoCapture(0)

# Smoothing cursor movement
prev_x, prev_y = 0, 0
smoothening = 7

def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape
    
    # Convert to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)
    
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            # Draw landmarks
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Get index finger tip
            x_tip = int(hand_landmarks.landmark[8].x * w)
            y_tip = int(hand_landmarks.landmark[8].y * h)
            
            # Map to screen coordinates
            screen_x = screen_width / w * x_tip
            screen_y = screen_height / h * y_tip
            
            # Smooth movement
            curr_x = prev_x + (screen_x - prev_x) / smoothening
            curr_y = prev_y + (screen_y - prev_y) / smoothening
            pyautogui.moveTo(curr_x, curr_y)
            prev_x, prev_y = curr_x, curr_y
            
            # Detect pinch (thumb tip 4 and index tip 8)
            thumb_tip = hand_landmarks.landmark[4]
            index_tip = hand_landmarks.landmark[8]
            dist = distance((thumb_tip.x, thumb_tip.y), (index_tip.x, index_tip.y))
            
            if dist < 0.03:  # Adjust threshold
                pyautogui.click()
                time.sleep(0.3)  # Avoid multiple clicks

    cv2.imshow("Hand Control", frame)
    
    if cv2.waitKey(1) & 0xFF == 27:  # Press ESC to exit
        break

cap.release()
cv2.destroyAllWindows()
