#!/usr/bin/env pybricks-micropython

from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, TouchSensor, ColorSensor,InfraredSensor, UltrasonicSensor, GyroSensor
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile

import lecture 
distance, angle= lecture.read_fichier("test.txt")

# Create your objects here.
ev3 = EV3Brick()

motorL= Motor(Port.B,Direction.COUNTERCLOCKWISE )
motorR= Motor(Port.D, Direction.COUNTERCLOCKWISE)

robot = DriveBase(motorR, motorL, wheel_diameter=56, axle_track=112)
robot.settings(straight_speed=100, turn_rate=90)

def distance(angle, distance):
    if(angle>180):
        motorR.run(angle)
        motorL.run(-angle)
    else:
        nvl = 180 - angle
        motorR.run(-nvl)
        motorL.run(nvl)
    robot.straight(distance)
        
def attraper():
    if (distance< 3):
        libre = True
        
#dans le main analyser pour trouver la balle la plus proche et mettre libre a faux 
    