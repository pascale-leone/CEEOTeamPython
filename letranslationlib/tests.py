from double_motor_functions import doubleMotor
from controller_functions import controller
import legoeducation as le
import time

card_color = le.LEGO_COLOR_MAGENTA
card_serial = '1128'
c = controller()
c.connect(card_color=card_color, card_serial=card_serial)

dm = doubleMotor()
dm.connect(card_color=card_color, card_serial=card_serial)

for _ in range(100):
    if c.left_up() and c.right_up():
        dm.run()
    elif c.left_released() and c.right_released():
        dm.stop()
    elif c.left_up():
        dm.turn_left()
    elif c.right_up():
        dm.turn_right()
    time.sleep(0.5)