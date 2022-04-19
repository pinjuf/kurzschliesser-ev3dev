#!/usr/bin/env python3

from main import *

def get_room_size_from_corner():
    MINDIST = 40
    values = []

    for _ in range(4):
        values.append(ultrasound.distance_centimeters)
        tank_drive.turn_degrees(-50, 90)

    for i in range(4):
        if values[i] > MINDIST:
            xs = values[i]
            ys = values[(i+1)%len(values)]
            break
        tank_drive.turn_degrees(-50, 90)

    return xs, ys

def search_trig(xs, ys):
    critical_angle = atan(ys/xs)
    offset = tank_drive.left_motor.position
    tank_drive.on(25, -25)
    
    angle = 0
    while angle < 90:
        angle = 360*(tank_drive.left_motor.position-offset)/R_ROTPOS_360
        if angle < critical_angle:
            expected = xs/cos(radians(angle))
        else:
            expected = ys/cos(radians(90-angle))
            
        actual = ultrasound.distance_centimeters
        if actual < (expected - 10):
            tank_drive.off()
            break

def pickup_ball():
    set_claw_lift("up")
    set_claw("open")

    tank_drive.on_for_rotations(-25, -25, 50 * TIRE_CONST)
    tank_drive.turn_degrees(-50, 180)
    tank_drive.on_for_rotations(-25, -25, 20 * TIRE_CONST)

    set_claw_lift("down")
    set_claw("closed")

    tank_drive.turn_degrees(-50, -180)
    tank_drive.on_for_rotations(25, 25, 30 * TIRE_CONST)

def bmain():
    pickup_ball()

if __name__ == '__main__':
    init()
    print(claw_lift.position)
    calibrate_and_ready()
    bmain()
