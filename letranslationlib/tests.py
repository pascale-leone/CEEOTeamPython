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

for _ in range(300):
    c.drive(dm)
    time.sleep(0.5)