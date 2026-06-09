import legoeducation as le
import single_motor_functions
import double_motor_functions
import color_sensor_functions
import controller_functions
import time

def wait(seconds: float):
    time.sleep(seconds)


azure =   "LEGO_COLOR_AZURE"
blue =   "LEGO_COLOR_BLUE"
cyan =   "LEGO_COLOR_CYAN"
green =   "LEGO_COLOR_GREEN"
red =     "LEGO_COLOR_RED"
yellow =  "LEGO_COLOR_YELLOW"
white =   "LEGO_COLOR_WHITE"
black =   "LEGO_COLOR_BLACK"
orange =  "LEGO_COLOR_ORANGE"
purple =  "LEGO_COLOR_PURPLE"
magenta = "LEGO_COLOR_MAGENTA"


cs = color_sensor_functions.colorSensor()
dm = double_motor_functions.doubleMotor()
c = controller_functions.controller()
sm = single_motor_functions.singleMotor()


""
"LEGO Education Beginner Python Library"
"--------------------------------------------------------"
"Connecting to the devices:"

"device.connect(color, number)"
"please enter the color in lowercase and the serial number as a string"
"example: dm.connect(orange, '1234')"

"------------------------"
"Available Functions:"

"wait(seconds) - pause for this many seconds (time.sleep(seconds))"

"------------------------"
"Single Motor Functions"

"sm.connect(card color, serial number) - connect to the motor"
"sm.spin(degrees) - spin the motor this many degrees"
"sm.stop() - stop the motor"
"sm.set_speed(speed) - set the motor speed"
"sm.run() - run the motor"
"------------------------"
"Double Motor Functions"

"dm.connect(card color, serial number) - connect to the motors"

"dm.run() - run the motors"
"dm.run_time(time) - run the motors for this many milliseconds"

"dm.run_left() - run the left motor"
"dm.run_right() - run the right motor"

"dm.turn_left(degrees) - turn left by this many degrees"
"dm.turn_right(degrees) - turn right by this many degrees"

"dm.set_speed(speed) - set the motor speed"
"dm.set_speed_left(speed) - set the left motor speed"
"dm.set_speed_right(speed) - set the right motor speed"

"dm.stop() - stop the motors"

"------------------------"
"Color Sensor Functions"

"cs.connect(card color, serial number) - connect to the color sensor"
"cs.detect_color() - return the detected color"
"   note: the color will be returned as a string, such as 'red' or 'blue'"

"------------------------"
"Controller Functions"

"c.connect() - connect to the controller"
"c.drive(dm) - control the double motor for 10 seconds using the controller sticks"

"c.left_up() - return True if left stick is up"
"c.left_down() - return True if left stick is down"
"c.left_released() - return True if left stick is released"

"c.right_up() - return True if right stick is up"
"c.right_down() - return True if right stick is down"
"c.right_released() - return True if right stick is released"

"c.left_position() - return 'UP', 'DOWN', or 'RELEASED' for left stick"
"c.right_position() - return 'UP', 'DOWN', or 'RELEASED'"

"------------------------"
"if statements - use these to make decisions in your code"

"Example: Green means go!"
"if cs.detect_color() == 'green':"
"    print('The color is green!')"
"    dm.run()"


"for loops - use these to repeat code a certain number of times"

"Example: Spin 5 times!"
"for i in range(5):"
"    sm.spin()"

"while loops - use these to repeat code until a condition is met"
"Example: Spin until we see red!"
"while cs.detect_color() != 'red':"
"    sm.spin()"

"-----------------------------------------------------------------------------------------------------------"

"MY CODE GOES HERE!" 

"-----------------------------------------------------------------------------------------------------------"

