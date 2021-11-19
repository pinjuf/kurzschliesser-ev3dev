#!/usr/bin/env python3

from time import time, sleep
from balls import grab_ball

from ev3dev2.motor import *
from ev3dev2.sensor import *
from ev3dev2.sensor.lego import *
from ev3dev2.led import *
from ev3dev2.sound import *
from ev3dev2.button import *
from ev3dev2.display import *
from main import *
from balls import *

force_claw_closed()
force_claw_lift_down()
grab_ball()
