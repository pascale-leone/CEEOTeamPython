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
        if (self.left_up() and self.right_up()) or (self.left_down() and self.right_down()):
            dm.set_speed(max(self.left_position(), self.right_position()))
            dm.run()
        elif self.left_up() or self.right_down():
            dm.set_speed_left(self.left_position())
            dm.turn_left()
        elif self.right_up() or self.left_down():
            dm.set_speed_right(self.right_position())
            dm.turn_right()
        else:
            dm.stop()
    
if __name__ == '__main__':
    card_color = le.LEGO_COLOR_MAGENTA
    card_serial = '1128'
    c = controller()
    c.connect(card_color=card_color, card_serial=card_serial)

    for _ in range(100):
        print(f'left up: {c.left_up()}')
        print(f'left down: {c.left_down()}')
        print(f'left released: {c.left_released()}')
        print(f'right up: {c.right_up()}')
        print(f'right down: {c.right_down()}')
        print(f'right released: {c.right_released()}\n')
        time.sleep(1)