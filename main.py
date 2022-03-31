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

from config import *
print("done.")

try: # device configuration check
    claw_lift = LargeMotor(OUTPUT_D)
    claw      = MediumMotor(OUTPUT_A)
    tank_drive = MoveTank(OUTPUT_B, OUTPUT_C)

    ultrasound = UltrasonicSensor(INPUT_4)
    ultrasound.mode = UltrasonicSensor.MODE_US_DIST_CM

    color_left = ColorSensor(INPUT_3)
    color_right = ColorSensor(INPUT_2)
    color_left.mode = ColorSensor.MODE_COL_COLOR
    color_right.mode = ColorSensor.MODE_COL_COLOR

    ROTPOS_360 /= tank_drive.left_motor.count_per_rot # hacky and i know it
except ev3dev2.DeviceNotFound: # module not connected, alert and exit
    Sound().beep("-f 220")
    exit(2)


display = Display()
buttons = Button()
sound = Sound()
leds = Led()


def force_claw_lift_down():
    """
    Forces the claw lift down, periodically checking if it is stalled.
    When this happens, it breaks.
    """
    claw_lift.on(-25)
    while not claw_lift.is_stalled:
        sleep(0.01)
    claw_lift.reset()

def set_claw_lift(position):
    """
    Sets the clas lift position. Pass 'up' or 'down'.
    """
    claw_lift.on_to_position(
            40 if position.lower()=="down" else 75,
            0 if position.lower()=="down" else CLAW_LIFT_RANGE)


def force_claw_closed():
    """
    Forces the claw closed, periodically checking if it is stalled.
    When this happens, it breaks.
    """
    claw.on(-100)
    while not claw.is_stalled:
        sleep(0.01)
    claw.reset() # make post-stalling movement work before final reset
    claw.on_for_seconds(100, 0.5) # release pressure
    claw.reset()

def set_claw(position):
    """
    Sets the claw's state. Pass 'open' or 'closed'.
    """
    claw.on_to_position(
            100,
            0 if position.lower()=="closed" else CLAW_RANGE)


def read_green_markers(): # read markers and return as 2-bit number bcuz i like complicated shit that i will hate myself for after
    """
    Wrapper that reads the current state of the markers.
    Outputs a 2-bit number, high bit represents the left.
    """
    return ((color_left.color == ColorSensor.COLOR_GREEN) << 1) \
          | (color_right.color == ColorSensor.COLOR_GREEN)

def eval_color(color):
    r, g, b = color
    min_diff = 256*3
    out = 0
    for c in COLORS:
        t, h, n = c
        diff = abs(r-t) \
             + abs(g-h) \
             + abs(b-n)
        if diff < min_diff:
            min_diff = diff
            out = c
    return out

def snoop(): # try finding a maximum amount of markers
    """
    Move the robo around in an attempt to find a maximum of markers.
    Outputs in the same format as 'read_green_markers()'.
    """
    tank_drive.stop()
    sound.beep() # emotional support beep
    tank_drive.on_for_rotations(50, 50, 5 * TIRE_CONST) # drive a little bit back
    output = read_green_markers() # initialize output, will be expanded during the actual snooping

    tank_drive.on(-25, 25) # start turning right
    start = time.time()
    while color_left.color != ColorSensor.COLOR_BLACK and time.time() - start <= 0.4 * TIME_CONST:
        output |= read_green_markers()
    total1 = time.time() - start # total time rotating right

    tank_drive.on(25, -25) # start turning left
    start = time.time()
    while color_right.color != ColorSensor.COLOR_BLACK and time.time() - start <= 0.8 * TIME_CONST: # check but with double the time
        output |= read_green_markers()
    total2 = time.time() - start # total time rotating left

    tank_drive.stop()
    if total2-total1 > 0: # reset to original rotation using the 2 rotation values
        tank_drive.on_for_seconds(-25, 25, total2-total1)
    if total2-total1 < 0:
        tank_drive.on_for_seconds(25, -25, total1-total2)

    if output: # found marker(s)!
        sound.beep("-f 880") # VERY emotional support beep
    tank_drive.on_for_rotations(-50, -50, 5 * TIRE_CONST) # reset to original position

    return output

def handle_snooped(snooped):
    """
    Moves and rotates the robo acording to the passed values (should be from 'snooped()').
    """
    if snooped == MARKER_FOUND_B:
        tank_drive.on_for_rotations(25, 25, 80 * TIRE_CONST) # move forward as to be exactly on top of the intersection
        tank_drive.on_for_rotations(50, -50, 180 * ROTPOS_360) # rotate
        tank_drive.on_for_rotations(-25, -25, 5 * TIRE_CONST) # move back to be closer to the intersection b4 starting again
    elif snooped == MARKER_FOUND_L:
        tank_drive.on_for_rotations(25, 25, 80 * TIRE_CONST)
        tank_drive.on_for_rotations(50, -50, 90 * ROTPOS_360)
        tank_drive.on_for_rotations(-25, -25, 5 * TIRE_CONST)
    elif snooped == MARKER_FOUND_R:
        tank_drive.on_for_rotations(25, 25, 80 * TIRE_CONST)
        tank_drive.on_for_rotations(-50, 50, 90 * ROTPOS_360)
        tank_drive.on_for_rotations(-25, -25, 5 * TIRE_CONST)


def handle_intersection():
    """
    Handles intersection and intersection-like markings.
    Returns True if an intersection is found.
    """
    global check_for_black # OOOOOOO scary global var

    if color_left.color == color_right.color == ColorSensor.COLOR_BLACK == check_for_black: # we hit a black line at 90 degs
        tank_drive.on_for_rotations(-25, -25, 30 * TIRE_CONST) # check if we missed green markers
        markers = snoop()
        if not markers: # Could've used beautiful walross operator, but our ev3dev has <3.8 Python
            tank_drive.on_for_rotations(25, 25, 110 * TIRE_CONST) # nothing missed, move back forward + 70 mm
            start, found = time.time(), False
            tank_drive.on(50, -50) # rotate to check if there is black
            while time.time() <= start + 0.4 * TIME_CONST:
                if color_right.color == ColorSensor.COLOR_BLACK:
                    found = True
                    break
            if not found: # nothing found, move back
                tank_drive.on_for_seconds(-50, 50, 0.4 * TIME_CONST)
                tank_drive.on_for_rotations(-25, -25, 70 * TIRE_CONST)
                check_for_black = False
                return False
            return True
        handle_snooped(markers)
        return True

    if ColorSensor.COLOR_GREEN in [color_left.color, color_right.color]: # found marker directly
        markers = snoop()
        handle_snooped(markers)
        return True
    return False

def handle_obstacle():
    tank_drive.stop()
    count = 0
    found_hole = False
    for _ in range(32): # max number of steps
        if ultrasound.distance_centimeters >= 20:
            tank_drive.on_for_rotations(-50, 50, 90 * ROTPOS_360)
            tank_drive.on_for_rotations(25, 25, 60 * TIRE_CONST)
            tank_drive.on_for_rotations(50, -50, 90 * ROTPOS_360)
            found_hole = True
            break

        tank_drive.on_for_rotations(-50, 50, 90 * ROTPOS_360)

        if ultrasound.distance_centimeters <= 18:
            tank_drive.on_for_rotations(50, -50, 90 * ROTPOS_360)
            break

        tank_drive.on_for_rotations(25, 25, 200 * TIRE_CONST)
        tank_drive.on_for_rotations(50, -50, 90 * ROTPOS_360)
        count += 1

    if not found_hole:
        tank_drive.on_for_rotations(50, -50, 90 * ROTPOS_360)
        tank_drive.on_for_rotations(25, 25, 200 * count * TIRE_CONST)
        count = 0
        for _ in range(32): # max number of steps
            if ultrasound.distance_centimeters >= 20:
                tank_drive.on_for_rotations(50, -50, 90 * ROTPOS_360)
                tank_drive.on_for_rotations(25, 25, 60 * TIRE_CONST)
                tank_drive.on_for_rotations(-50, 50, 90 * ROTPOS_360)
                found_hole = True
                break

            tank_drive.on_for_rotations(50, -50, 90 * ROTPOS_360)
            tank_drive.on_for_rotations(25, 25, 200 * TIRE_CONST)
            tank_drive.on_for_rotations(-50, 50, 90 * ROTPOS_360)
            count -= 1

    tank_drive.on_for_rotations(25, 25, 550 * TIRE_CONST)

    if count > 0:
        tank_drive.on_for_rotations(50, -50, 90 * ROTPOS_360)
    if count < 0:
        tank_drive.on_for_rotations(-50, 50, 90 * ROTPOS_360)

    tank_drive.on_for_rotations(25, 25, 200 * abs(count) * TIRE_CONST)

    if count > 0:
        tank_drive.on_for_rotations(-50, 50, 90 * ROTPOS_360)
    if count < 0:
        tank_drive.on_for_rotations(50, -50, 90 * ROTPOS_360)

def main():
    """
    Main function of the robo.
    """
    global check_for_black

    print("Initializing claw... ", end="")
    force_claw_lift_down()
    set_claw_lift("up")
    force_claw_closed()
    set_claw("open")
    print("done.\nWaiting for start signal... ", end="")
    buttons.wait_for_bump("enter")
    print("received.")

    while True:
        check_for_black = True # set up for handle_intersection()
        broken = False # there has got to be a better way to do this

        if ColorSensor.COLOR_NOCOLOR in [color_left.color, color_right.color]: # invalid readings, stop!
            tank_drive.stop()
        elif ultrasound.distance_centimeters < 14: # we VERY close to a (suspected) wall
            handle_obstacle()

        elif handle_intersection(): # handle_intersection() has found sth and reacted to it! start the loop again
            continue

        elif color_left.color == ColorSensor.COLOR_BLACK: # turn left
            tank_drive.stop()
            while color_left.color == ColorSensor.COLOR_BLACK:
                if handle_intersection(): # check for intersection
                    broken = True
                    break
                tank_drive.on(50, -25)
            if broken: # handle_intersection() was triggered, start again
                continue

            start = time.time()
            while time.time()-start <= 0.3 * TIME_CONST: # drive a little bit further than necessary as to center on the line
                if handle_intersection():
                    break
                if color_right.color == ColorSensor.COLOR_BLACK:
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
                if color_left.color == ColorSensor.COLOR_BLACK:
                    break
                tank_drive.on(-25, 50)

        # TODO: trigger when ball room is detected

        else:
            tank_drive.on(50, 50)

    print("Program finished.")

if __name__ == "__main__":
    main()
