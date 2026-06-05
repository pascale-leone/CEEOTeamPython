import legoeducation as le
import time

class colorSensor(le.ColorSensor):
    def __init__(self):
        super().__init__()
    
    def connect(self, card_color, card_serial):
        self.connect(card_color, card_serial)

        #connect the color sensor
    
    def detect_color(self):
        detected_color = self.sensor.color
        return detected_color
        #detect the color, return the detected color

card_color = le.LEGO_COLOR_PURPLE
card_serial = '1131'

cs = colorSensor(card_color=card_color, card_serial=card_serial)

cs.connect(card_color, card_serial)

for i in range(10):
    color = cs.detect_color()
    print(f'Detected color: {color}')
    time.sleep(5)

cs.disconnect()
exit(0)
