#!/usr/bin/env python3

print("Loading libs... ", end="")

from time import time, sleep
from math import *

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

def init():
    global claw_lift, claw
    global tank_drive
    global ultrasound
    global color_left, color_right
    global gyro
    global display, buttons, sound, leds

    try: # device configuration check :) 8=)
        claw_lift = LargeMotor(OUTPUT_D)
        claw      = MediumMotor(OUTPUT_A)
        tank_drive = MoveTank(OUTPUT_B, OUTPUT_C)

        ultrasound = UltrasonicSensor(INPUT_4)
        ultrasound.mode = UltrasonicSensor.MODE_US_DIST_CM

        color_left = ColorSensor(INPUT_3)
        color_right = ColorSensor(INPUT_2)
        color_left.mode = ColorSensor.MODE_COL_COLOR
        color_right.mode = ColorSensor.MODE_COL_COLOR

        gyro = GyroSensor(INPUT_1)
        tank_drive.gyro = gyro
    except ev3dev2.DeviceNotFound: # module not connected, alert and exit
        Sound().beep("-f 220")
        exit(2)

    display = Display()
    buttons = Button()
    sound = Sound()
    leds = Led()

def stop_beep_continue():
    speed_a, speed_b = tank_drive.left_motor.speed_sp, tank_drive.right_motor.speed_sp
    tank_drive.off()
    sound.beep("-f 440")
    tank_drive.on(100*speed_a/tank_drive.left_motor.max_speed, 100*speed_b/tank_drive.right_motor.max_speed)

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
            0 if position.lower()=="down" else CLAW_LIFT_RANGE, block=False)
    while claw_lift.is_running:
        if claw_lift.is_stalled:
            return


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
            0 if position.lower()=="closed" else CLAW_RANGE, block=False)
    while claw_lift.is_running:
        if claw_lift.is_stalled:
            return


def read_green_markers(): # read markers and return as 2-bit number bcuz i like complicated shit that i will hate myself for after
    """
    Wrapper that reads the current state of the markers.
    Outputs a 2-bit number, high bit represents the left.
    """
    return ((color_left.color == ColorSensor.COLOR_GREEN) << 1) \
          | (color_right.color == ColorSensor.COLOR_GREEN)

def eval_color(color):
    """
    Evaluate a RGB color tuple.
    """
    r, g, b = color
    maxc    = min(max(color), 100) # Extrapolate to 255
    r *= 255/maxc
    g *= 255/maxc
    b *= 255/maxc

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
    #sound.beep() # emotional support beep
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

    #if output: # found marker(s)!
        #sound.beep("-f 880") # VERY emotional support beep
    tank_drive.on_for_rotations(-50, -50, 5 * TIRE_CONST) # reset to original position

    return output

def handle_snooped(snooped):
    """
    Moves and rotates the robo acording to the passed values (should be from 'snooped()').
    """
    if snooped == MARKER_FOUND_B:
        tank_drive.on_for_rotations(25, 25, 90 * TIRE_CONST) # move forward as to be exactly on top of the intersection
        tank_drive.turn_degrees(50, 180)
        tank_drive.on_for_rotations(25, 25, 25 * TIRE_CONST) # move forward to awoid green markers
    elif snooped == MARKER_FOUND_L:
        tank_drive.on_for_rotations(25, 25, 90 * TIRE_CONST)
        tank_drive.turn_degrees(-50, -90)
        tank_drive.on_for_rotations(25, 25, 25 * TIRE_CONST)
    elif snooped == MARKER_FOUND_R:
        tank_drive.on_for_rotations(25, 25, 90 * TIRE_CONST)
        tank_drive.turn_degrees(-50, 90)
        tank_drive.on_for_rotations(25, 25, 25 * TIRE_CONST)


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
            tank_drive.on_for_rotations(25, 25, 90 * TIRE_CONST) # nothing missed, move back forward + 60 mm

            if last_turn == "right":
                start, found = time.time(), False
                tank_drive.on(50, -50) # rotate to check if there is black
                while time.time() <= start + 0.6 * TIME_CONST:
                    if color_right.color == ColorSensor.COLOR_BLACK:
                        found = True
                        break

                    if color_left.color == ColorSensor.COLOR_BLACK:
                        while color_left.color == ColorSensor.COLOR_BLACK:
                            pass
                        tank_drive.on_for_rotations(25, 25, 30 * TIRE_CONST)
                        return True

            if last_turn == "left":
                start, found = time.time(), False
                tank_drive.on(-50, 50)
                while time.time() <= start + 0.6 * TIME_CONST:
                    if color_left.color == ColorSensor.COLOR_BLACK:
                        found = True
                        break

                    if color_right.color == ColorSensor.COLOR_BLACK:
                        while color_right.color == ColorSensor.COLOR_BLACK:
                            pass
                        tank_drive.on_for_rotations(25, 25, 30 * TIRE_CONST)
                        return True

            if not found: # nothing found, check ttrig and/or move back
                if last_turn == "right":
                    tank_drive.on_for_seconds(-50, 50, 0.6 * TIME_CONST)
                if last_turn == "left":
                    tank_drive.on_for_seconds(50, -50, 0.6 * TIME_CONST)

                tank_drive.on_for_rotations(-25, -25, 65 * TIRE_CONST)
                check_for_black = False
                return False
            else:
                tank_drive.on_for_rotations(25, 25, 5 * TIRE_CONST)
            return True

        handle_snooped(markers)
        return True

    if ColorSensor.COLOR_GREEN in [color_left.color, color_right.color]: # found marker directly
        markers = snoop()
        handle_snooped(markers)
        return True
    return False

def handle_obstacle():
    """
    The robot is facing an obstacle head on and has to drive around it.
    """
    tank_drive.stop()
    count = 0
    found_hole = False
    for _ in range(3): # max number of steps
        if ultrasound.distance_centimeters >= 20:
            tank_drive.turn_degrees(-50, 90) # turn right
            tank_drive.on_for_rotations(25, 25, 60 * TIRE_CONST)
            tank_drive.turn_degrees(-50, -90) # turn left
            found_hole = True
            break

        tank_drive.turn_degrees(-50, 90)

        if ultrasound.distance_centimeters <= 20:
            tank_drive.turn_degrees(-50, -90)
            break

        tank_drive.on_for_rotations(25, 25, 200 * TIRE_CONST)
        tank_drive.turn_degrees(-50, -90)
        count += 1

    if not found_hole:
        tank_drive.turn_degrees(-50, -90)
        tank_drive.on_for_rotations(25, 25, 200 * count * TIRE_CONST)
        count = 0
        for _ in range(3): # max number of steps
            if ultrasound.distance_centimeters >= 20:
                tank_drive.turn_degrees(-50, -90)
                tank_drive.on_for_rotations(25, 25, 60 * TIRE_CONST)
                tank_drive.turn_degrees(-50, 90)
                found_hole = True
                break

            tank_drive.turn_degrees(-50, -90)
            tank_drive.on_for_rotations(25, 25, 200 * TIRE_CONST)
            tank_drive.turn_degrees(-50, 90)
            count -= 1

    tank_drive.on_for_rotations(25, 25, 550 * TIRE_CONST)

    if count > 0:
        tank_drive.turn_degrees(-50, -90)
    if count < 0:
        tank_drive.turn_degrees(-50, 90)

    tank_drive.on_for_rotations(25, 25, 200 * abs(count) * TIRE_CONST)

    if count > 0:
        tank_drive.turn_degrees(-50, 90)
    if count < 0:
        tank_drive.turn_degrees(-50, -90)


def calibrate_and_ready():
    print("Initializing claw... ", end="")
    force_claw_lift_down()
    set_claw_lift("up")
    force_claw_closed()
    set_claw("open")

    print("done.\nWaiting for calibration signal... ", end="")
    buttons.wait_for_bump("enter")
    gyro.calibrate()
    sound.beep()

    if RESCUE_KIT:
        print("done.\nWaiting for pickup rescue kit signal... ", end="")
        buttons.wait_for_bump("enter")
        set_claw("closed")
        sound.beep()

    print("done.\nWaiting for start signal...", end="")
    buttons.wait_for_bump("enter")
    print("received.")

def banzai_into_wall():
    tank_drive.on_for_rotations(50, 50, (ultrasound.distance_centimeters * 10.0) * TIRE_CONST)  # to drive into the wall

    for _ in range(4):
        tank_drive.left_motor.on_for_seconds(75, 1)
        tank_drive.right_motor.on_for_seconds(75, 1)

def finish():
    def end():
        tank_drive.turn_degrees(-50, 180)
        set_claw_lift("down")
        set_claw("open")
        sound.beep("-f 440 -l 2000")
        exit(0)

    # check function
    check_green = lambda: ColorSensor.COLOR_GREEN in [color_left.color, color_right]

    tank_drive.on_for_rotations(50, 50, 50 * TIRE_CONST)
    tank_drive.turn_degrees(-50, 90)
    tank_drive.on_for_rotations(50, 50, 50 * TIRE_CONST)
    tank_drive.turn_degrees(-50, 90)
    if check_green():
        end()

    for _ in range(12):
        tank_drive.on_for_rotations(100, 100, 50 * TIRE_CONST)
        tank_drive.turn_degrees(-50, 90)
        if check_green():
            end()
    end()

def drive_to_corner():
    find_shortest_distance_to_next_wall()
    tank_drive.turn_degrees(50, 90)
    find_shortest_distance_to_next_wall()
    tank_drive.turn_degrees(50, 180)

def spiral_algo():
    length = 1000
    delta = 75

    while length > 0:
        for _ in range(2):
            set_claw_lift("up")
            tank_drive.on_for_rotations(-50, -50, length * TIRE_CONST)
            set_claw("open")
            set_claw_lift("down")
            tank_drive.turn_degrees(-50, 90)

        length -= delta

    set_claw_lift("down")

def resc_orientate():
    tank_drive.on_for_rotations(-50, -50, 100 * TIRE_CONST)
    tank_drive.turn_degrees(-50, 90)
    tank_drive.on_for_rotations(50, 50, (ultrasound.distance_centimeters * 10 -100) * TIRE_CONST)
    tank_drive.turn_degrees(-50, -90)

def rescue_can():
    banzai_into_wall()
    resc_orientate()
    spiral_algo()
    finish()

def lmain():
    """
    Main function of the robo.
    """
    global check_for_black, last_turn

    while True:
        check_for_black = True # set up for handle_intersection()
        broken = False # there has got to be a better way to do this

        if ColorSensor.COLOR_NOCOLOR in [color_left.color, color_right.color]: # invalid readings, stop!
            tank_drive.stop()
        elif ColorSensor.COLOR_RED in [color_left.color, color_right.color]: # we fucking did it, we are at the rescue zone
            stop_beep_continue()
            set_claw_lift("down")
            tank_drive.on_for_rotations(50, 50, 300 * TIRE_CONST)
            set_claw_lift("up")
            rescue_can()

        elif ultrasound.distance_centimeters < 7 and OBSTACLE_AVOIDANCE: # we VERY close to a (suspected) wall
            tank_drive.on_for_rotations(-25, -25, 70 * TIRE_CONST)
            handle_obstacle()

        elif ColorSensor.COLOR_YELLOW in [color_left.color, color_right.color] and TRACK_VICTIM_DETECTION: # we found a victim
            stop_beep_continue()
            while ColorSensor.COLOR_YELLOW in [color_left.color, color_right.color]:
                tank_drive.on(50, 50)

        elif handle_intersection(): # handle_intersection() has found sth and reacted to it! start the loop again
            continue

        elif color_left.color == ColorSensor.COLOR_BLACK: # turn left
            last_turn = "left"
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
            last_turn = "right"
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
        else:
            tank_drive.on(50, 50)

    print("Program finished.")

def pickup_ball():
    set_claw_lift("up")
    set_claw("open")

    tank_drive.on_for_rotations(-25, -25, 50 * TIRE_CONST)
    tank_drive.turn_degrees(-50, 180)
    tank_drive.on_for_rotations(-25, -25, 40 * TIRE_CONST)

    set_claw_lift("down")
    set_claw("closed")
    set_claw_lift("up")

    tank_drive.turn_degrees(-50, -180)
    tank_drive.on_for_rotations(25, 25, 10 * TIRE_CONST)

def drop_ball():
    set_claw_lift("up")
    set_claw("closed")

    tank_drive.on_for_rotations(-25, -25, 50 * TIRE_CONST)
    tank_drive.turn_degrees(-50, 180)
    tank_drive.on_for_rotations(-25, -25, 40 * TIRE_CONST)

    set_claw_lift("down")
    set_claw("open")
    set_claw_lift("up")

    tank_drive.turn_degrees(-50, -180)
    tank_drive.on_for_rotations(25, 25, 10 * TIRE_CONST)

def find_zigzag():
    turn_dir = "right" # know which direction to turn in
    while not RESCUE_SIZE[0]-200 < ultrasound.distance_centimeters*10 < RESCUE_SIZE[0]+200:
        turn_dir = "right"
        if RESCUE_SIZE[1]-200 < ultrasound.distance_centimeters*10 < RESCUE_SIZE[1]+200:
            turn_dir = "left" # the measurement BEFORE the locating of RESCUE_SIZE[0] tells us on which side a wall is next to us
        tank_drive.turn_degrees(-90, 90)

    for i in range((RESCUE_SIZE[1]-100)/100):
        tank_drive.on_for_rotations(50, 50, (RESCUE_SIZE[1]-100), block=False)
        while tank_drive.left.is_running:
            if ultrasound.distance_centimeters < 40:
                return
        if turn_dir == "left":
            tank_drive.turn_degrees(-50, -90)
            tank_drive.on_for_rotations(25, 25, 100 * TIRE_CONST)
            tank_drive.turn_degrees(-50, -90)
            turn_dir = "right"
        else:
            tank_drive.turn_degrees(-50, 90)
            tank_drive.on_for_rotations(25, 25, 100 * TIRE_CONST)
            tank_drive.turn_degrees(-50, 90)
            turn_dir = "left"

def bmain():
    find_zigzag()

if __name__ == "__main__":
    init()
    calibrate_and_ready()
    rescue_can()
    #lmain()
