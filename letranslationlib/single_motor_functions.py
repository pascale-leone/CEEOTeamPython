import legoeducation as le
import time

class singleMotor(le.SingleMotor):
    def __init__(self):
        super().__init__()
        
    def spin(self, rotations=1):
        self.motor_run_for_degrees(rotations * 360)

    def stop(self):
        self.motor_stop()
    
    def set_speed(self, speed):
        self.motor_set_speed(speed)

    def run(self):
        self.motor_run() 
