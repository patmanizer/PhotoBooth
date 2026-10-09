"""Hand gesture recognition."""


def is_finger_up(hand_landmarks, finger_tip, finger_pip):
    """Check whether a fingertip is above its PIP joint."""

    return (
        hand_landmarks[finger_tip].y
        < hand_landmarks[finger_pip].y
    )


def is_one_finger_up(hand_landmarks):
    """
    Detect one finger pointing upward.

    Uses hand-relative sizing to help detect the gesture
    when the hand is farther from the camera.
    """

    landmarks = hand_landmarks

    wrist = landmarks[0]
    index_tip = landmarks[8]
    index_pip = landmarks[6]
    index_mcp = landmarks[5]

    middle_up = is_finger_up(landmarks, 12, 10)
    ring_up = is_finger_up(landmarks, 16, 14)
    pinky_up = is_finger_up(landmarks, 20, 18)

    # Index finger must be extended.
    finger_extended = (
        index_tip.y < index_pip.y
        and index_pip.y < index_mcp.y
    )

    # Normalize finger extension against hand size.
    hand_size = (
        (landmarks[9].x - wrist.x) ** 2
        + (landmarks[9].y - wrist.y) ** 2
    ) ** 0.5

    if hand_size < 0.001:
        return False

    finger_length = index_mcp.y - index_tip.y

    # Adjust this threshold to change sensitivity.
    pointing_up = finger_length / hand_size > 0.6

    # Finger must point mostly upward.
    vertical_distance = abs(index_tip.y - index_mcp.y)
    horizontal_distance = abs(index_tip.x - index_mcp.x)

    pointing_vertical = (
        horizontal_distance
        < vertical_distance * 0.75
    )

    return (
        finger_extended
        and pointing_up
        and pointing_vertical
        and not middle_up
        and not ring_up
        and not pinky_up
    )


def is_two_fingers_up(hand_landmarks):
    """Detect the index and middle fingers raised."""

    index_up = is_finger_up(hand_landmarks, 8, 6)
    middle_up = is_finger_up(hand_landmarks, 12, 10)

    return index_up and middle_up


def is_three_fingers_up(hand_landmarks):
    """Detect the index, middle, and ring fingers raised."""

    index_up = is_finger_up(hand_landmarks, 8, 6)
    middle_up = is_finger_up(hand_landmarks, 12, 10)
    ring_up = is_finger_up(hand_landmarks, 16, 14)

    return index_up and middle_up and ring_up


def is_open_hand(hand_landmarks):
    """
    Detect an open palm facing the camera and pointing upward.

    Works with both left and right hands.
    """

    wrist = hand_landmarks[0]

    def distance_3d(a, b):
        return (
            (a.x - b.x) ** 2
            + (a.y - b.y) ** 2
            + (a.z - b.z) ** 2
        ) ** 0.5

    # --------------------------------------------------
    # 1. All four fingers must be extended.
    # --------------------------------------------------
    fingers = (
        (8, 6),
        (12, 10),
        (16, 14),
        (20, 18),
    )

    extended_fingers = 0

    for tip_index, pip_index in fingers:
        tip = hand_landmarks[tip_index]
        pip = hand_landmarks[pip_index]

        tip_distance = distance_3d(tip, wrist)
        pip_distance = distance_3d(pip, wrist)

        if tip_distance > pip_distance * 1.10:
            extended_fingers += 1

    if extended_fingers < 4:
        return False

    # --------------------------------------------------
    # 2. Thumb must be extended.
    # --------------------------------------------------
    thumb_tip = hand_landmarks[4]
    thumb_ip = hand_landmarks[3]

    if (
        distance_3d(thumb_tip, wrist)
        <= distance_3d(thumb_ip, wrist) * 1.05
    ):
        return False

    # --------------------------------------------------
    # 3. Palm must point upward.
    # --------------------------------------------------
    middle_tip = hand_landmarks[12]

    vertical_distance = wrist.y - middle_tip.y
    horizontal_distance = abs(wrist.x - middle_tip.x)

    if vertical_distance <= 0:
        return False

    if vertical_distance < horizontal_distance * 1.2:
        return False

    # --------------------------------------------------
    # 4. Palm must face toward or away from the camera.
    # --------------------------------------------------
    index_mcp = hand_landmarks[5]
    pinky_mcp = hand_landmarks[17]

    ax = index_mcp.x - wrist.x
    ay = index_mcp.y - wrist.y
    az = index_mcp.z - wrist.z

    bx = pinky_mcp.x - wrist.x
    by = pinky_mcp.y - wrist.y
    bz = pinky_mcp.z - wrist.z

    nx = ay * bz - az * by
    ny = az * bx - ax * bz
    nz = ax * by - ay * bx

    normal_length = (
        nx ** 2 + ny ** 2 + nz ** 2
    ) ** 0.5

    if normal_length == 0:
        return False

    facing_ratio = abs(nz) / normal_length

    return facing_ratio >= 0.35