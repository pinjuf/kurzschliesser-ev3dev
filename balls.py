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
from grab_ball import *

REFLECTION_LIMIT = 50       #Limit of dead and alive balls
ULATRASOUND_DISTANCE = 2    #Distance to wall/ball in cm to see ball using light sensor

direction = 1               #used to turn in right direction after line finished
victim_count = 0       #there are two alive victims to get

def check_for_ball():
    return color_ball.reflected_light_intensity > REFLECTION_LIMIT

def grab_ball():
    #turn 178 degrees
    tank_drive.on_for_seconds(48, -50, 180/(DPS * 50))

    set_claw("open")       #open claws
    set_claw_lift("down")
    set_claw("closed")      #close claws
    set_claw_lift("up")
    return

def release_ball():
    #turn 180 degrees
    tank_drive.on_for_seconds(50, -50, 180/(DPS * 50))

    set_claw_lift("down")       #open claws
    set_claw("open")
    tank_drive.on_for_rotations(50, 50, 5 * TIRE_CONST)   #drive away
    set_claw("closed")          #close claws
    set_claw_lift("up")
    return

def search_release_area():
    color_ball.mode = ColorSensor.MODE_COL_COLOR            #change to color mode
    tank_drive.on(50, 50)
    while True:
        if ultrasound.distance_centimeters < ULATRASOUND_DISTANCE or is_on_border_line:
            tank_drive.on_for_seconds(50, -50, 90/(DPS * 50))                   #turn 90 degres
            tank_drive.on(50, 50)
        if color_ball.color == ColorSensor.COLOR_BLACK:
            color_ball.mode = ColorSensor.MODE_COL_REFLECT
            return

def handle_dead_victim():    #check if object is wall or dead victim
    tank_drive.on_for_seconds(50, -50, 90 /(DPS * 50))              #turn 90 degres
    tank_drive.on_for_rotations(50, 50, 10 * TIRE_CONST)            #drive away from dead ball (if it is)
    tank_drive.on_for_seconds(50, -50, -90 /(DPS * 50))             #turn 90 degres
    if ultrasound.distance_centimeters < ULATRASOUND_DISTANCE:      #check if wall
        tank_drive.on_for_seconds(50, -50, -90 /(DPS * 50))
        tank_drive.on_for_rotations(50, 50, 10 * TIRE_CONST)        #drive back
        tank_drive.on_for_seconds(50, -50, 90 /(DPS * 50))
        next_line()
    else:
        tank_drive.on_for_rotations(50, 50, 10 * TIRE_CONST)        #drive around
        tank_drive.on_for_seconds(50, -50, -90 /(DPS * 50))
        tank_drive.on_for_rotations(50, 50, 10 * TIRE_CONST)
        tank_drive.on_for_seconds(50, -50, 90 /(DPS * 50))

def is_on_border_line(check_black):
    #TODO: check if silver counts as gray, if not change mode to reflect to check it
    return ((color_right.color == ColorSensor.COLOR_BLACK or color_left.color == ColorSensor.COLOR_BLACK) if check_black else False) or color_right.color == ColorSensor.COLOR_GRAY or color_left.color == ColorSensor.COLOR_GRAY or color_right.color == ColorSensor.COLOR_GREEN or color_left.color == ColorSensor.COLOR_GREEN

def next_line():
    tank_drive.on_for_rotations(-50, -50, 5 * TIRE_CONST)                              #drive back
    tank_drive.on_for_seconds(50, -50, (90 if direction==0 else -90) /(DPS * 50))      #turn 90 degres
    tank_drive.on_for_rotations(50, 50, 5 * TIRE_CONST)                                #drive forward to next line
    tank_drive.on_for_seconds(50, -50, (90 if direction==0 else -90)/(DPS * 50))       #turn 90 degres
    tank_drive.on(50, 50)                                                               #start main movement
    direction = 1-direction

def search():
    color_ball.mode = ColorSensor.MODE_COL_REFLECT
    tank_drive.on(50, 50)
    while victim_count < 2:
        if is_on_border_line(True): #Drive back -> next line
            next_line()
        if ultrasound.distance_centimeters < ULATRASOUND_DISTANCE:  # check for ball/wall
            if check_for_ball():
                grab_ball()
                search_release_area()
                release_ball()
                victim_count += 1
                tank_drive.on_for_rotations(50, 50, 10 * TIRE_CONST)    #drive forward to next away from black line
                next_line()
            else:
                handle_dead_victim()
