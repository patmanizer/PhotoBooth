"""OpenCV drawing utilities."""

import cv2


HAND_CONNECTIONS = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (13, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    (0, 17),
)


def draw_hand(frame, hand_landmarks):
    """Draw hand connections and landmark points."""

    height, width, _ = frame.shape

    # Draw connections.
    for start_index, end_index in HAND_CONNECTIONS:
        start = hand_landmarks[start_index]
        end = hand_landmarks[end_index]

        start_point = (
            int(start.x * width),
            int(start.y * height),
        )

        end_point = (
            int(end.x * width),
            int(end.y * height),
        )

        cv2.line(
            frame,
            start_point,
            end_point,
            (0, 255, 0),
            2,
        )

    # Draw landmarks.
    for landmark in hand_landmarks:
        point = (
            int(landmark.x * width),
            int(landmark.y * height),
        )

        cv2.circle(
            frame,
            point,
            4,
            (0, 255, 0),
            -1,
        )


def draw_gesture_progress(frame, hand_landmarks, progress):
    """Draw a circular gesture-hold progress indicator."""

    height, width, _ = frame.shape

    palm_landmarks = [
        hand_landmarks[index]
        for index in (0, 5, 9, 13, 17)
    ]

    palm_points = [
        (
            int(landmark.x * width),
            int(landmark.y * height),
        )
        for landmark in palm_landmarks
    ]

    center = (
        sum(point[0] for point in palm_points) // len(palm_points),
        sum(point[1] for point in palm_points) // len(palm_points),
    )

    radius = max(
        12,
        int(
            max(
                (
                    (point[0] - center[0]) ** 2
                    + (point[1] - center[1]) ** 2
                ) ** 0.5
                for point in palm_points
            ) * 0.8
        ),
    )

    thickness = max(5, radius // 2)

    cv2.circle(
        frame,
        center,
        radius,
        (80, 80, 80),
        thickness,
        cv2.LINE_AA,
    )

    if int(360 * progress) > 0:
        cv2.ellipse(
            frame,
            center,
            (radius, radius),
            0,
            -90,
            -90 + int(360 * progress),
            (0, 255, 0),
            thickness,
            cv2.LINE_AA,
        )