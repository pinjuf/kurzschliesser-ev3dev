#!/usr/bin/env python3

from time import time, sleep

from ev3dev2.motor import *
from ev3dev2.sensor import *
from ev3dev2.sensor.lego import *
from ev3dev2.led import *
from ev3dev2.sound import *
from ev3dev2.button import *
from ev3dev2.display import *
from main import set_claw, set_claw_lift

REFLECTION_LIMIT = 50       #Limit of dead and alive balls
ULATRASOUND_DISTANCE = 2    #Distance to wall/ball in cm to see ball using light sensor

direction = 0               #used to turn in right direction after line finished

tank_drive = MoveTank(OUTPUT_B, OUTPUT_C)
claw_lift = LargeMotor(OUTPUT_D)
claw      = MediumMotor(OUTPUT_A)

ultrasound = UltrasonicSensor(INPUT_4)
ultrasound.mode = UltrasonicSensor.MODE_US_DIST_CM

color_left = ColorSensor(INPUT_3)
color_right = ColorSensor(INPUT_2)
color_ball = ColorSensor(INPUT_1)
color_left.mode = ColorSensor.MODE_COL_COLOR
color_right.mode = ColorSensor.MODE_COL_COLOR
color_ball.mode = ColorSensor.MODE_COL_REFLECT


def check_for_ball():
    return color_ball.reflected_light_intensity > REFLECTION_LIMIT

def grab_ball():
    #drive back and turn 180 degrees
    tank_drive.on_for_rotations(-50, -50, 5 * TIRE_CONST)
    tank_drive.on_for_seconds(50, -50, 180/(DPS * 50))

    set_claw_lift("down")       #open claws
    set_claw("open")
    tank_drive.on_for_rotations(-50, -50, 5 * TIRE_CONST)   #grab ball
    set_claw("closed")          #close claws
    set_claw_lift("up")
    return

def search_evacuation_zone():
    #TODO: find fast algorithm to find black line
    return

def is_on_border_line(check_black):
    #TODO: check if silver counts as gray, if not change mode to reflect to check it
    return ((color_right.color == ColorSensor.COLOR_BLACK or color_left.color == ColorSensor.COLOR_BLACK) if check_black else False) or color_right.color == ColorSensor.COLOR_GRAY or color_left.color == ColorSensor.COLOR_GRAY or color_right.color == ColorSensor.GREEN or color_left.color == ColorSensor.GREEN

def next_line():
    tank_drive.on_for_rotations(-50, -50, 5 * TIRE_CONST)  #drive back
    tank_drive.on_for_seconds(50, -50, (90 if direction==0 else -90) /(DPS * 50))       #turn 90 degres
    tank_drive.on_for_rotations(50, 50, 5 * TIRE_CONST)     #drive forward to next line
    tank_drive.on_for_seconds(50, -50, (90 if direction==0 else -90)/(DPS * 50))       #turn 90 degres
    tank_drive.on(50, 50)                                   #start main movement
    direction = 1-direction

def search():
    tank_drive.on(50, 50)
    while ball_found == false:
        if is_on_border_line(True): #Drive back -> next line
            next_line()
        if ultrasound.distance_centimeters < ULATRASOUND_DISTANCE:  # check for ball/wall
            if check_for_ball():
                grab_ball()
                search_evacuation_zone()
            else:   #turn right twice
                next_line()
