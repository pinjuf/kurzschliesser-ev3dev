#!/usr/bin/env python3

print("Loading libs... ", end="")
from time import time, sleep

import ev3dev2
from ev3dev2.motor import *
from ev3dev2.sensor import *
from ev3dev2.sensor.lego import *
from ev3dev2.led import *
from ev3dev2.sound import *
from ev3dev2.button import *
from ev3dev2.display import *
print("done.")

try:
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
except ev3dev2.DeviceNotFound:
    Sound().beep("-f 220")
    exit(2)

tank_drive.on(50, -50)
while color_right.color != ColorSensor.COLOR_BLACK:
    time.sleep(0.01)
start = time.time()
while color_right.color == ColorSensor.COLOR_BLACK:
    time.sleep(0.01)
while color_right.color != ColorSensor.COLOR_BLACK:
    time.sleep(0.01)
stop = time.time()
tank_drive.off()

"""
Calculate the DPS

The whole rotation over the time,
and then everything over the 50% power
"""

DPS = 360/((stop-start)*50) 
with open("dps", "w") as file:
    file.write(str(DPS))
