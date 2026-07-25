import cv2
import mediapipe as mp
import math

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)

PINCH_THRESHOLD = 80

while True:

    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    results = hands.process(rgb)

    if results.multi_hand_landmarks:

        for hand_landmarks in results.multi_hand_landmarks:

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            h, w, _ = frame.shape

            thumb_tip = hand_landmarks.landmark[4]
            index_tip = hand_landmarks.landmark[8]

            thumb_x = int(thumb_tip.x * w)
            thumb_y = int(thumb_tip.y * h)

            index_x = int(index_tip.x * w)
            index_y = int(index_tip.y * h)

            distance = math.hypot(
                index_x - thumb_x,
                index_y - thumb_y
            )

            cv2.circle(
                frame,
                (thumb_x, thumb_y),
                12,
                (0, 255, 0),
                -1
            )

            cv2.circle(
                frame,
                (index_x, index_y),
                12,
                (0, 255, 0),
                -1
            )

            cv2.line(
                frame,
                (thumb_x, thumb_y),
                (index_x, index_y),
                (255, 0, 0),
                3
            )

            cv2.putText(
                frame,
                f"Distance: {int(distance)}",
                (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2
            )

            if distance < PINCH_THRESHOLD:

                cv2.putText(
                    frame,
                    "PINCH DETECTED",
                    (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    3
                )

            else:

                cv2.putText(
                    frame,
                    "OPEN",
                    (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    3
                )

    cv2.imshow(
        "AI3D Studio Hand Tracker",
        frame
    )

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()

