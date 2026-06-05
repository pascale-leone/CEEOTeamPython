import legoeducation as le
import time


# update these values to match the Connection Card
card_color = le.LEGO_COLOR_PURPLE
card_serial = '1131'

# Connect to the Single Motor
sm = le.SingleMotor()
sm.connect(card_color=card_color, card_serial=card_serial)

# Check connection
if not sm.connected:
	print('Error connecting to Single Motor.')
	exit(1) # error connecting

sm.motor_set_speed(10)
sm.motor_run_for_time(2000)
time.sleep(0.5)
sm.motor_set_speed(90)
sm.motor_run_for_time(2000)
time.sleep(0.5)
sm.motor_set_speed(10)
sm.motor_run_for_degrees(360)



# Disconnect
sm.disconnect()
exit(0) # successful execution