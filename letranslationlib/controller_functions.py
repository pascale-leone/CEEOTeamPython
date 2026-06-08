import time
import legoeducation as le

class controller(le.Controller):

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

    def drive(self, dm):
        """
        Use this controller to drive
        Call this inside a loop to keep controlling continuously.

        Left lever  → steer left
        Right lever → steer right
        Both forward  → drive forward
        Both backward → drive backward
        Both centered → stop

        Example:
            for i in range(200):      
                ctrl.drive(dm)
                wait(0.5)
            dm.stop()
        """
        if (self.left_up() and self.right_up()):
            dm.set_speed(max(self.left_position(), self.right_position()))
            dm.run()
        elif (self.left_down() and self.right_down()):
            dm.set_speed(min(self.left_position(), self.right_position()))
            dm.run()
        elif self.left_up() or self.right_down():
            dm.set_speed_left(self.left_position())
            dm.turn_left(15)
        elif self.right_up() or self.left_down():
            dm.set_speed_right(self.right_position())
            dm.turn_right(15)
        else:
            dm.stop()  