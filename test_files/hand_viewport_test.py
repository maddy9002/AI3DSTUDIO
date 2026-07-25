import cv2

from webcam.hand_tracker_class import HandTracker

tracker = HandTracker()

cap = cv2.VideoCapture(0)

while True:

    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    pos = tracker.get_hand_position(frame)

    if pos:

        x, y = pos

        x = (x - 0.5) * 2
        y = -(y - 0.5) * 2

        print(
            f"Viewport: {x:.2f}, {y:.2f}"
        )

    cv2.imshow(
        "Hand Test",
        frame
    )

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()