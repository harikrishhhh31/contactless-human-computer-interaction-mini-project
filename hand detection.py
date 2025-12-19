import cv2
import mediapipe as mp

# Initialize Mediapipe Hand model
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

with mp_hands.Hands(
    max_num_hands=1,       # Detect only one hand (you can set 2 later)
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
) as hands:

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Flip the frame for natural movement (mirror effect)
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process frame with Mediapipe
        results = hands.process(rgb_frame)

        # Draw landmarks if hand detected
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        cv2.imshow("Hand Detection", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # Press ESC to quit
            break

cap.release()
cv2.destroyAllWindows()
