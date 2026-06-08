import time
import legoeducation as le

class doubleMotor(le.DoubleMotor):
       
    def move_steps(self, step=1):
        '''
        Move both motors at once for given number of steps. 
        One step defined to be 180 degrees.
        '''
        self.movement_move_for_degrees(180*step)

    def run(self):
        self.movement_move()

    def run_time(self, time=2000):
        self.movement_move_for_time(time)

    
    def run_left_motor(self):
        # Rotate the right side of the Double Motor counterclockwise at 50% speed.
        self.motor_run(direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE, motor=le.MOTOR_LEFT, speed=50)

    def run_right(self):
        self.motor_run(direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE, motor=le.MOTOR_RIGHT, speed=50)

    

    def turn_left(self, degrees=90):
        '''
        Turns left by specified number of degrees.
        '''
        self.movement_turn_for_degrees(degrees, direction=le.MOVEMENT_TURN_DIRECTION_LEFT)

    def turn_right(self, degrees=90):
        '''
        Turns right by specified number of degrees.
        '''
        self.movement_turn_for_degrees(degrees, direction=le.MOVEMENT_TURN_DIRECTION_RIGHT)

    def set_speed(self, speed):
        '''
        Set speed of both motors for individual rotation and movement.
        '''
        self.motor_set_speed(speed, motor=le.MOTOR_LEFT)   
        self.motor_set_speed(speed, motor=le.MOTOR_RIGHT)   
        self.movement_set_speed(speed)

    def set_speed_left(self, speed):
        '''
        Set speed of left motor for individual rotation.
        '''
        self.motor_set_speed(speed, motor=le.MOTOR_LEFT)   

    def set_speed_right(self, speed):
        '''
        Set speed of right motor for individual rotation.
        '''
        self.motor_set_speed(speed, motor=le.MOTOR_RIGHT)   


    def stop(self):
        self.motor_stop()

# help(le.SingleMotor)

#help(type(le.DoubleMotor))
# card_color = le.LEGO_COLOR_BLUE
# card_serial = '1131'
# dm = doubleMotor()
# dm.connect(card_color=card_color, card_serial=card_serial)
# if not dm.connected:
# 	print('Error connecting to Double Motor.')
# 	exit(1) # error connecting

# dm.motor_set_speed(10, motor=le.MOTOR_RIGHT)   
# dm.movement_set_speed(100)
# dm.motor_run_for_degrees(360, motor=le.MOTOR_RIGHT)
# dm.move_steps(10)
# #dm.motor_set_speed(100, motor=le.MOTOR_RIGHT)
# dm.movement_set_speed(-100)
# time.sleep(.5)
# dm.motor_run_for_degrees(360, motor=le.MOTOR_RIGHT)

#dm.move_steps(10)
    
