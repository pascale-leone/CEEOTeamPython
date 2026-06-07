"""
🟡 lego_easy_examples.py
========================
Fun example programs for kids using lego_easy!

Pick any example below, change MY_CARD (and MY_CARD etc.) to
the 4-digit number on YOUR Connection Card, and run it!
"""

from lego_easy import Motor, Robot, ColorSensor, Controller, wait
from lego_easy import COLOR_RED, COLOR_GREEN, COLOR_BLUE


# ══════════════════════════════════════════════
# EXAMPLE 1: Run a motor continuously 🔄
# ══════════════════════════════════════════════
def example_motor_continuous():
    MY_CARD = "3683"

    motor = Motor(MY_CARD, speed=50)

    # Just turn it on and let it spin!
    print("Starting motor... (runs until we call stop)")
    motor.start()
    wait(3)          # spin for 3 seconds
    motor.stop()

    wait(1)

    # Spin backward continuously
    print("Now spinning backward...")
    motor.start_backward()
    wait(2)
    motor.stop()

    motor.beep()
    motor.disconnect()


# ══════════════════════════════════════════════
# EXAMPLE 2: Spin a motor a set amount 📐
# ══════════════════════════════════════════════
def example_motor_measured():
    MY_CARD = "3683"

    motor = Motor(MY_CARD)

    print("Spinning forward one full turn...")
    motor.spin(degrees=360)     # one turn, then stops by itself
    wait(1)

    print("Spinning backward slowly...")
    motor.set_speed(25)
    motor.spin_backward(degrees=180)
    wait(1)

    print("Spinning fast for 2 seconds!")
    motor.set_speed(100)
    motor.spin_for(seconds=2)

    motor.beep()
    motor.disconnect()


# ══════════════════════════════════════════════
# EXAMPLE 3: Drive a robot in a square 🤖
# ══════════════════════════════════════════════
def example_drive_square():
    MY_CARD = "3683"

    robot = Robot(MY_CARD, speed=40)

    print("Driving in a square!")
    for side in range(4):
        print(f"  Side {side + 1}...")
        robot.forward(seconds=2)
        robot.turn_right(degrees=90)

    robot.beep()
    robot.light("green")
    wait(1)
    robot.disconnect()


# ══════════════════════════════════════════════
# EXAMPLE 4: Run robot forward until told to stop 🏎️
# ══════════════════════════════════════════════
def example_robot_run():
    MY_CARD = "3683"

    robot = Robot(MY_CARD, speed=40)

    print("Robot driving forward... (stops after 4 seconds)")
    robot.run()       # starts driving — keeps going!
    wait(4)           # let it drive for 4 seconds
    robot.stop()      # stop!

    wait(1)
    print("Now reversing...")
    robot.run_backward()
    wait(2)
    robot.stop()

    robot.disconnect()


# ══════════════════════════════════════════════
# EXAMPLE 5: Read the color sensor 🌈
# ══════════════════════════════════════════════
def example_read_color():
    MY_CARD = "3683"

    sensor = ColorSensor(MY_CARD)

    print("Reading colors for 5 seconds. Hold things up to the sensor!")
    for i in range(50):
        color      = sensor.read_color()
        brightness = sensor.read_brightness()
        print(f"  Color: {color:<15}  Brightness: {brightness}%")
        wait(0.1)

    sensor.disconnect()


# ══════════════════════════════════════════════
# EXAMPLE 6: Read the controller 🕹️
# ══════════════════════════════════════════════
def example_read_controller():
    MY_CARD = "3683"

    ctrl = Controller(MY_CARD)

    print("Move the levers! Reading for 10 seconds...")
    for i in range(100):   # 100 reads × 0.1s = 10 seconds
        left, right = ctrl.read_levers()
        # Build a little bar to visualize each lever
        l_bar = "█" * (abs(left)  // 10)
        r_bar = "█" * (abs(right) // 10)
        l_dir = "▲" if left  > 0 else ("▼" if left  < 0 else "●")
        r_dir = "▲" if right > 0 else ("▼" if right < 0 else "●")
        print(f"  Left {l_dir} {l_bar:<10} {left:>4}%    Right {r_dir} {r_bar:<10} {right:>4}%")
        wait(0.1)

    ctrl.disconnect()


# ══════════════════════════════════════════════
# EXAMPLE 7: Drive a robot with the controller! 🕹️🤖
# Left lever = left side speed, Right lever = right side speed
# ══════════════════════════════════════════════
def example_controller_drives_robot():
    ROBOT_SERIAL     = "1111"   # ← change to your robot's serial
    CTRL_SERIAL      = "2222"   # ← change to your controller's serial

    robot = Robot(ROBOT_SERIAL, speed=50)
    ctrl  = Controller(CTRL_SERIAL)

    print("🕹️ Use the levers to drive! (runs for 30 seconds)")
    print("   Both forward = drive forward")
    print("   Both backward = drive backward")
    print("   Left only = turn left")
    print("   Right only = turn right")
    print("   Both centered = stop")

    for i in range(300):         # 300 × 0.1s = 30 seconds
        ctrl.drive_robot(robot)  # one tick of controller driving
        wait(0.1)

    robot.stop()
    robot.disconnect()
    ctrl.disconnect()


# ══════════════════════════════════════════════
# EXAMPLE 8: Color-triggered robot 🚦
# Show green to go, red to stop!
# ══════════════════════════════════════════════
def example_color_robot():
    ROBOT_SERIAL  = "3683"
    SENSOR_SERIAL = "1234"   # ← change to your sensor's serial

    robot  = Robot(ROBOT_SERIAL, speed=40)
    sensor = ColorSensor(SENSOR_SERIAL)

    print("Show the sensor GREEN to go, RED to stop!")
    print("(Running for 30 seconds total)")

    import time as _time
    start   = _time.time()
    driving = False

    while _time.time() - start < 30:
        color = sensor.read_color()

        if color == COLOR_GREEN and not driving:
            print("🟢 Green — go!")
            robot.light("green")
            robot.beep()
            robot.run()       # keep driving until red
            driving = True

        elif color == COLOR_RED and driving:
            print("🔴 Red — stop!")
            robot.stop()
            robot.light("red")
            robot.beep()
            driving = False

        wait(0.1)

    robot.stop()
    robot.disconnect()
    sensor.disconnect()


# ══════════════════════════════════════════════
# EXAMPLE 9: Victory dance! 🎉
# ══════════════════════════════════════════════
def example_victory_dance():
    MY_CARD = "3683"

    robot = Robot(MY_CARD, speed=60)
    robot.victory_dance()
    robot.disconnect()


# ──────────────────────────────────────────────
# RUN ONE EXAMPLE HERE ↓
# ──────────────────────────────────────────────
if __name__ == "__main__":
    example_read_controller()   # ← change me to try a different example!
