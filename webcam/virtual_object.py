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

# Virtual object
box_x = 300
box_y = 200
box_size = 100

dragging = False

while True:

    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb)

    if results.multi_hand_landmarks:

        for hand_landmarks in results.multi_hand_landmarks:

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            h, w, _ = frame.shape

            thumb = hand_landmarks.landmark[4]
            index = hand_landmarks.landmark[8]

            thumb_x = int(thumb.x * w)
            thumb_y = int(thumb.y * h)

            index_x = int(index.x * w)
            index_y = int(index.y * h)

            distance = math.hypot(
                index_x - thumb_x,
                index_y - thumb_y
            )

            cv2.circle(frame, (index_x, index_y), 10, (0,255,0), -1)

            inside_box = (
                box_x < index_x < box_x + box_size
                and
                box_y < index_y < box_y + box_size
            )

            if distance < PINCH_THRESHOLD and inside_box:
                dragging = True

            if distance > PINCH_THRESHOLD:
                dragging = False

            if dragging:
                box_x = index_x - box_size // 2
                box_y = index_y - box_size // 2

    cv2.rectangle(
        frame,
        (box_x, box_y),
        (box_x + box_size, box_y + box_size),
        (0, 255, 0),
        -1
    )

    if dragging:

        cv2.putText(
            frame,
            "DRAGGING",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3
        )

    cv2.imshow(
        "AI3D Studio Virtual Object",
        frame
    )

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()