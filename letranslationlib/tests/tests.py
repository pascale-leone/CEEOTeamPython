from double_motor_functions import doubleMotor
from controller_functions import controller
import legoeducation as le
import time

# card_color = le.LEGO_COLOR_MAGENTA
# card_serial = '1128'
# c = controller()
# c.connect(card_color=card_color, card_serial=card_serial)

# dm = doubleMotor()
# dm.connect(card_color=card_color, card_serial=card_serial)

# c.drive(dm)
card_color = le.LEGO_COLOR_RED
card_serial = '1151'
c = controller()
c.connect(card_color=card_color, card_serial=card_serial)
for i in range(100):
    print(c.sensor.leftPercent, c.sensor.rightPercent)
    time.sleep(0.5)