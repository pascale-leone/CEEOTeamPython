import legoeducation as le
import time
import sys
import json
import threading

class singleMotor(le.SingleMotor):
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
            raise ConnectionError('Error connecting to Single Motor.')
            
        
    def spin(self, rotations=1):
        self.motor_run_for_degrees(rotations * 360)

    def stop(self):
        self.motor_stop()
    
    def set_speed(self, speed):
        self.motor_set_speed(speed)

    def run(self):
        self.motor_run()

    def run_to(self, degrees=90):
        self.motor_run_to_absolute_position(degrees)
    

    def plot(self):
        stop_event = threading.Event()
        self._plot_stop_event = stop_event
        counter = [0]

        def _sample():
            while not stop_event.is_set():
                pos = self.motor.absolutePosition
                sys.stdout.write(f"\x00PLOT\x00{json.dumps({'x': counter[0], 'y': pos, 'channel': 'sm'})}")
                sys.stdout.flush()
                counter[0] += 1
                time.sleep(0.05)

        t = threading.Thread(target=_sample, daemon=True)
        t.start()

    def position(self):
        return self.motor.absolutePosition