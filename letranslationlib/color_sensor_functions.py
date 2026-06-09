import legoeducation as le
import time

class colorSensor(le.ColorSensor):
    def __init__(self):
        super().__init__()
    
    def detect_color(self):
        color_number = self.sensor.color
        color_mapping = {
            0: 'No color',
            1: 'Red',
            2: 'Yellow',
            3: 'Blue',
            4: 'Teal',
            5: 'Green',
            6: 'Purple',
            7: 'White',
            8: 'Magenta',
            9: 'Orange',
            10: 'Azure'
        }
        #detect the color, return the detected color
        return color_mapping.get(color_number, 'Unknown')
    
# card_color = le.LEGO_COLOR_PURPLE
# card_serial = '1131'

# cs = colorSensor()

# cs.connect(card_color=card_color, card_serial=card_serial)
# if not cs.connected:
#     print('Error connecting to Color Sensor.')
#     exit(1) # error connecting

# time.sleep(5)
# for i in range(21):
#     color = cs.detect_color()
#     print(f'Detected color: {color}')
#     time.sleep(5)

# cs.disconnect()
# exit(0)
