"""OpenCV drawing utilities."""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .config import FONT_PATH


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


def _draw_centered_text(
    frame,
    text,
    center,
    font_size,
    color_bgr,
    max_width=None,
):
    """Draw centered text using the configured OpenType font."""

    font = ImageFont.truetype(FONT_PATH, font_size)
    if max_width is not None:
        text_width = font.getbbox(text)[2]
        if text_width > max_width:
            font_size = max(1, int(font_size * max_width / text_width))
            font = ImageFont.truetype(FONT_PATH, font_size)

    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    ImageDraw.Draw(image).text(
        center,
        text,
        font=font,
        fill=tuple(reversed(color_bgr)),
        anchor="mm",
    )
    frame[:] = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)


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


def draw_gesture_progress(
    frame,
    hand_landmarks,
    progress,
    finger_count,
):
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
        32,
        int(
            max(
                (
                    (point[0] - center[0]) ** 2
                    + (point[1] - center[1]) ** 2
                ) ** 0.5
                for point in palm_points
            ) * 1.25
        ),
    )

    thickness = max(6, radius // 5)

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

    if finger_count is not None:
        _draw_centered_text(
            frame,
            str(finger_count),
            center,
            max(32, int(radius * 1.5)),
            (255, 255, 255),
        )


def draw_capture_countdown(frame, prompt, countdown):
    """Display the photo prompt or countdown with a cinematic overlay."""

    height, width = frame.shape[:2]
    darkened_frame = frame.copy()
    cv2.rectangle(
        darkened_frame,
        (0, 0),
        (width, height),
        (0, 0, 0),
        -1,
    )
    cv2.addWeighted(darkened_frame, 0.58, frame, 0.42, 0, frame)

    white = (255, 255, 255)
    center_x = width // 2

    if countdown is None:
        _draw_centered_text(
            frame,
            prompt,
            (center_x, height // 2),
            72,
            white,
            max_width=int(width * 0.82),
        )

        return

    _draw_centered_text(
        frame,
        str(countdown),
        (center_x, height // 2),
        300,
        white,
        max_width=int(width * 0.65),
    )


def draw_steady_message(frame):
    """Show a steadying message while the camera takes a photo."""

    height, width = frame.shape[:2]
    frame[:] = (12, 12, 12)

    _draw_centered_text(
        frame,
        "STEADY!",
        (width // 2, height // 2),
        180,
        (255, 255, 255),
        max_width=int(width * 0.82),
    )