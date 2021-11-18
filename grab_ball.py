#!/usr/bin/env python3

from time import time, sleep

from ev3dev2.motor import *
from ev3dev2.sensor import *
from ev3dev2.sensor.lego import *
from ev3dev2.led import *
from ev3dev2.sound import *
from ev3dev2.button import *
from ev3dev2.display import *
from main import *

def grab_ball():
    #turn 180 degrees
    tank_drive.on_for_seconds(50, -50, 180/(DPS * 50))

    set_claw("open")       #open claws
    set_claw_lift("down")
    set_claw("closed")      #close claws
    set_claw_lift("up")
    return