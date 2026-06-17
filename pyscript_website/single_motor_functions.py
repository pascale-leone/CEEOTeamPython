import math
import legoeducation as le

class singleMotor(le.SingleMotor):
    def __init__(self):
        super().__init__()

    # ── Motion ──────────────────────────────────────────────────
    def spin(self, rotations=1):
        self.motor_run_for_degrees(rotations * 360, blocking=False)

    def stop(self):
        self.motor_stop(blocking=False)

    def set_speed(self, speed):
        self.motor_set_speed(speed, blocking=False)

    def run(self):
        self.motor_run(blocking=False)

    # ── Sensor accessors (safe nan guard on all) ─────────────────
    def _safe(self, val):
        """Return None if value is nan (not yet received), else return val."""
        try:
            if math.isnan(val):
                return None
        except TypeError:
            pass
        return val

    def get_speed(self):
        return self._safe(self.motor.speed)

    def get_power(self):
        return self._safe(self.motor.power)

    def get_position(self):
        return self._safe(self.motor.position)

    def get_absolute_position(self):
        return self._safe(self.motor.absolutePosition)