#!/usr/bin/env python3

from main import *

def get_room_size_from_corner():
    MINDIST = 40
    values = []

    for _ in range(4):
        values.append(ultrasound.distance_centimeters)
        tank_drive.on_for_rotations(50, -50, 90 * ROTPOS_360)

    for i in range(4):
        if values[i] > MINDIST:
            xs = values[i]
            ys = values[(i+1)%len(values)]
            break
        tank_drive.on_for_rotations(50, -50, 90 * ROTPOS_360)

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
        

if __name__ == '__main__':
    xs, ys = get_room_size_from_corner()
    search_trig(xs, ys)
