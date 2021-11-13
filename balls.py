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

tank_drive = MoveTank(OUTPUT_B, OUTPUT_C)
claw_lift = LargeMotor(OUTPUT_D)
claw      = MediumMotor(OUTPUT_A)

ultrasound = UltrasonicSensor(INPUT_4)
ultrasound.mode = UltrasonicSensor.MODE_US_DIST_CM

color_ball = ColorSensor(INPUT_1)
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

def search_release_area():
    return

def search():
    tank_drive.on(50, 50)
    while ball_found == false:
        if ultrasound.distance_centimeters < ULATRASOUND_DISTANCE:  # check for ball/wall
            if check_for_ball():
                grab_ball()
                search_release_area()
            else:   #turn right twice
                #tank_drive.off()
                tank_drive.on_for_rotations(-50, -50, 5 * TIRE_CONST)  #drive back to avoid wall contact
                tank_drive.on_for_seconds(50, -50, 90/(DPS * 50))       #turn 90 degres
                tank_drive.on_for_rotations(50, 50, 5 * TIRE_CONST)     #drive forward to next line
                tank_drive.on_for_seconds(50, -50, 90/(DPS * 50))       #turn 90 degres
                tank_drive.on(50, 50)                                   #start main movement
