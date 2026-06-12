import time
import sys
import legoeducation as le


class controller(le.Controller):

    def connect(self, card_color, card_serial):
        for attempt in range(5):
            try:
                super().connect(card_color=card_color, card_serial=card_serial)
                break
            except Exception as e:
                if "not ready" in str(e).lower() and attempt < 4:
                    time.sleep(1)
                else:
                    raise
        if not self.connected:
            raise ConnectionError('Error connecting to Controller.')

    def left_up(self):
        return self.sensor.leftPercent > 0
    
    def left_down(self):
        return self.sensor.leftPercent < 0

    def left_released(self):
        return self.sensor.leftPercent == 0

    def right_up(self):
        return self.sensor.rightPercent > 0

    def right_down(self):
        return self.sensor.rightPercent < 0

    def right_released(self):
        return self.sensor.rightPercent == 0
    
    def left_position(self):
        return self.sensor.leftPercent
    
    def right_position(self):
        return self.sensor.rightPercent
        
    # ── driving helper ──────────────────

    def drive(self, dm, t=100): 
        for i in range(t):
            print(self.left_position(), self.right_position())
            dm.movement_move_tank(self.left_position(), self.right_position())
            time.sleep(0.1)