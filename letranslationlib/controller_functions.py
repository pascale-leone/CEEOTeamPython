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
        if self.left_up():
            return 'UP'
        elif self.left_down():
            return 'DOWN'
        else:
            return 'RELEASED'
    
    def right_position(self):
        if self.right_up():
            return 'UP'
        elif self.right_down():
            return 'DOWN'
        else:
            return 'RELEASED'
    
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