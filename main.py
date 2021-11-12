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

DPS = 2.0 # degrees per second on 1% power
TIRE_RAD = 17.5 # mm
TIME_CONST = 1 # TODO TEMPORARY! USED FOR TIMED ROTATION! TO BE REPLACED WITH POSITIONAL INPUT INSTEAD OF TIME

TIRE_CONST = 1 / (2 * 3.14159 * TIRE_RAD)

CLAW_RANGE   = 2500
CLAW_LIFT_RANGE = 110

MARKER_FOUND_L = 0b10
MARKER_FOUND_R = 0b01
MARKER_FOUND_B = 0b11

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
sound = Sound()
leds = Led()

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

def read_green_markers(): # read markers and return as 2-bit number bcuz i like complicated shit that i will hate myself for after
    return ((color_left.color == ColorSensor.COLOR_GREEN) << 1) \
          | (color_right.color == ColorSensor.COLOR_GREEN)

def snoop(): # try finding a maximum amount of markers
    sound.beep() # emotional support beep
    output = read_green_markers()
    tank_drive.on(-25, 25) # turn right
    start = time.time()
    while color_left.color != ColorSensor.COLOR_BLACK and time.time() - start <= 0.4 * TIME_CONST:
        output |= read_green_markers()
    total1 = time.time() - start
    tank_drive.on(25, -25)
    start = time.time()
    while color_right.color != ColorSensor.COLOR_BLACK and time.time() - start <= 0.8 * TIME_CONST:
        output |= read_green_markers()
    total2 = time.time() - start
    if total2-total1 >= 0:
        tank_drive.on_for_seconds(-25, 25, total2-total1)
    if total2-total1 < 0:
        tank_drive.on_for_seconds(25, -25, total1-total2)
    return output
    
def handle_snooped(snooped):
    if snooped == MARKER_FOUND_B:
       tank_drive.on_for_seconds(25, 25, 80 * TIRE_CONST)
       tank_drive.on_for_seconds(50, -50, 180/(DPS * 50))
       tank_drive.on_for_rotations(-25, -25, 5 * TIRE_CONST) # move back to be closer to the intersection b4 starting again
    elif snooped == MARKER_FOUND_L:
       tank_drive.on_for_seconds(25, 25, 120 * TIRE_CONST)
       tank_drive.on_for_seconds(50, -50, 90/(DPS * 50))
       tank_drive.on_for_rotations(-25, -25, 5 * TIRE_CONST)
    elif snooped == MARKER_FOUND_R:
       tank_drive.on_for_seconds(25, 25, 120 * TIRE_CONST)
       tank_drive.on_for_seconds(-50, 50, 90/(DPS * 50))
       tank_drive.on_for_rotations(-25, -25, 5 * TIRE_CONST)
    tank_drive.off()

def handle_intersection(): # move back to be closer to the intersection b4 starting again
    global check_for_black
    if color_left.color == color_right.color == ColorSensor.COLOR_BLACK == check_for_black: # we hit a black line at 90 degs
        tank_drive.stop()
        tank_drive.on_for_seconds(-25, -25, 40 * TIRE_CONST) # check if we missed green markers
        if not snoop():
            tank_drive.on_for_seconds(25, 25, 90 * TIRE_CONST) # nothing missed, move back forward + 60 mm
            start, found = time.time(), False
            tank_drive.on(50, -50) # rotate to check if there is black
            while time.time() <= start + 0.4 * TIME_CONST:
                if color_right.color == ColorSensor.COLOR_BLACK:
                    found = True
                    break
            if not found: # nothing found, move back
                tank_drive.on_for_seconds(-50, 50, 0.4 * TIME_CONST)
                tank_drive.on_for_seconds(-25, -25, 50 * TIRE_CONST)
                check_for_black = False
                return False
            tank_drive.off()
            markers = snoop()
            if markers: # Could've used beautiful walross operator, but our ev3dev has <3.8 Python
                handle_snooped(markers)
            return True
    if ColorSensor.COLOR_GREEN in [color_left.color, color_right.color]:
        tank_drive.stop()
        markers = snoop()
        handle_snooped(markers)
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
    check_for_black = True
    broken = False
    if ColorSensor.COLOR_NOCOLOR in [color_left.color, color_right.color]:
        tank_drive.stop()
    elif ultrasound.distance_centimeters < 9:
        tank_drive.on_for_seconds(50, -50, 180/(DPS * 50))

    elif handle_intersection():
        continue

    elif color_left.color == ColorSensor.COLOR_BLACK: # turn left
        tank_drive.stop()
        while color_left.color == ColorSensor.COLOR_BLACK:
            if handle_intersection(): # check for intersection
                broken = True
                break
            tank_drive.on(50, -25)
        if broken:
            continue
        start = time.time()
        while time.time()-start <= 0.3 * TIME_CONST: # time padding
            if handle_intersection():
                break
            tank_drive.on(50, -25)
    elif color_right.color == ColorSensor.COLOR_BLACK: # turn right
        tank_drive.stop()
        while color_right.color == ColorSensor.COLOR_BLACK:
            if handle_intersection():
                broken = True
                break
            tank_drive.on(-25, 50)
        if broken:
            continue
        start = time.time()
        while time.time()-start <= 0.3 * TIME_CONST:
            if handle_intersection():
                break
            tank_drive.on(-25, 50)

    else:
        tank_drive.on(50, 50)

print("Program finished.")
