import legoeducation as le
import time
import sys

class colorSensor(le.ColorSensor):
    def __init__(self):
        super().__init__()

    def connect(self, card_serial, card_color=None):
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
            raise ConnectionError('Error connecting to Color Sensor.')
    
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
