import cv2
import mediapipe as mp
import pyautogui
import math
pyautogui.FAILSAFE = False
# Initialize Mediapipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Screen size
screen_width, screen_height = pyautogui.size()

# Open webcam
cap = cv2.VideoCapture(0)

def distance(p1, p2):
    """Calculate Euclidean distance between two points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)  # Mirror image
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:

            # Draw hand landmarks on frame
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Get coordinates of index finger tip and thumb tip
            index_finger = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]

            x = int(index_finger.x * screen_width)
            y = int(index_finger.y * screen_height)

            # Move mouse
            pyautogui.moveTo(x, y)

            # Pinch detection
            thumb_x = int(thumb_tip.x * screen_width)
            thumb_y = int(thumb_tip.y * screen_height)
            pinch_distance = distance((x, y), (thumb_x, thumb_y))

            if pinch_distance < 40:  # Pinch threshold
                pyautogui.click()     # Single click
            elif pinch_distance < 20:  # Strong pinch for double click
                pyautogui.doubleClick()

    cv2.imshow("Hand Control", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
        break

cap.release()
cv2.destroyAllWindows()
