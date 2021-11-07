#!/usr/bin/env python3

print("Loading libs... ", end="")
from time import time, sleep

from ev3dev2.motor import *
from ev3dev2.sensor import *
from ev3dev2.sensor.lego import *
from ev3dev2.led import *
from ev3dev2.sound import *
from ev3dev2.button import *
from ev3dev2.display import *
print("done.")

DPS_50 = 82.5 # degrees per second on full rotation with 50% power

CLAW_RANGE   = 2500
CLAW_LIFT_RANGE = 90

claw_lift = LargeMotor(OUTPUT_D)
claw      = MediumMotor(OUTPUT_A)
tank_drive = MoveTank(OUTPUT_B, OUTPUT_C)

ultrasound = UltrasonicSensor(INPUT_4)
ultrasound.mode = UltrasonicSensor.MODE_US_DIST_CM

color_left = ColorSensor(INPUT_3)
color_right = ColorSensor(INPUT_2)
color_ball = ColorSensor(INPUT_1)
color_left.mode = ColorSensor.MODE_COL_COLOR
color_right.mode = ColorSensor.MODE_COL_COLOR
color_ball.mode = ColorSensor.MODE_COL_REFLECT

display = Display()
buttons = Button()

def force_claw_lift_down():
    claw_lift.on(-25)
    while not claw_lift.is_stalled:
        sleep(0.01)
    claw_lift.reset()
def set_claw_lift(position):
    claw_lift.on_to_position(
            40 if position.lower()=="down" else 75,
            0 if position.lower()=="down" else CLAW_LIFT_RANGE)

def force_claw_closed():
    claw.on(-100)
    while not claw.is_stalled:
        sleep(0.01)
    claw.reset() # make post-stalling movement work befire final reset
    claw.on_for_seconds(100, 0.5) # release pressure
    claw.reset()
def set_claw(position):
    claw.on_to_position(
            100,
            0 if position.lower()=="closed" else CLAW_RANGE)

def handle_intersection():
    global check_for_black
    if color_left.color == color_right.color == ColorSensor.COLOR_BLACK == check_for_black: # we hit a black line at 90 degs
        tank_drive.stop()
        tank_drive.on_for_seconds(25, 25, 0.75)
        tank_drive.on_for_seconds(50, -50, 0.2) # check if there is black
        if color_right.color != ColorSensor.COLOR_BLACK:
            tank_drive.on_for_seconds(-50, 50, 0.2)
            tank_drive.on_for_seconds(-25, -25, 0.75)
            check_for_black = 0
            return False
        return True
    if ColorSensor.COLOR_GREEN in [color_left.color, color_right.color]:
        sleep(0.1) # make sure we are totally on the markers
        tank_drive.stop()
        if color_left.color == ColorSensor.COLOR_GREEN and \
           color_right.color == ColorSensor.COLOR_GREEN:
               tank_drive.on_for_seconds(50, -50, 180/DPS_90)
        elif color_left.color == ColorSensor.COLOR_GREEN:
               tank_drive.on_for_seconds(25, 25, 1.25)
               tank_drive.on_for_seconds(50, -50, 90/DPS_50)
               tank_drive.on_for_seconds(-25, -25, 0.4)
        elif color_right.color == ColorSensor.COLOR_GREEN:
               tank_drive.on_for_seconds(25, 25, 1.25)
               tank_drive.on_for_seconds(-50, 50, 90/DPS_50)
               tank_drive.on_for_seconds(-25, -25, 0.4)
        return True
    return False



print("Initializing claw... ", end="")
force_claw_lift_down()
set_claw_lift("up")
force_claw_closed()
set_claw("open")
print("done.\nWaiting for start signal... ", end="")
buttons.wait_for_bump("enter")
print("received.")

while True:
    check_for_black = 1
    if ColorSensor.COLOR_NOCOLOR in [color_left.color, color_right.color]:
        tank_drive.stop()
    elif ultrasound.distance_centimeters < 9:
        tank_drive.on_for_seconds(50, -50, 180/DPS_50)

    elif handle_intersection():
        continue

    elif color_left.color == ColorSensor.COLOR_BLACK: # turn left
        tank_drive.stop()
        while color_left.color == ColorSensor.COLOR_BLACK:
            if handle_intersection(): # check for intersection
                break
            tank_drive.on(50, -25)
        start = time.time()
        while time.time()-start <= 0.3: # time padding
            if handle_intersection():
                break
            tank_drive.on(50, -25)
    elif color_right.color == ColorSensor.COLOR_BLACK: # turn right
        tank_drive.stop()
        while color_right.color == ColorSensor.COLOR_BLACK:
            if handle_intersection():
                break
            tank_drive.on(-25, 50)
        start = time.time()
        while time.time()-start <= 0.3:
            if handle_intersection():
                break
            tank_drive.on(-25, 50)
        tank_drive.on(50, 50)

    else:
        tank_drive.on(50, 50)

print("Program finished.")
