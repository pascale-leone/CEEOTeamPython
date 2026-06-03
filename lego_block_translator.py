"""
lego_block_translator.py
========================
LEGO® Education Coding Canvas → Python Translation Library
Maps block-coding commands from code.legoeducation.com/en-us/word
to the legoeducation Python API (pip install legoeducation).

Usage:
    from lego_block_translator import DoubleMotorProgram, SingleMotorProgram, ColorSensorProgram

Repo reference: https://github.com/LEGO/LEGOEducation
"""

import legoeducation as le
import time


# ─────────────────────────────────────────────
#  DIRECTION MAPS  (block label → API constant)
# ─────────────────────────────────────────────

# Arrow directions used by "start moving" / "move N steps" blocks
MOVE_DIRECTION_MAP = {
    "forward":  le.MOVEMENT_MOVE_DIRECTION_FORWARD,
    "↑":        le.MOVEMENT_MOVE_DIRECTION_FORWARD,
    "up":       le.MOVEMENT_MOVE_DIRECTION_FORWARD,
    "backward": le.MOVEMENT_MOVE_DIRECTION_BACKWARD,
    "↓":        le.MOVEMENT_MOVE_DIRECTION_BACKWARD,
    "down":     le.MOVEMENT_MOVE_DIRECTION_BACKWARD,
}

# Arrow directions used by "start moving" continuous block (movement_move)
CONTINUOUS_DIRECTION_MAP = {
    "forward":  le.MOVEMENT_DIRECTION_FORWARD,
    "↑":        le.MOVEMENT_DIRECTION_FORWARD,
    "up":       le.MOVEMENT_DIRECTION_FORWARD,
    "backward": le.MOVEMENT_DIRECTION_BACKWARD,
    "↓":        le.MOVEMENT_DIRECTION_BACKWARD,
    "down":     le.MOVEMENT_DIRECTION_BACKWARD,
    "left":     le.MOVEMENT_DIRECTION_LEFT,
    "←":        le.MOVEMENT_DIRECTION_LEFT,
    "right":    le.MOVEMENT_DIRECTION_RIGHT,
    "→":        le.MOVEMENT_DIRECTION_RIGHT,
}

# Turn directions used by "turn N degrees" block
TURN_DIRECTION_MAP = {
    "right":        le.MOVEMENT_TURN_DIRECTION_RIGHT,
    "clockwise":    le.MOVEMENT_TURN_DIRECTION_RIGHT,
    "↷":            le.MOVEMENT_TURN_DIRECTION_RIGHT,
    "↱":            le.MOVEMENT_TURN_DIRECTION_RIGHT,
    "left":         le.MOVEMENT_TURN_DIRECTION_LEFT,
    "counterclockwise": le.MOVEMENT_TURN_DIRECTION_LEFT,
    "↶":            le.MOVEMENT_TURN_DIRECTION_LEFT,
    "↰":            le.MOVEMENT_TURN_DIRECTION_LEFT,
}

# Single-motor spin directions used by "run motor" block
MOTOR_DIRECTION_MAP = {
    "clockwise":        le.MOTOR_MOVE_DIRECTION_CLOCKWISE,
    "↷":                le.MOTOR_MOVE_DIRECTION_CLOCKWISE,
    "right":            le.MOTOR_MOVE_DIRECTION_CLOCKWISE,
    "counterclockwise": le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE,
    "↶":                le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE,
    "left":             le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE,
}

# Motor side used by double-motor independent control blocks
MOTOR_SIDE_MAP = {
    "left":  le.MOTOR_LEFT,
    "right": le.MOTOR_RIGHT,
    "both":  le.MOTOR_BOTH,
}

# LEGO Color names (connection card colors, light colors, sensor colors)
COLOR_MAP = {
    "red":     le.LEGO_COLOR_RED,
    "yellow":  le.LEGO_COLOR_YELLOW,
    "blue":    le.LEGO_COLOR_BLUE,
    "teal":    le.LEGO_COLOR_TEAL,
    "green":   le.LEGO_COLOR_GREEN,
    "purple":  le.LEGO_COLOR_PURPLE,
    "white":   le.LEGO_COLOR_WHITE,
    "magenta": le.LEGO_COLOR_MAGENTA,
    "orange":  le.LEGO_COLOR_ORANGE,
    "azure":   le.LEGO_COLOR_AZURE,
    "none":    le.LEGO_COLOR_NOCOLOR,
}

# Light patterns for the hardware button LED
LIGHT_PATTERN_MAP = {
    "solid":       le.LIGHT_PATTERN_SOLID,
    "breathe":     le.LIGHT_PATTERN_BREATHE,
    "pulse":       le.LIGHT_PATTERN_PULSE,
    "short blink": le.LIGHT_PATTERN_SHORT_BLINK,
    "long blink":  le.LIGHT_PATTERN_LONG_BLINK,
    "double blink":le.LIGHT_PATTERN_DOUBLE_BLINK,
}

# Sound patterns for the hardware beeper
SOUND_PATTERN_MAP = {
    "single":          le.SOUND_PATTERN_BEEP_SINGLE,
    "double":          le.SOUND_PATTERN_BEEP_DOUBLE,
    "triple":          le.SOUND_PATTERN_BEEP_TRIPLE,
    "up middle down":  le.SOUND_PATTERN_BEEP_UP_MIDDLE_DOWN,
}

# Motor end states (used by "set end state" block)
END_STATE_MAP = {
    "coast":       le.MOTOR_END_STATE_COAST,
    "brake":       le.MOTOR_END_STATE_BRAKE,
    "hold":        le.MOTOR_END_STATE_HOLD,
    "continue":    le.MOTOR_END_STATE_CONTINUE,
    "smart coast": le.MOTOR_END_STATE_SMART_COAST,
    "smart brake": le.MOTOR_END_STATE_SMART_BRAKE,
    "default":     le.MOTOR_END_STATE_DEFAULT,
}


# ─────────────────────────────────────────────────────────────────────────────
#  HELPER: resolve a direction string to an API constant
# ─────────────────────────────────────────────────────────────────────────────

def _resolve(mapping, key, label="value"):
    """Look up key (case-insensitive) in mapping or raise a clear error."""
    result = mapping.get(str(key).lower().strip())
    if result is None:
        raise ValueError(
            f"Unknown {label}: '{key}'. Valid options: {list(mapping.keys())}"
        )
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  DOUBLE MOTOR PROGRAM
#  Wraps every block available in the Double Motor section of Coding Canvas
# ─────────────────────────────────────────────────────────────────────────────

class DoubleMotorProgram:
    """
    A helper class that mirrors the LEGO Coding Canvas block palette for the
    Double Motor.  Create an instance, call blocks in order, then call run().

    Example
    -------
        prog = DoubleMotorProgram(card_color="azure", card_serial="3683")
        prog.start_moving("forward")
        prog.turn(90, "right")
        prog.set_movement_speed(50)
        prog.move(2, "forward")
        prog.stop_moving()
        prog.run()
    """

    def __init__(self, card_color: str, card_serial: str):
        self._card_color = _resolve(COLOR_MAP, card_color, "card color")
        self._card_serial = card_serial
        self._steps: list = []

    # ── Block: "when ▶ clicked" ──────────────────────────────────────────────
    # This is implicit — just call run() to execute the program.

    # ── Block: "start moving ↑" ──────────────────────────────────────────────
    def start_moving(self, direction: str = "forward", speed: int = 50):
        """
        Block: start moving [direction]
        Starts continuous movement. Equivalent to movement_move().
        direction: "forward" | "backward" | "left" | "right"
        speed: 0–100 (%)
        """
        d = _resolve(CONTINUOUS_DIRECTION_MAP, direction, "direction")
        self._steps.append(("start_moving", d, speed))

    # ── Block: "turn N degrees ↷" ────────────────────────────────────────────
    def turn(self, degrees: int, direction: str = "right"):
        """
        Block: turn [degrees] degrees [direction]
        direction: "left" | "right" | "clockwise" | "counterclockwise"
        """
        d = _resolve(TURN_DIRECTION_MAP, direction, "turn direction")
        self._steps.append(("turn", degrees, d))

    # ── Block: "set movement speed to N %" ───────────────────────────────────
    def set_movement_speed(self, speed: int):
        """
        Block: set movement speed to [N] %
        Stores the speed value; applied to the next move block.
        speed: 0–100 (%)
        """
        self._steps.append(("set_speed", speed))

    # ── Block: "move N steps ↑" ──────────────────────────────────────────────
    def move(self, steps: int, direction: str = "forward", speed: int = 50):
        """
        Block: move [N] steps [direction]
        'steps' maps to degrees in the Python API.
        direction: "forward" | "backward"
        speed: 0–100 (%)
        """
        d = _resolve(MOVE_DIRECTION_MAP, direction, "move direction")
        self._steps.append(("move", steps, d, speed))

    # ── Block: "move for N seconds ↑" ────────────────────────────────────────
    def move_for_time(self, seconds: float, direction: str = "forward", speed: int = 50):
        """
        Block: move for [N] seconds [direction]
        direction: "forward" | "backward" | "left" | "right"
        speed: 0–100 (%)
        """
        d = _resolve(CONTINUOUS_DIRECTION_MAP, direction, "direction")
        self._steps.append(("move_time", int(seconds * 1000), d, speed))

    # ── Block: "stop moving" ─────────────────────────────────────────────────
    def stop_moving(self):
        """Block: stop moving"""
        self._steps.append(("stop",))

    # ── Block: "wait N seconds" ───────────────────────────────────────────────
    def wait(self, seconds: float):
        """Block: wait [N] seconds"""
        self._steps.append(("wait", seconds))

    # ── Block: "repeat N times" ───────────────────────────────────────────────
    def repeat(self, times: int, inner_steps: list):
        """
        Block: repeat [N] times
        inner_steps: list of bound method calls, e.g. [(prog.move, (2,), {"direction":"forward"})]
        """
        self._steps.append(("repeat", times, inner_steps))

    # ── Block: "set light color [color]" ─────────────────────────────────────
    def set_light(self, color: str, pattern: str = "solid", intensity: int = 100):
        """
        Block: set light color [color]
        color: "red" | "blue" | "green" | etc.
        pattern: "solid" | "breathe" | "pulse" | "short blink" | "long blink" | "double blink"
        """
        c = _resolve(COLOR_MAP, color, "color")
        p = _resolve(LIGHT_PATTERN_MAP, pattern, "light pattern")
        self._steps.append(("light", c, p, intensity))

    # ── Block: "beep [pattern]" ───────────────────────────────────────────────
    def beep(self, pattern: str = "single", frequency: int = 440):
        """
        Block: beep [pattern]
        pattern: "single" | "double" | "triple" | "up middle down"
        """
        p = _resolve(SOUND_PATTERN_MAP, pattern, "sound pattern")
        self._steps.append(("beep", p, frequency))

    # ── Block: "run left motor for N degrees ↷" ───────────────────────────────
    def run_motor(self, motor: str, degrees: int, direction: str = "clockwise", speed: int = 50):
        """
        Block: run [left|right|both] motor for [N] degrees [direction]
        Independently controls one or both motors.
        """
        m = _resolve(MOTOR_SIDE_MAP, motor, "motor side")
        d = _resolve(MOTOR_DIRECTION_MAP, direction, "motor direction")
        self._steps.append(("run_motor", m, degrees, d, speed))

    # ── Execute the program ───────────────────────────────────────────────────
    def run(self):
        """
        Connect to the Double Motor, execute all queued blocks in order,
        then disconnect. Mirrors pressing ▶ in Coding Canvas.
        """
        motor = le.DoubleMotor()
        motor.connect(card_color=self._card_color, card_serial=self._card_serial)

        if not motor.connected:
            print("Error: Could not connect to Double Motor.")
            exit(1)

        _speed = 50  # default speed, updated by set_speed block

        for step in self._steps:
            cmd = step[0]

            if cmd == "start_moving":
                _, direction, speed = step
                motor.movement_move(direction=direction, speed=speed)

            elif cmd == "turn":
                _, degrees, direction = step
                motor.movement_turn_for_degrees(degrees=degrees, direction=direction)

            elif cmd == "set_speed":
                _, speed = step
                _speed = speed

            elif cmd == "move":
                _, steps, direction, speed = step
                motor.movement_move_for_degrees(steps, direction=direction, speed=_speed)

            elif cmd == "move_time":
                _, ms, direction, speed = step
                motor.movement_move_for_time(time_ms=ms, direction=direction, speed=_speed)

            elif cmd == "stop":
                motor.motor_stop()

            elif cmd == "wait":
                _, seconds = step
                time.sleep(seconds)

            elif cmd == "light":
                _, color, pattern, intensity = step
                motor.light_color(color, pattern=pattern, intensity=intensity)

            elif cmd == "beep":
                _, pattern, frequency = step
                motor.beep(pattern=pattern, frequency=frequency)

            elif cmd == "run_motor":
                _, m, degrees, direction, speed = step
                motor.motor_run_for_degrees(degrees, motor=m, direction=direction, speed=speed)

        motor.disconnect()
        exit(0)


# ─────────────────────────────────────────────────────────────────────────────
#  SINGLE MOTOR PROGRAM
#  Wraps every block available in the Single Motor section of Coding Canvas
# ─────────────────────────────────────────────────────────────────────────────

class SingleMotorProgram:
    """
    Mirrors the LEGO Coding Canvas block palette for the Single Motor.

    Example
    -------
        prog = SingleMotorProgram(card_color="azure", card_serial="3683")
        prog.run_for_degrees(360, direction="clockwise", speed=75)
        prog.stop()
        prog.run()
    """

    def __init__(self, card_color: str, card_serial: str):
        self._card_color = _resolve(COLOR_MAP, card_color, "card color")
        self._card_serial = card_serial
        self._steps: list = []

    # ── Block: "run motor ↷" (continuous) ────────────────────────────────────
    def start_motor(self, direction: str = "clockwise", speed: int = 50):
        """
        Block: run motor [direction]  (no duration — runs until stop)
        direction: "clockwise" | "counterclockwise"
        speed: 0–100 (%)
        """
        d = _resolve(MOTOR_DIRECTION_MAP, direction, "motor direction")
        self._steps.append(("start", d, speed))

    # ── Block: "run motor for N degrees ↷" ───────────────────────────────────
    def run_for_degrees(self, degrees: int, direction: str = "clockwise", speed: int = 50):
        """
        Block: run motor for [N] degrees [direction]
        """
        d = _resolve(MOTOR_DIRECTION_MAP, direction, "motor direction")
        self._steps.append(("degrees", degrees, d, speed))

    # ── Block: "run motor for N seconds ↷" ───────────────────────────────────
    def run_for_time(self, seconds: float, direction: str = "clockwise", speed: int = 50):
        """
        Block: run motor for [N] seconds [direction]
        """
        d = _resolve(MOTOR_DIRECTION_MAP, direction, "motor direction")
        self._steps.append(("time", int(seconds * 1000), d, speed))

    # ── Block: "set motor speed to N %" ──────────────────────────────────────
    def set_speed(self, speed: int):
        """Block: set motor speed to [N] %"""
        self._steps.append(("set_speed", speed))

    # ── Block: "stop motor" ───────────────────────────────────────────────────
    def stop(self):
        """Block: stop motor"""
        self._steps.append(("stop",))

    # ── Block: "wait N seconds" ───────────────────────────────────────────────
    def wait(self, seconds: float):
        """Block: wait [N] seconds"""
        self._steps.append(("wait", seconds))

    # ── Block: "set light color [color]" ─────────────────────────────────────
    def set_light(self, color: str, pattern: str = "solid", intensity: int = 100):
        c = _resolve(COLOR_MAP, color, "color")
        p = _resolve(LIGHT_PATTERN_MAP, pattern, "light pattern")
        self._steps.append(("light", c, p, intensity))

    # ── Block: "beep [pattern]" ───────────────────────────────────────────────
    def beep(self, pattern: str = "single", frequency: int = 440):
        p = _resolve(SOUND_PATTERN_MAP, pattern, "sound pattern")
        self._steps.append(("beep", p, frequency))

    def run(self):
        """Connect, execute all blocks, then disconnect."""
        motor = le.SingleMotor()
        motor.connect(card_color=self._card_color, card_serial=self._card_serial)

        if not motor.connected:
            print("Error: Could not connect to Single Motor.")
            exit(1)

        _speed = 50

        for step in self._steps:
            cmd = step[0]

            if cmd == "start":
                _, direction, speed = step
                motor.motor_run(direction=direction, speed=speed)

            elif cmd == "degrees":
                _, degrees, direction, speed = step
                motor.motor_run_for_degrees(degrees=degrees, direction=direction, speed=_speed)

            elif cmd == "time":
                _, ms, direction, speed = step
                motor.motor_run_for_time(ms, direction=direction, speed=_speed)

            elif cmd == "set_speed":
                _, speed = step
                _speed = speed
                motor.motor_set_speed(_speed)

            elif cmd == "stop":
                motor.motor_stop()

            elif cmd == "wait":
                _, seconds = step
                time.sleep(seconds)

            elif cmd == "light":
                _, color, pattern, intensity = step
                motor.light_color(color, pattern=pattern, intensity=intensity)

            elif cmd == "beep":
                _, pattern, frequency = step
                motor.beep(pattern=pattern, frequency=frequency)

        motor.disconnect()
        exit(0)


# ─────────────────────────────────────────────────────────────────────────────
#  COLOR SENSOR PROGRAM
#  Wraps Color Sensor reading blocks from Coding Canvas
# ─────────────────────────────────────────────────────────────────────────────

class ColorSensorProgram:
    """
    Mirrors the LEGO Coding Canvas block palette for the Color Sensor.

    Example
    -------
        prog = ColorSensorProgram(card_color="azure", card_serial="3683")
        prog.print_color(duration_seconds=5)
        prog.run()
    """

    def __init__(self, card_color: str, card_serial: str):
        self._card_color = _resolve(COLOR_MAP, card_color, "card color")
        self._card_serial = card_serial
        self._steps: list = []

    # ── Block: "when color detected = [color]" ────────────────────────────────
    def when_color_detected(self, color: str, callback):
        """
        Block: when color detected = [color]
        Registers a callback to fire whenever that color is seen.
        callback: callable()
        """
        c = _resolve(COLOR_MAP, color, "color")
        self._steps.append(("when_color", c, callback))

    # ── Block: "print detected color for N seconds" ───────────────────────────
    def print_color(self, duration_seconds: float = 5.0):
        """Convenience block: read and print the detected color for N seconds."""
        self._steps.append(("print_color", duration_seconds))

    # ── Block: "wait N seconds" ───────────────────────────────────────────────
    def wait(self, seconds: float):
        """Block: wait [N] seconds"""
        self._steps.append(("wait", seconds))

    # ── Block: "set light color [color]" ─────────────────────────────────────
    def set_light(self, color: str, pattern: str = "solid", intensity: int = 100):
        c = _resolve(COLOR_MAP, color, "color")
        p = _resolve(LIGHT_PATTERN_MAP, pattern, "light pattern")
        self._steps.append(("light", c, p, intensity))

    # ── Block: "beep [pattern]" ───────────────────────────────────────────────
    def beep(self, pattern: str = "single", frequency: int = 440):
        p = _resolve(SOUND_PATTERN_MAP, pattern, "sound pattern")
        self._steps.append(("beep", p, frequency))

    def run(self):
        """Connect, execute all blocks, then disconnect."""
        sensor = le.ColorSensor()
        sensor.connect(card_color=self._card_color, card_serial=self._card_serial)

        if not sensor.connected:
            print("Error: Could not connect to Color Sensor.")
            exit(1)

        for step in self._steps:
            cmd = step[0]

            if cmd == "print_color":
                _, duration = step
                iterations = int(duration * 10)
                for _ in range(iterations):
                    print(f"Color detected: {sensor.sensor.color}")
                    time.sleep(0.1)

            elif cmd == "when_color":
                _, target_color, callback = step
                # Poll for the color and fire the callback once when matched
                for _ in range(100):  # poll for up to 10 seconds
                    if sensor.sensor.color == target_color:
                        callback()
                        break
                    time.sleep(0.1)

            elif cmd == "wait":
                _, seconds = step
                time.sleep(seconds)

            elif cmd == "light":
                _, color, pattern, intensity = step
                sensor.light_color(color, pattern=pattern, intensity=intensity)

            elif cmd == "beep":
                _, pattern, frequency = step
                sensor.beep(pattern=pattern, frequency=frequency)

        sensor.disconnect()
        exit(0)


# ─────────────────────────────────────────────────────────────────────────────
#  QUICK TRANSLATION REFERENCE  (block label → Python call)
# ─────────────────────────────────────────────────────────────────────────────

BLOCK_REFERENCE = """
╔══════════════════════════════════════════════════════════════════════════════╗
║          LEGO Coding Canvas → Python API Quick Reference                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  DOUBLE MOTOR BLOCKS                                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Block                            │ Python (DoubleMotorProgram)             ║
║──────────────────────────────────────────────────────────────────────────── ║
║  when ▶ clicked                   │ prog.run()                              ║
║  start moving ↑                   │ prog.start_moving("forward")            ║
║  start moving ↓                   │ prog.start_moving("backward")           ║
║  start moving ← / →               │ prog.start_moving("left"/"right")       ║
║  turn 90 degrees ↷                │ prog.turn(90, "right")                  ║
║  turn 90 degrees ↶                │ prog.turn(90, "left")                   ║
║  set movement speed to 50 %       │ prog.set_movement_speed(50)             ║
║  move 2 steps ↑                   │ prog.move(2, "forward")                 ║
║  move 2 steps ↓                   │ prog.move(2, "backward")                ║
║  move for 3 seconds ↑             │ prog.move_for_time(3, "forward")        ║
║  stop moving                      │ prog.stop_moving()                      ║
║  wait 1 seconds                   │ prog.wait(1)                            ║
║  run left motor for 360 degrees ↷ │ prog.run_motor("left", 360)             ║
║  run right motor for 360 degrees ↷│ prog.run_motor("right", 360)            ║
║  set light color blue             │ prog.set_light("blue")                  ║
║  beep single                      │ prog.beep("single")                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  SINGLE MOTOR BLOCKS                                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Block                            │ Python (SingleMotorProgram)             ║
║──────────────────────────────────────────────────────────────────────────── ║
║  when ▶ clicked                   │ prog.run()                              ║
║  run motor ↷                      │ prog.start_motor("clockwise")           ║
║  run motor ↶                      │ prog.start_motor("counterclockwise")    ║
║  run motor for 360 degrees ↷      │ prog.run_for_degrees(360, "clockwise")  ║
║  run motor for 2 seconds ↷        │ prog.run_for_time(2, "clockwise")       ║
║  set motor speed to 50 %          │ prog.set_speed(50)                      ║
║  stop motor                       │ prog.stop()                             ║
║  wait 1 seconds                   │ prog.wait(1)                            ║
║  set light color blue             │ prog.set_light("blue")                  ║
║  beep single                      │ prog.beep("single")                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  COLOR SENSOR BLOCKS                                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Block                            │ Python (ColorSensorProgram)             ║
║──────────────────────────────────────────────────────────────────────────── ║
║  when ▶ clicked                   │ prog.run()                              ║
║  print detected color 5s          │ prog.print_color(5)                     ║
║  when color detected = red        │ prog.when_color_detected("red", fn)     ║
║  wait 1 seconds                   │ prog.wait(1)                            ║
║  set light color blue             │ prog.set_light("blue")                  ║
║  beep single                      │ prog.beep("single")                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  VALID OPTION VALUES                                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Colors:    red, yellow, blue, teal, green, purple, white, magenta,        ║
║             orange, azure, none                                             ║
║  Move dir:  forward (↑), backward (↓)                                      ║
║  Turn dir:  right (↷), left (↶), clockwise, counterclockwise               ║
║  Contin.:   forward, backward, left, right                                  ║
║  Motor dir: clockwise (↷), counterclockwise (↶)                            ║
║  Motor:     left, right, both                                               ║
║  Light:     solid, breathe, pulse, short blink, long blink, double blink   ║
║  Sound:     single, double, triple, up middle down                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


def print_reference():
    """Print the full block → Python quick reference table."""
    print(BLOCK_REFERENCE)


# ─────────────────────────────────────────────────────────────────────────────
#  EXAMPLE PROGRAMS
# ─────────────────────────────────────────────────────────────────────────────

def example_from_image():
    """
    Reproduces the block program shown in the original screenshot:

        when ▶ clicked
        start moving ↑
        turn 90 degrees ↷
        set movement speed to 50 %
        move 2 steps ↑
        stop moving
    """
    prog = DoubleMotorProgram(card_color="azure", card_serial="3683")
    prog.start_moving("forward")
    prog.turn(90, "right")
    prog.set_movement_speed(50)
    prog.move(2, "forward")
    prog.stop_moving()
    prog.run()


def example_square():
    """Drive the Double Motor in a square (4 × forward + turn right)."""
    prog = DoubleMotorProgram(card_color="azure", card_serial="3683")
    prog.set_movement_speed(50)
    for _ in range(4):
        prog.move(180, "forward")
        prog.turn(90, "right")
    prog.stop_moving()
    prog.run()


def example_single_motor_spin():
    """Spin the Single Motor two full rotations clockwise then stop."""
    prog = SingleMotorProgram(card_color="azure", card_serial="3683")
    prog.set_speed(75)
    prog.run_for_degrees(720, direction="clockwise")
    prog.stop()
    prog.run()


if __name__ == "__main__":
    print_reference()
