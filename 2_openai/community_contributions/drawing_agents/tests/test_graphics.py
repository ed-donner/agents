from tools.graphic_canvas import HeadlessCanvas

GLOBAL_CANVAS = HeadlessCanvas()

def draw_house():
    """
    Draw a simple house: square body + triangular roof + door + window.
    Coordinates are in pixels on a 400x300 canvas.
    """
    # House body (rectangle)
    body = [
        (50, 180), (150, 180),
        (150, 260), (50, 260),
        (50, 180),
    ]
    GLOBAL_CANVAS.free_draw(body, color="#8B4513", brush_px=4)

    # Roof (triangle)
    roof = [
        (50, 180), (100, 130),
        (150, 180), (50, 180),
    ]
    GLOBAL_CANVAS.free_draw(roof, color="#A52A2A", brush_px=4)

    # Door
    door = [
        (90, 260), (110, 260),
        (110, 220), (90, 220),
        (90, 260),
    ]
    GLOBAL_CANVAS.free_draw(door, color="#3B2F2F", brush_px=3)

    # Window (small square)
    window = [
        (60, 200), (80, 200),
        (80, 220), (60, 220),
        (60, 200),
    ]
    GLOBAL_CANVAS.free_draw(window, color="#1E90FF", brush_px=2)


def draw_person():
    """
    Draw a stick figure person near the house.
    """
    # Head (circle approximated as polygonal loop)
    head = [
        (230, 150), (240, 145), (250, 150),
        (255, 160), (250, 170), (240, 175),
        (230, 170), (225, 160), (230, 150),
    ]
    GLOBAL_CANVAS.free_draw(head, color="#000000", brush_px=2)

    # Body
    body = [
        (240, 175), (240, 215),
    ]
    GLOBAL_CANVAS.free_draw(body, color="#000000", brush_px=3)

    # Arms
    arms = [
        (220, 195), (260, 195),
    ]
    GLOBAL_CANVAS.free_draw(arms, color="#000000", brush_px=3)

    # Left leg
    left_leg = [
        (240, 215), (230, 245),
    ]
    GLOBAL_CANVAS.free_draw(left_leg, color="#000000", brush_px=3)

    # Right leg
    right_leg = [
        (240, 215), (250, 245),
    ]
    GLOBAL_CANVAS.free_draw(right_leg, color="#000000", brush_px=3)


def draw_dog():
    """
    Draw a simple dog shape: body, head, legs, and tail.
    """
    # Body (horizontal rectangle)
    body = [
        (280, 210), (330, 210),
        (340, 225), (285, 225),
        (280, 210),
    ]
    GLOBAL_CANVAS.free_draw(body, color="#654321", brush_px=3)

    # Head (small rectangle)
    head = [
        (330, 200), (350, 200),
        (350, 215), (330, 215),
        (330, 200),
    ]
    GLOBAL_CANVAS.free_draw(head, color="#654321", brush_px=3)

    # Legs (four short lines)
    front_leg = [
        (335, 225), (335, 245),
    ]
    back_leg = [
        (290, 225), (290, 245),
    ]
    mid_leg1 = [
        (300, 225), (300, 245),
    ]
    mid_leg2 = [
        (325, 225), (325, 245),
    ]
    GLOBAL_CANVAS.free_draw(front_leg, color="#654321", brush_px=3)
    GLOBAL_CANVAS.free_draw(back_leg, color="#654321", brush_px=3)
    GLOBAL_CANVAS.free_draw(mid_leg1, color="#654321", brush_px=3)
    GLOBAL_CANVAS.free_draw(mid_leg2, color="#654321", brush_px=3)

    # Tail
    tail = [
        (285, 210), (270, 200),
    ]
    GLOBAL_CANVAS.free_draw(tail, color="#654321", brush_px=3)


def main():
    # 1) Initialize a 400x300 canvas with light sky background
    GLOBAL_CANVAS.initialize(400, 300, background="#E0F7FF")

    # 2) Draw objects
    draw_house()
    draw_person()
    draw_dog()

    # 3) Save PNG and cleanup
    GLOBAL_CANVAS.save_and_cleanup("test_output.png")


if __name__ == "__main__":
    main()