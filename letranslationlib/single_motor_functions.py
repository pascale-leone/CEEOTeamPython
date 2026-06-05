import legoeducation as le
import time

class singleMotor(le.SingleMotor):
    def __init__(self, card_color, card_serial):
        super().__init__()
        self.connect(card_color=card_color, card_serial=card_serial)

    def turn(self, degrees=360):
        self.motor_run_for_degrees(degrees)

    #uses degrees - alternative?

    def stop(self):
        self.motor_stop()
    
    def set_speed(self, speed):
        self.motor_set_speed(speed)

    def run(self):
        self.motor_run() 

card_color = le.LEGO_COLOR_PURPLE
card_serial = '1131'   
sm = singleMotor(card_color=card_color, card_serial=card_serial)







