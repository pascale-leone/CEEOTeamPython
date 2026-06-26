import math
import asyncio
import legoeducation as le

class doubleMotor(le.DoubleMotor):

    # ── Sensor accessors ────────────────────────────────────────
    # self.motor is a list: [0] = left, [1] = right
    def _safe(self, val):
        try:
            if math.isnan(val):
                return None
        except TypeError:
            pass
        return val

    def get_speed(self, side='left'):
        idx = 1 if side == 'right' else 0
        return self._safe(self.motor[idx].speed)

    def get_power(self, side='left'):
        idx = 1 if side == 'right' else 0
        return self._safe(self.motor[idx].power)

    def get_position(self, side='left'):
        idx = 1 if side == 'right' else 0
        return self._safe(self.motor[idx].position)

    def get_absolute_position(self, side='left'):
        idx = 1 if side == 'right' else 0
        return self._safe(self.motor[idx].absolutePosition)

    # ── Motion ──────────────────────────────────────────────────
    def move_steps(self, step=1):
        self.movement_move_for_degrees(180 * step, direction=le.MOVEMENT_MOVE_DIRECTION_BACKWARD, blocking=False)

    def run(self):
        self.movement_move(direction=le.MOVEMENT_MOVE_DIRECTION_BACKWARD, blocking=False)

    async def run_time(self, time=2):
        self.movement_move_for_time(time*1000, direction=le.MOVEMENT_MOVE_DIRECTION_BACKWARD, blocking=False)
        await asyncio.sleep(time)
    
    def run_right(self, degrees=None):
        if degrees is None:
            self.motor_run(direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE, motor=le.MOTOR_RIGHT, blocking=False)
        else:
            self.motor_run_for_degrees(degrees=degrees, direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE, motor=le.MOTOR_RIGHT, blocking=False)
            
    def run_left(self, degrees=None):
        if degrees is None:
            self.motor_run(direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE, motor=le.MOTOR_LEFT, blocking=False)
        else:
            self.motor_run_for_degrees(degrees=degrees, direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE, motor=le.MOTOR_LEFT, blocking=False)


    async def turn_left(self, degrees=90):
        self.movement_turn_for_degrees(degrees,
                                       direction=le.MOVEMENT_TURN_DIRECTION_LEFT, blocking=False)
        curr = self._safe(self.motor[1].speed)
        if degrees <= 180:
            time_pause = 1 - curr*0.01
        else:
            time_pause = 2 - curr*0.02
        await asyncio.sleep(time_pause)
        

    async def turn_right(self, degrees=90):
        self.movement_turn_for_degrees(degrees,
                                       direction=le.MOVEMENT_TURN_DIRECTION_RIGHT, blocking=False)
        curr = self._safe(self.motor[1].speed)
        if degrees <= 180:
            time_pause = 1 - curr*0.01
        else:
            time_pause = 2 - curr*0.02
        await asyncio.sleep(time_pause)

    def set_speed(self, speed):
        self.motor_set_speed(speed, motor=le.MOTOR_LEFT,  blocking=False)
        self.motor_set_speed(speed, motor=le.MOTOR_RIGHT, blocking=False)
        self.movement_set_speed(speed, blocking=False)

    def set_speed_left(self, speed):
        self.motor_set_speed(speed, motor=le.MOTOR_LEFT, blocking=False)

    def set_speed_right(self, speed):
        self.motor_set_speed(speed, motor=le.MOTOR_RIGHT, blocking=False)

    def stop(self):
        self.motor_stop(motor=le.MOTOR_RIGHT, blocking=False)
        self.motor_stop(motor=le.MOTOR_LEFT, blocking=False)

