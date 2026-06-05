import legoeducation as le
import time

class singleMotor(le.SingleMotor):
    def __init__(self):
        super().__init__()

    def turn(self, degrees=360):
        self.motor_run_for_degrees(degrees)

    #uses degrees - alternative?

    def stop(self):
        self.motor_stop()
    
    def set_speed(self, speed):
        self.motor_set_speed(speed)

    def run(self):
        self.motor_run() 


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
    

sm = singleMotor()
cs = colorSensor()

card_color = le.LEGO_COLOR_PURPLE
card_serial = '1131'

sm.connect(card_color=card_color, card_serial=card_serial)
if not sm.connected:
    print('Error connecting to Single Motor.')
    exit(1) # error connecting

cs.connect(card_color=card_color, card_serial=card_serial)
if not cs.connected:
    print('Error connecting to Color Sensor.')
    exit(1) # error connecting

time.sleep(2)

cs.disconnect()
sm.disconnect()
exit(0)
