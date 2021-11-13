#!/usr/bin/env python3

from time import time, sleep

from ev3dev2.motor import *
from ev3dev2.sensor import *
from ev3dev2.sensor.lego import *
from ev3dev2.led import *
from ev3dev2.sound import *
from ev3dev2.button import *
from ev3dev2.display import *

REFLECTION_LIMIT = 50   #Limit of dead and alive balls

tank_drive = MoveTank(OUTPUT_B, OUTPUT_C)

ultrasound = UltrasonicSensor(INPUT_4)
ultrasound.mode = UltrasonicSensor.MODE_US_DIST_CM

color_ball = ColorSensor(INPUT_1)
color_ball.mode = ColorSensor.MODE_COL_REFLECT

def check_for_ball():
    return color_ball.reflected_light_intensity > REFLECTION_LIMIT

def grab_ball():
    #TODO: implement ball grabbing with claws
    return

def search():
    tank_drive.on(50, 50)
    while ball_found == false:
        if ultrasound.distance_centimeters < 3:  # Check for ball/wall
            if check_for_ball():
                grab_ball();
            else:   #turn right twice
                tank_drive.off()
                tank_drive.on_for_rotations(-50, -50, 10 * TIRE_CONST)
                tank_drive.on_for_seconds(50, -50, 90/(DPS * 50))
                tank_drive.on_for_rotations(50, 50, 5 * TIRE_CONST)
                tank_drive.on_for_seconds(50, -50, 90/(DPS * 50))
                tank_drive.on(50, 50)
