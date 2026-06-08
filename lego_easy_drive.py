from lego_easy import Motor, Robot, ColorSensor, Controller, wait
from lego_easy import COLOR_RED, COLOR_GREEN, COLOR_BLUE

MY_CARD = "1128"

robot = Robot(MY_CARD, speed=100)
controller = Controller(MY_CARD)

for i in range(500):
    controller.drive_robot(robot)
    wait(0.1)
robot.stop()