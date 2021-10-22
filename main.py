#!/usr/bin/env python3

print("Loading libs... ", end="")
from time import sleep

from ev3dev2.motor import *
from ev3dev2.sensor import *
from ev3dev2.sensor.lego import *
from ev3dev2.led import *
from ev3dev2.sound import *
print("done.")

CLAW_RANGE   = 2500
CLAW_LIFT_RANGE = 90

claw_lift = LargeMotor(OUTPUT_D)
claw      = MediumMotor(OUTPUT_A)
tank_drive = MoveTank(OUTPUT_B, OUTPUT_C)

def force_claw_lift_down():
    claw_lift.on(-25)
    while not claw_lift.is_stalled:
        pass
    claw_lift.reset()
def set_claw_lift(position):
    claw_lift.on_to_position(
            40 if position.lower()=="down" else 75,
            0 if position.lower()=="down" else CLAW_LIFT_RANGE)

def force_claw_closed():
    claw.on(-100)
    while not claw.is_stalled:
        pass
    claw.reset()
def set_claw(position):
    claw.on_to_position(
            100,
            0 if position.lower()=="closed" else CLAW_RANGE)


force_claw_closed()
force_claw_lift_down()
