"""Hand gesture recognition."""


def is_finger_up(hand_landmarks, finger_tip, finger_pip):
    """Check whether a fingertip is above its PIP joint."""

    return (
        hand_landmarks[finger_tip].y
        < hand_landmarks[finger_pip].y
    )


def is_thumb_extended(hand_landmarks):
    """Check for thumb extension along the palm's thumb-side axis."""

    index_mcp = hand_landmarks[5]
    pinky_mcp = hand_landmarks[17]
    thumb_ip = hand_landmarks[3]
    thumb_tip = hand_landmarks[4]

    palm_axis = (
        index_mcp.x - pinky_mcp.x,
        index_mcp.y - pinky_mcp.y,
        index_mcp.z - pinky_mcp.z,
    )
    palm_width = sum(component ** 2 for component in palm_axis) ** 0.5
    if palm_width < 0.001:
        return False

    tip_from_ip = (
        thumb_tip.x - thumb_ip.x,
        thumb_tip.y - thumb_ip.y,
        thumb_tip.z - thumb_ip.z,
    )
    outward_extension = sum(
        thumb_component * palm_component
        for thumb_component, palm_component in zip(
            tip_from_ip,
            palm_axis,
        )
    ) / palm_width

    return outward_extension > palm_width * 0.05


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

    if is_thumb_extended(landmarks):
        return False

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

    if is_thumb_extended(hand_landmarks):
        return False

    index_up = is_finger_up(hand_landmarks, 8, 6)
    middle_up = is_finger_up(hand_landmarks, 12, 10)
    ring_up = is_finger_up(hand_landmarks, 16, 14)
    pinky_up = is_finger_up(hand_landmarks, 20, 18)

    return index_up and middle_up and not ring_up and not pinky_up


def is_three_fingers_up(hand_landmarks):
    """Detect either supported three-finger combination."""

    if is_thumb_extended(hand_landmarks):
        return False

    index_up = is_finger_up(hand_landmarks, 8, 6)
    middle_up = is_finger_up(hand_landmarks, 12, 10)
    ring_up = is_finger_up(hand_landmarks, 16, 14)
    pinky_up = is_finger_up(hand_landmarks, 20, 18)

    return (
        (index_up and middle_up and ring_up and not pinky_up)
        or (not index_up and middle_up and ring_up and pinky_up)
    )


def get_raised_finger_count(hand_landmarks):
    """Return the supported raised-finger gesture count, if any."""

    if is_one_finger_up(hand_landmarks):
        return 1
    if is_two_fingers_up(hand_landmarks):
        return 2
    if is_three_fingers_up(hand_landmarks):
        return 3
    return None


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
    if not is_thumb_extended(hand_landmarks):
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