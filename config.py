#!/usr/bin/env python3

DPS = 1.9 # degrees per second on 1% power
TIRE_RAD = 17.5 # mm
TIME_CONST = 1 # TODO TEMPORARY! USED FOR TIMED ROTATION! TO BE REPLACED WITH POSITIONAL INPUT INSTEAD OF TIME

TIRE_CONST = 1 / (2 * 3.14159 * TIRE_RAD)

CLAW_RANGE   = 1750
CLAW_LIFT_RANGE = 95

MARKER_FOUND_L = 0b10
MARKER_FOUND_R = 0b01
MARKER_FOUND_B = 0b11

COLORS = {
        'white':(255,255,255),
        'black':(0, 0, 0),
        'green':(0, 255, 0),
        'red':(255, 0, 0),
}

RESCUE_SIZE = (1200, 900)

RESCUE_KIT = False
OBSTACLE_AVOIDANCE = False
