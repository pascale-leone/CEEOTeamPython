import single_motor_functions
import double_motor_functions
import color_sensor_functions
import controller_functions

""
"LEGO Education Beginner Python Library"
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
"dm.spin(degrees) - spin the motors this many degrees"
"dm.stop() - stop the motors"
"dm.set_speed(speed) - set the motor speed"
"dm.run() - run the motors"
"------------------------"
"Color Sensor Functions"

"cs.connect(card color, serial number) - connect to the color sensor"
"cs.detect_color() - return the detected color"
"------------------------"
"Controller Functions"

"controller.connect() - connect to the controller"
"------------------------"

