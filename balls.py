#!/usr/bin/env python3

from main import *

def get_room_size_from_corner():
    MINDIST = 20
    values = []

    for _ in range(4):
        values.append(ultrasound.distance_centimeters)
        tank_drive.on_for_rotations(50, -50, 90 * ROTPOS_360)

    for i in range(4):
        if values[i] < MINDIST:
            xs = values[i]
            ys = values[(i+1)%len(values)]
            break
        tank_drive.on_for_rotations(50, -50, 90 * ROTPOS_360)

    return xs, ys
    

if __name__ == '__main__':
    xs, ys = get_room_size_from_corner()
