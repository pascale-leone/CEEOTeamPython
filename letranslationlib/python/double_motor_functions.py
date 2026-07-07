import time
import sys
import json
import threading
import legoeducation as le



class doubleMotor(le.DoubleMotor):

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
            raise ConnectionError('Error connecting to Double Motor.')
       
    def move_steps(self, step=1):
        '''
        Move both motors at once for given number of steps. 
        One step defined to be 180 degrees.
        '''
        self.movement_move_for_degrees(-180*step)

    def run(self):
        self.movement_move(direction=le.MOVEMENT_MOVE_DIRECTION_BACKWARD)

    def run_time(self, time=2000):
        self.movement_move_for_time(time)

    def run_left_to(self, degrees=90):
        self.motor_run_to_absolute_position(degrees, motor=le.MOTOR_LEFT)

    def run_right_to(self, degrees=90):
        self.motor_run_to_absolute_position(degrees, motor=le.MOTOR_RIGHT)
    
    def run_left(self, degrees=None):
        if degrees is None:
            self.motor_run(direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE, motor=le.MOTOR_LEFT)
        else:
            self.motor_run_for_degrees(degrees=degrees, direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE, motor=le.MOTOR_LEFT)

    def run_right(self, degrees=None):
        if degrees is None:
            self.motor_run(direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE, motor=le.MOTOR_RIGHT)
        else:
            self.motor_run_for_degrees(degrees=degrees, direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE, motor=le.MOTOR_RIGHT)


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

    def plot_left(self):
        stop_event = threading.Event()
        self._plot_stop_event = stop_event
        counter = [0]

        def _sample():
            while not stop_event.is_set():
                pos = self.motor[le.MOTOR_LEFT].absolutePosition
                sys.stdout.write(f"\x00PLOT\x00{json.dumps({'x': counter[0], 'y': pos, 'channel': 'dm_left'})}")
                sys.stdout.flush()
                counter[0] += 1
                time.sleep(0.05)

        t = threading.Thread(target=_sample, daemon=True)
        t.start()

    def plot_right(self):
        stop_event = threading.Event()
        self._plot_stop_event = stop_event
        counter = [0]

        def _sample():
            while not stop_event.is_set():
                pos = self.motor[le.MOTOR_RIGHT].absolutePosition
                sys.stdout.write(f"\x00PLOT\x00{json.dumps({'x': counter[0], 'y': pos, 'channel': 'dm_right'})}")
                sys.stdout.flush()
                counter[0] += 1
                time.sleep(0.05)

        t = threading.Thread(target=_sample, daemon=True)
        t.start()

    def left_position(self):
        return self.motor[le.MOTOR_LEFT].absolutePosition
    
    def right_position(self):
        return self.motor[le.MOTOR_RIGHT].absolutePosition
