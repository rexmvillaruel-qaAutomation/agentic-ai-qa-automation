
"""
Generate original pixel-art robot assets for the NiceGUI dashboard.

The script creates:
- robot_idle.png: one transparent idle frame
- robot_walk.png: six transparent walking frames in a horizontal sprite sheet

Each frame is exactly 64 x 64 pixels.
"""

from pathlib import Path

from PIL import Image, ImageDraw


# Define fixed frame dimensions for predictable CSS animations.
FRAME_SIZE = 64
WALK_FRAMES = 6

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Define the robot's futuristic blue-and-white color palette.
OUTLINE = "#17223D"
WHITE = "#E8F6FF"
SHADOW = "#90AFCB"
CYAN = "#35E5FF"
DARK = "#10243B"
BLUE = "#438FFF"


def draw_robot(step=0):
    """
    Draw one transparent robot frame.

    The step parameter changes arm and leg positions to simulate
    a walking cycle while preserving the robot's overall appearance.
    """
    image = Image.new(
        "RGBA",
        (FRAME_SIZE, FRAME_SIZE),
        (0, 0, 0, 0),
    )
    draw = ImageDraw.Draw(image)

    # Alternate limb positions across the walking cycle.
    poses = [
        (0, 0),
        (-3, 3),
        (-5, 5),
        (0, 0),
        (3, -3),
        (5, -5),
    ]
    arm_offset, leg_offset = poses[step % len(poses)]

    # Draw the antenna and its cyan indicator.
    draw.rectangle((30, 3, 33, 11), fill=OUTLINE)
    draw.rectangle((30, 3, 33, 6), fill=CYAN)

    # Draw the robot's rounded, silver head.
    draw.rounded_rectangle(
        (12, 10, 51, 38),
        radius=11,
        fill=WHITE,
        outline=OUTLINE,
        width=3,
    )

    # Add side-mounted blue headphones.
    draw.rounded_rectangle(
        (8, 19, 15, 31),
        radius=3,
        fill=BLUE,
        outline=OUTLINE,
        width=2,
    )
    draw.rounded_rectangle(
        (48, 19, 55, 31),
        radius=3,
        fill=BLUE,
        outline=OUTLINE,
        width=2,
    )

    # Draw the dark visor and glowing cyan eyes.
    draw.rounded_rectangle(
        (19, 16, 45, 33),
        radius=6,
        fill=DARK,
        outline=OUTLINE,
        width=2,
    )
    draw.rectangle((26, 22, 28, 27), fill=CYAN)
    draw.rectangle((36, 22, 38, 27), fill=CYAN)

    # Draw the compact body and chest indicator.
    draw.rounded_rectangle(
        (24, 38, 40, 52),
        radius=4,
        fill=WHITE,
        outline=OUTLINE,
        width=2,
    )
    draw.rectangle((30, 41, 34, 44), fill=CYAN)

    # Draw swinging arms for the walking frames.
    draw.rounded_rectangle(
        (17, 40 + arm_offset, 24, 50 + arm_offset),
        radius=2,
        fill=SHADOW,
        outline=OUTLINE,
        width=2,
    )
    draw.rounded_rectangle(
        (40, 40 - arm_offset, 47, 50 - arm_offset),
        radius=2,
        fill=SHADOW,
        outline=OUTLINE,
        width=2,
    )

    # Draw alternating legs and boots.
    draw.rectangle(
        (26 + leg_offset, 51, 30 + leg_offset, 57),
        fill=SHADOW,
    )
    draw.rectangle(
        (35 - leg_offset, 51, 39 - leg_offset, 57),
        fill=SHADOW,
    )
    draw.rounded_rectangle(
        (23 + leg_offset, 56, 31 + leg_offset, 60),
        radius=1,
        fill=BLUE,
        outline=OUTLINE,
    )
    draw.rounded_rectangle(
        (34 - leg_offset, 56, 42 - leg_offset, 60),
        radius=1,
        fill=BLUE,
        outline=OUTLINE,
    )

    return image


def draw_execute_frame(step: int):
    """
    Draw one frame of the robot typing at a workstation.

    The robot remains in a fixed position while its arms move
    alternately toward a keyboard, creating a looping work animation.
    """
    # Start with the existing robot to preserve its visual identity.
    image = draw_robot(0)
    draw = ImageDraw.Draw(image)

    # Create a small keyboard in front of the robot.
    draw.rounded_rectangle(
        (15, 53, 49, 61),
        radius=2,
        fill=DARK,
        outline=BLUE,
        width=2,
    )

    # Add cyan keyboard keys for a futuristic appearance.
    for x in range(20, 46, 6):
        draw.rectangle((x, 56, x + 2, 57), fill=CYAN)

    # Alternate the position of the robot's hands.
    # The movement repeats across four animation frames.
    hand_positions = [
        (43, 47),
        (48, 43),
        (43, 48),
        (48, 44),
    ]

    left_hand_y, right_hand_y = hand_positions[step % 4]

    # Draw the animated hands over the existing robot arms.
    draw.rounded_rectangle(
        (17, left_hand_y, 25, left_hand_y + 7),
        radius=2,
        fill=WHITE,
        outline=OUTLINE,
        width=2,
    )

    draw.rounded_rectangle(
        (39, right_hand_y, 47, right_hand_y + 7),
        radius=2,
        fill=WHITE,
        outline=OUTLINE,
        width=2,
    )

    return image


def draw_analyze_frame(step: int):
    """
    Draw one frame of the robot analyzing test results.

    The robot's visor and scanning indicator change across
    four frames to simulate reading a monitor.
    """
    image = draw_robot(0)
    draw = ImageDraw.Draw(image)

    # Create a small analysis monitor beside the robot.
    draw.rectangle(
        (43, 37, 62, 53),
        fill=OUTLINE,
        outline=BLUE,
        width=2,
    )
    draw.rectangle((46, 40, 59, 49), fill=DARK)

    # Show test-result lines on the monitor.
    draw.line((48, 43, 56, 43), fill=CYAN, width=2)
    draw.line((48, 47, 54, 47), fill=SHADOW, width=2)

    # Move a bright scan indicator down the monitor.
    scan_positions = [40, 42, 44, 46]
    scan_y = scan_positions[step % 4]
    draw.line((46, scan_y, 59, scan_y), fill=CYAN, width=1)

    # Animate the robot's visor as it processes the results.
    eye_positions = [22, 23, 24, 23]
    eye_y = eye_positions[step % 4]

    # Cover the original eyes before drawing the new eye position.
    draw.rectangle((24, 20, 40, 29), fill=DARK)
    draw.rectangle((26, eye_y, 28, eye_y + 4), fill=CYAN)
    draw.rectangle((36, eye_y, 38, eye_y + 4), fill=CYAN)

    return image


def draw_investigate_frame(step: int):
    """
    Draw one frame of the robot inspecting a test failure.

    The magnifying glass moves across four frames to simulate
    examining an error while keeping the robot's body consistent.
    """
    image = draw_robot(0)
    draw = ImageDraw.Draw(image)

    # Move the magnifying glass slightly between frames.
    positions = [
        (45, 35),
        (47, 32),
        (49, 35),
        (47, 38),
    ]
    glass_x, glass_y = positions[step % len(positions)]

    # Draw the magnifying glass handle and circular lens.
    draw.line(
        (glass_x - 4, glass_y + 5, glass_x - 10, glass_y + 12),
        fill=SHADOW,
        width=3,
    )
    draw.ellipse(
        (glass_x - 5, glass_y - 5, glass_x + 5, glass_y + 5),
        fill=DARK,
        outline=CYAN,
        width=2,
    )

    # Draw a small error indicator inside the lens.
    draw.line(
        (glass_x - 2, glass_y - 2, glass_x + 2, glass_y + 2),
        fill="#FB7185",
        width=2,
    )
    draw.line(
        (glass_x + 2, glass_y - 2, glass_x - 2, glass_y + 2),
        fill="#FB7185",
        width=2,
    )

    return image

    
def draw_report_frame(step: int):
    """
    Draw one frame of the robot preparing a test report.

    Report lines appear progressively across four frames
    to simulate writing an execution summary.
    """
    image = draw_robot(0)
    draw = ImageDraw.Draw(image)

    # Draw a small report document beside the robot.
    draw.rectangle(
        (43, 32, 61, 56),
        fill=WHITE,
        outline=OUTLINE,
        width=2,
    )

    # Add a colored heading at the top of the report.
    draw.rectangle(
        (47, 36, 57, 39),
        fill=BLUE,
    )

    # Reveal more report lines as the animation progresses.
    report_lines = [
        (43, 53),
        (47, 53),
        (51, 53),
        (55, 53),
    ]

    visible_lines = (step % 4) + 1

    for index in range(visible_lines):
        y = report_lines[index][0]

        draw.line(
            (47, y, 57, y),
            fill=CYAN if index == visible_lines - 1 else SHADOW,
            width=2,
        )

    # Animate a small writing indicator.
    indicator_x = [47, 50, 53, 56][step % 4]

    draw.rectangle(
        (indicator_x, 54, indicator_x + 2, 55),
        fill=BLUE,
    )

    return image

def generate_assets():
    """
    Save idle and walking PNG assets.

    The walking sprite sheet arranges six frames horizontally,
    allowing CSS to switch frames using background-position.
    """
    idle = draw_robot()
    idle.save(ASSETS_DIR / "robot_idle.png")

    sheet = Image.new(
        "RGBA",
        (FRAME_SIZE * WALK_FRAMES, FRAME_SIZE),
        (0, 0, 0, 0),
    )

    for index in range(WALK_FRAMES):
        frame = draw_robot(index)
        sheet.paste(frame, (index * FRAME_SIZE, 0))

    sheet.save(ASSETS_DIR / "robot_walk.png")


    # Generate a four-frame typing animation for the Execute station.
    # Each frame uses the same 64x64 dimensions as the idle robot.
    execute_frames = 4

    execute_sheet = Image.new(
        "RGBA",
        (FRAME_SIZE * execute_frames, FRAME_SIZE),
        (0, 0, 0, 0),
    )

    for index in range(execute_frames):
        frame = draw_execute_frame(index)
        execute_sheet.paste(frame, (index * FRAME_SIZE, 0))

    execute_sheet.save(ASSETS_DIR / "robot_execute.png")

    
    # Generate a four-frame animation for test-result analysis.
    analyze_frames = 4

    analyze_sheet = Image.new(
        "RGBA",
        (FRAME_SIZE * analyze_frames, FRAME_SIZE),
        (0, 0, 0, 0),
    )

    for index in range(analyze_frames):
        frame = draw_analyze_frame(index)
        analyze_sheet.paste(frame, (index * FRAME_SIZE, 0))

    analyze_sheet.save(ASSETS_DIR / "robot_analyze.png")

    
    # Generate four frames of the robot investigating a failure.
    investigate_frames = 4

    investigate_sheet = Image.new(
        "RGBA",
        (FRAME_SIZE * investigate_frames, FRAME_SIZE),
        (0, 0, 0, 0),
    )

    for index in range(investigate_frames):
        frame = draw_investigate_frame(index)
        investigate_sheet.paste(
            frame,
            (index * FRAME_SIZE, 0),
        )

    investigate_sheet.save(
        ASSETS_DIR / "robot_investigate.png"
    )

    print(
        f"Investigate: {ASSETS_DIR / 'robot_investigate.png'}"
    )

    
    # Generate four frames of the robot writing a test report.
    report_frames = 4

    report_sheet = Image.new(
        "RGBA",
        (FRAME_SIZE * report_frames, FRAME_SIZE),
        (0, 0, 0, 0),
    )

    for index in range(report_frames):
        frame = draw_report_frame(index)

        report_sheet.paste(
            frame,
            (index * FRAME_SIZE, 0),
        )

    report_sheet.save(
        ASSETS_DIR / "robot_report.png"
    )

    print(
        f"Report: {ASSETS_DIR / 'robot_report.png'}"
    )


    print(f"Analyze: {ASSETS_DIR / 'robot_analyze.png'}")
    print(f"Execute: {ASSETS_DIR / 'robot_execute.png'}")
    print("Robot assets generated successfully!")
    print(f"Idle: {ASSETS_DIR / 'robot_idle.png'}")
    print(f"Walk: {ASSETS_DIR / 'robot_walk.png'}")



if __name__ == "__main__":
    generate_assets()
