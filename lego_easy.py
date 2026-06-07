"""
lego_easy.py  🟡🔴🔵
=====================
A simple, friendly library for kids to control LEGO Education hardware!

Requires: pip install legoeducation

HOW TO CONNECT YOUR LEGO:
  Look at the 4-digit number on the Connection Card that came with your device.
  Pass just that number when creating a Motor, Robot, Sensor, or Controller!

  If two devices with the same number are nearby, you can also pass the card
  color as a second argument to tell them apart.

EXAMPLE - Spin a single motor:
  from lego_easy import Motor
  motor = Motor("3683")         # just the number!
  motor.start()
  wait(3)
  motor.stop()
  motor.disconnect()

EXAMPLE - Drive a robot:
  from lego_easy import Robot
  robot = Robot("3683")
  robot.run()
  wait(2)
  robot.stop()
  robot.disconnect()

EXAMPLE - Read a color sensor:
  from lego_easy import ColorSensor
  sensor = ColorSensor("3683")
  print("I see:", sensor.read_color())
  sensor.disconnect()

EXAMPLE - Use the controller:
  from lego_easy import Controller
  ctrl = Controller("3683")
  left, right = ctrl.read_levers()
  print("Left lever:", left, "  Right lever:", right)
  ctrl.disconnect()

EXAMPLE - Two devices with the same serial? Add the color:
  motor = Motor("3683", color="azure")
  robot = Robot("3683", color="red")
"""

import time
import sys

try:
    import legoeducation as le
except ImportError:
    print("Oops! The LEGO library isn't installed yet.")
    print("Run this in your terminal:  pip install legoeducation")
    sys.exit(1)


# ─────────────────────────────────────────────
# Color helpers (only needed when disambiguating
# two devices with the same serial number)
# ─────────────────────────────────────────────
_COLOR_MAP = {
    "azure":   "LEGO_COLOR_AZURE",
    "blue":    "LEGO_COLOR_BLUE",
    "cyan":    "LEGO_COLOR_CYAN",
    "green":   "LEGO_COLOR_GREEN",
    "red":     "LEGO_COLOR_RED",
    "yellow":  "LEGO_COLOR_YELLOW",
    "white":   "LEGO_COLOR_WHITE",
    "black":   "LEGO_COLOR_BLACK",
    "orange":  "LEGO_COLOR_ORANGE",
    "purple":  "LEGO_COLOR_PURPLE",
    "pink":    "LEGO_COLOR_PINK",
    "magenta": "LEGO_COLOR_MAGENTA",
}

def _get_card_color(color_name: str):
    key  = color_name.lower().strip()
    attr = _COLOR_MAP.get(key)
    if attr is None:
        options = ", ".join(_COLOR_MAP.keys())
        print(f"Hmm, '{color_name}' isn't a color I know. Try: {options}")
        print("Ignoring the color and connecting by serial number only.")
        return None
    return getattr(le, attr)

def _connect(device, serial: str, color: str = None, device_name: str = "device"):
    """
    Call .connect() on any legoeducation device object.
    - Always passes card_serial so the right device is found.
    - Only passes card_color when the caller supplied one.
    """
    print(f"🔌 Connecting to {device_name} (serial: {serial}"
          + (f", color: {color}" if color else "") + ")…")
    kwargs = {"card_serial": serial}
    if color:
        lego_color = _get_card_color(color)
        if lego_color is not None:
            kwargs["card_color"] = lego_color
    device.connect(**kwargs)


# Map LEGO color numbers to friendly names for the color sensor
_LEGO_COLOR_NAMES = {
    0:  "black",
    1:  "pink",
    2:  "purple",
    3:  "blue",
    4:  "light blue",
    5:  "cyan",
    6:  "green",
    7:  "yellow",
    8:  "orange",
    9:  "red",
    10: "white",
    -1: "nothing / unknown",
}


# ══════════════════════════════════════════════════════════
#  🔧 Motor  – control a single motor
# ══════════════════════════════════════════════════════════
class Motor:
    """
    Control a LEGO Single Motor.

    Usage:
        motor = Motor("3683")            # just the serial number from your card
        motor = Motor("3683", color="azure")  # add color only if needed

        # Continuous (runs until stop):
        motor.start()                    # spin forward
        motor.start_backward()           # spin backward
        motor.stop()

        # Measured moves:
        motor.spin(degrees=360)          # one full turn, then stop
        motor.spin_backward(degrees=90)
        motor.spin_for(seconds=2)
        motor.spin_backward_for(seconds=1)

        # Other:
        motor.set_speed(50)              # 1–100
        motor.beep()
        motor.light("blue")
        motor.read_position()            # current angle in degrees
        motor.disconnect()
    """

    def __init__(self, serial: str, color: str = None, speed: int = 50):
        self._speed = max(1, min(100, speed))
        self._motor = le.SingleMotor()
        _connect(self._motor, serial, color, "Single Motor")
        if not self._motor.connected:
            print("❌ Couldn't connect. Is the motor on and charged?")
            sys.exit(1)
        print("✅ Motor connected!")

    # ── continuous ────────────────────────────

    def start(self):
        """Turn the motor on — keeps spinning until stop() is called."""
        self._motor.motor_run(
            direction=le.MOTOR_MOVE_DIRECTION_CLOCKWISE,
            speed=self._speed,
        )

    def start_backward(self):
        """Turn the motor on in reverse — keeps spinning until stop()."""
        self._motor.motor_run(
            direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE,
            speed=self._speed,
        )

    # ── measured ──────────────────────────────

    def spin(self, degrees: int = 360):
        """Spin forward by this many degrees, then stop. 360 = one full turn."""
        self._motor.motor_run_for_degrees(
            degrees,
            direction=le.MOTOR_MOVE_DIRECTION_CLOCKWISE,
            speed=self._speed,
        )

    def spin_backward(self, degrees: int = 360):
        """Spin backward by this many degrees, then stop."""
        self._motor.motor_run_for_degrees(
            degrees,
            direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE,
            speed=self._speed,
        )

    def spin_for(self, seconds: float = 1.0):
        """Spin forward for this many seconds, then stop."""
        self._motor.motor_run_for_time(
            int(seconds * 1000),
            direction=le.MOTOR_MOVE_DIRECTION_CLOCKWISE,
            speed=self._speed,
        )

    def spin_backward_for(self, seconds: float = 1.0):
        """Spin backward for this many seconds, then stop."""
        self._motor.motor_run_for_time(
            int(seconds * 1000),
            direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE,
            speed=self._speed,
        )

    def stop(self):
        """Stop the motor right away."""
        self._motor.motor_stop()

    # ── settings ──────────────────────────────

    def set_speed(self, speed: int):
        """Change speed (1 = very slow, 100 = full speed)."""
        self._speed = max(1, min(100, speed))
        self._motor.motor_set_speed(self._speed)
        print(f"⚡ Speed set to {self._speed}%")

    # ── extras ────────────────────────────────

    def beep(self):
        """Play a beep sound! 🔔"""
        self._motor.beep(pattern=le.SOUND_PATTERN_BEEP_SINGLE, frequency=440)

    def light(self, color: str = "blue"):
        """Change the button light color (e.g. 'red', 'green', 'blue'). 💡"""
        c = _get_card_color(color)
        if c:
            self._motor.light_color(c)

    def read_position(self) -> int:
        """Read the motor's current angle in degrees (0–359)."""
        return self._motor.motor.position

    def disconnect(self):
        """Disconnect when you're done."""
        self._motor.disconnect()
        print("👋 Motor disconnected.")


# ══════════════════════════════════════════════════════════
#  🤖 Robot  – drive a two-wheeled robot (Double Motor)
# ══════════════════════════════════════════════════════════
class Robot:
    """
    Drive a LEGO robot that uses the Double Motor (two wheels).

    Usage:
        robot = Robot("3683")            # just the serial number
        robot = Robot("3683", color="azure")  # add color only if needed

        # Continuous (runs until stop):
        robot.run()                      # drive forward
        robot.run_backward()             # drive backward
        robot.stop()

        # Measured moves:
        robot.forward(seconds=2)
        robot.backward(seconds=1)
        robot.forward_degrees(360)
        robot.turn_left()                # 90° by default
        robot.turn_right(degrees=45)
        robot.spin_in_place()

        # Other:
        robot.set_speed(60)
        robot.beep()
        robot.light("green")
        robot.is_tilted()
        robot.read_tilt()
        robot.victory_dance()
        robot.disconnect()
    """

    def __init__(self, serial: str, color: str = None, speed: int = 50):
        self._speed = max(1, min(100, speed))
        self._motor = le.DoubleMotor()
        _connect(self._motor, serial, color, "Robot / Double Motor")
        if not self._motor.connected:
            print("❌ Couldn't connect. Is the robot on and charged?")
            sys.exit(1)
        print("✅ Robot connected!")

    # ── continuous ────────────────────────────

    def run(self):
        """Drive forward — keeps going until stop() is called."""
        self._motor.movement_move_for_time(
            999999,
            direction=le.MOVEMENT_MOVE_DIRECTION_FORWARD,
            speed=self._speed,
        )

    def run_backward(self):
        """Drive backward — keeps going until stop() is called."""
        self._motor.movement_move_for_time(
            999999,
            direction=le.MOVEMENT_MOVE_DIRECTION_BACKWARD,
            speed=self._speed,
        )

    # ── measured ──────────────────────────────

    def forward(self, seconds: float = 1.0):
        """Drive forward for this many seconds, then stop."""
        self._motor.movement_move_for_time(
            int(seconds * 1000),
            direction=le.MOVEMENT_MOVE_DIRECTION_FORWARD,
            speed=self._speed,
        )

    def backward(self, seconds: float = 1.0):
        """Drive backward for this many seconds, then stop."""
        self._motor.movement_move_for_time(
            int(seconds * 1000),
            direction=le.MOVEMENT_MOVE_DIRECTION_BACKWARD,
            speed=self._speed,
        )

    def forward_degrees(self, degrees: int = 360):
        """Drive forward by this many degrees of wheel rotation."""
        self._motor.movement_move_for_degrees(
            degrees,
            direction=le.MOVEMENT_MOVE_DIRECTION_FORWARD,
            speed=self._speed,
        )

    def backward_degrees(self, degrees: int = 360):
        """Drive backward by this many degrees of wheel rotation."""
        self._motor.movement_move_for_degrees(
            degrees,
            direction=le.MOVEMENT_MOVE_DIRECTION_BACKWARD,
            speed=self._speed,
        )

    def turn_left(self, degrees: int = 90):
        """Turn left. Default is 90°."""
        self._motor.movement_turn_for_degrees(
            degrees,
            direction=le.MOVEMENT_TURN_DIRECTION_LEFT,
        )

    def turn_right(self, degrees: int = 90):
        """Turn right. Default is 90°."""
        self._motor.movement_turn_for_degrees(
            degrees,
            direction=le.MOVEMENT_TURN_DIRECTION_RIGHT,
        )

    def spin_in_place(self):
        """Spin around in a full circle! 🌀"""
        self._motor.movement_turn_for_degrees(
            360,
            direction=le.MOVEMENT_TURN_DIRECTION_LEFT,
        )

    def stop(self):
        """Stop the robot immediately."""
        self._motor.motor_stop()

    # ── settings ──────────────────────────────

    def set_speed(self, speed: int):
        """Change speed (1 = very slow, 100 = full speed)."""
        self._speed = max(1, min(100, speed))
        print(f"⚡ Speed set to {self._speed}%")

    # ── tilt sensor ───────────────────────────

    def is_tilted(self) -> bool:
        """Returns True if the robot is tilted sideways."""
        return self._motor.imu_device.orientation != le.DEVICE_FACE_TOP

    def read_tilt(self) -> dict:
        """Returns the robot's pitch and roll angles as a dict."""
        imu = self._motor.imu_device
        return {"pitch": round(imu.pitch, 1), "roll": round(imu.roll, 1)}

    # ── extras ────────────────────────────────

    def beep(self):
        """Play a beep sound! 🔔"""
        self._motor.beep(pattern=le.SOUND_PATTERN_BEEP_SINGLE, frequency=440)

    def light(self, color: str = "green"):
        """Change the button light color. 💡"""
        c = _get_card_color(color)
        if c:
            self._motor.light_color(c)

    def victory_dance(self):
        """Do a victory dance! 🎉"""
        print("🎉 Victory dance!")
        self.light("yellow")
        self.beep()
        self.turn_left(180)
        self.beep()
        self.turn_right(360)
        self.beep()
        self.light("green")

    def disconnect(self):
        """Disconnect when you're done."""
        self._motor.disconnect()
        print("👋 Robot disconnected.")


# ══════════════════════════════════════════════════════════
#  🌈 ColorSensor  – detect colors
# ══════════════════════════════════════════════════════════
class ColorSensor:
    """
    Use the LEGO Color Sensor to see colors!

    Usage:
        sensor = ColorSensor("3683")
        sensor = ColorSensor("3683", color="azure")  # only if needed

        sensor.read_color()        # → "red", "blue", "green", etc.
        sensor.is_color("red")     # → True or False
        sensor.read_brightness()   # → 0 (dark) to 100 (bright)
        sensor.read_rgb()          # → {'red': 120, 'green': 45, 'blue': 200}
        sensor.wait_for_color("blue")
        sensor.beep()
        sensor.light("purple")
        sensor.disconnect()
    """

    def __init__(self, serial: str, color: str = None):
        self._sensor = le.ColorSensor()
        _connect(self._sensor, serial, color, "Color Sensor")
        if not self._sensor.connected:
            print("❌ Couldn't connect. Is the sensor on and charged?")
            sys.exit(1)
        print("✅ Color Sensor connected!")

    def read_color(self) -> str:
        """Read the detected color as a friendly name like 'red' or 'blue'."""
        return _LEGO_COLOR_NAMES.get(
            self._sensor.sensor.color,
            f"unknown ({self._sensor.sensor.color})",
        )

    def read_color_number(self) -> int:
        """Read the raw LEGO color number (0–10, or −1 for nothing)."""
        return self._sensor.sensor.color

    def read_brightness(self) -> int:
        """Read surface brightness: 0 = very dark, 100 = very bright/white."""
        return self._sensor.sensor.reflection

    def read_rgb(self) -> dict:
        """Read raw red/green/blue light values as a dict."""
        s = self._sensor.sensor
        return {"red": s.rawRed, "green": s.rawGreen, "blue": s.rawBlue}

    def is_color(self, color_name: str) -> bool:
        """Returns True if the sensor currently sees the given color."""
        return self.read_color().lower() == color_name.lower().strip()

    def wait_for_color(self, color_name: str, timeout: float = 10.0) -> bool:
        """Wait until the sensor sees the given color (or timeout runs out)."""
        print(f"👀 Waiting to see '{color_name}'… (up to {timeout}s)")
        start = time.time()
        while time.time() - start < timeout:
            if self.is_color(color_name):
                print(f"🌈 Saw '{color_name}'!")
                return True
            time.sleep(0.1)
        print(f"⏰ Timed out waiting for '{color_name}'.")
        return False

    def beep(self):
        """Play a beep sound! 🔔"""
        self._sensor.beep(pattern=le.SOUND_PATTERN_BEEP_SINGLE, frequency=440)

    def light(self, color: str = "blue"):
        """Change the button light color. 💡"""
        c = _get_card_color(color)
        if c:
            self._sensor.light_color(c)

    def disconnect(self):
        """Disconnect when you're done."""
        self._sensor.disconnect()
        print("👋 Color Sensor disconnected.")


# ══════════════════════════════════════════════════════════
#  🕹️ Controller  – read the two lever joysticks
# ══════════════════════════════════════════════════════════
class Controller:
    """
    Read the LEGO Controller (two levers, each −100 to +100).
    Positive = pushed forward, negative = pushed backward, 0 = centered.

    Usage:
        ctrl = Controller("3683")
        ctrl = Controller("3683", color="azure")  # only if needed

        left, right = ctrl.read_levers()   # both at once
        ctrl.read_left()                   # just the left lever
        ctrl.read_right()                  # just the right lever

        ctrl.left_forward()                # True / False
        ctrl.left_backward()
        ctrl.left_centered()
        ctrl.right_forward()               # same for right
        ctrl.right_backward()
        ctrl.right_centered()

        ctrl.drive_robot(robot)            # use in a loop to remote-control a robot!

        ctrl.beep()
        ctrl.light("yellow")
        ctrl.disconnect()
    """

    _CENTER_DEAD_ZONE = 10  # levers within ±10% are treated as "centered"

    def __init__(self, serial: str, color: str = None):
        self._ctrl = le.Controller()
        _connect(self._ctrl, serial, color, "Controller")
        if not self._ctrl.connected:
            print("❌ Couldn't connect. Is the controller on and charged?")
            sys.exit(1)
        print("✅ Controller connected!")

    # ── reading ───────────────────────────────

    def read_levers(self) -> tuple:
        """Read both levers. Returns (left_percent, right_percent), each −100 to +100."""
        s = self._ctrl.sensor
        return (s.leftPercent, s.rightPercent)

    def read_left(self) -> int:
        """Read the LEFT lever: −100 (full back) to +100 (full forward)."""
        return self._ctrl.sensor.leftPercent

    def read_right(self) -> int:
        """Read the RIGHT lever: −100 (full back) to +100 (full forward)."""
        return self._ctrl.sensor.rightPercent

    def read_left_angle(self) -> int:
        """Read the LEFT lever angle in degrees (more precise than percent)."""
        return self._ctrl.sensor.leftAngle

    def read_right_angle(self) -> int:
        """Read the RIGHT lever angle in degrees."""
        return self._ctrl.sensor.rightAngle

    # ── direction checks ──────────────────────

    def left_forward(self)  -> bool: return self.read_left()  >  self._CENTER_DEAD_ZONE
    def left_backward(self) -> bool: return self.read_left()  < -self._CENTER_DEAD_ZONE
    def left_centered(self) -> bool: return abs(self.read_left())  <= self._CENTER_DEAD_ZONE

    def right_forward(self)  -> bool: return self.read_right()  >  self._CENTER_DEAD_ZONE
    def right_backward(self) -> bool: return self.read_right()  < -self._CENTER_DEAD_ZONE
    def right_centered(self) -> bool: return abs(self.read_right()) <= self._CENTER_DEAD_ZONE

    # ── robot driving helper ──────────────────

    def drive_robot(self, robot: "Robot"):
        """
        Use this controller to drive a Robot right now!
        Call this inside a loop to keep controlling continuously.

        Left lever  → steer left
        Right lever → steer right
        Both forward  → drive forward
        Both backward → drive backward
        Both centered → stop

        Example:
            for i in range(200):       # ~20 seconds
                ctrl.drive_robot(robot)
                wait(0.1)
            robot.stop()
        """
        left  = self.read_left()
        right = self.read_right()

        if self.left_forward() and self.right_forward():
            speed = (abs(left) + abs(right)) // 2
            robot._motor.movement_move_for_time(
                110, direction=le.MOVEMENT_MOVE_DIRECTION_FORWARD, speed=max(10, speed),
            )
        elif self.left_backward() and self.right_backward():
            speed = (abs(left) + abs(right)) // 2
            robot._motor.movement_move_for_time(
                110, direction=le.MOVEMENT_MOVE_DIRECTION_BACKWARD, speed=max(10, speed),
            )
        elif self.left_forward() and not self.right_forward():
            robot._motor.movement_turn_for_degrees(15, direction=le.MOVEMENT_TURN_DIRECTION_RIGHT)
        elif self.right_forward() and not self.left_forward():
            robot._motor.movement_turn_for_degrees(15, direction=le.MOVEMENT_TURN_DIRECTION_LEFT)
        else:
            robot._motor.motor_stop()

    # ── extras ────────────────────────────────

    def beep(self):
        """Play a beep sound! 🔔"""
        self._ctrl.beep(pattern=le.SOUND_PATTERN_BEEP_SINGLE, frequency=440)

    def light(self, color: str = "blue"):
        """Change the controller's button light color. 💡"""
        c = _get_card_color(color)
        if c:
            self._ctrl.light_color(c)

    def disconnect(self):
        """Disconnect when you're done."""
        self._ctrl.disconnect()
        print("👋 Controller disconnected.")


# ══════════════════════════════════════════════════════════
#  Handy wait() so students don't need to import time
# ══════════════════════════════════════════════════════════
def wait(seconds: float):
    """Pause for this many seconds.  wait(2) → wait 2 seconds."""
    time.sleep(seconds)


# ══════════════════════════════════════════════════════════
#  Color name constants for easy comparisons
# ══════════════════════════════════════════════════════════
COLOR_BLACK      = "black"
COLOR_PINK       = "pink"
COLOR_PURPLE     = "purple"
COLOR_BLUE       = "blue"
COLOR_LIGHT_BLUE = "light blue"
COLOR_CYAN       = "cyan"
COLOR_GREEN      = "green"
COLOR_YELLOW     = "yellow"
COLOR_ORANGE     = "orange"
COLOR_RED        = "red"
COLOR_WHITE      = "white"
