#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, TouchSensor, ColorSensor,
                                 InfraredSensor, UltrasonicSensor, GyroSensor)
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile

import time

import socket
import os


# This program requires LEGO EV3 MicroPython v2.0 or higher.
# Click "Open user guide" on the EV3 extension tab for more information.


# Create your objects here.
ev3 = EV3Brick()


# Write your program() here.
ev3.speaker.beep()

MotorL = Motor(Port.A, positive_direction=Direction.COUNTERCLOCKWISE)
MotorR = Motor(Port.D, positive_direction=Direction.COUNTERCLOCKWISE)
WheelL = Motor(Port.B)
WheelR = Motor(Port.C)

drive_base = DriveBase(WheelL, WheelR, wheel_diameter=56, axle_track=106) #56, 106

def SetArmsOpen(state):
    if state == "wide_open":
        MotorL.track_target(180)
        MotorR.track_target(180)
    elif state == "open":
        MotorR.track_target(90)
        MotorL.track_target(90)
    elif state == "close":
        MotorL.track_target(0)
        MotorR.track_target(0)
    elif state == "wide_closed":
        MotorL.track_target(-40)
        MotorR.track_target(-40)

def test_states():
    states = ["open_parallel", "closed"]

    for i in range(0, len(states) * 500):
        print("State : ", states[i % len(states)])
        SetArmsOpen(states[i % len(states)])
        time.sleep(1)

def test_drive():
    while True:
        drive_base.straight(150)
        drive_base.turn(180)
        drive_base.straight(150)
        drive_base.turn(180)

# SetArmsOpen("open_parallel")
# test_drive()
#test_sensor()

target_host = "10.42.0.76" # Change this to the IP address of your server
target_port = 15666 # Change this to the port of your server


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.setblocking(True)

client.connect((target_host, target_port))

response = client.recv(len("ready".encode()))
if response.decode() == "ready":
    print("Server is ready.")
else:
    print("Error: server should send 'ready'.")
    exit(1)

def EXC_STRAIGHT(param:str):
    drive_base.straight(int(param))

### ADDED
def EXC_DRIVE_CONTINUOUS(param: str): # param = drive speed, turnrate
    p = param.split(",")
    drive_speed = int(p[0])
    turnrate = int(p[1])
    drive_base.drive(drive_speed, turnrate) #drive speed, turnrate

def EXC_SET_SPEED(param: str):
    p = param.split(",")
    left_speed = int(p[0])
    right_speed = int(p[1])
    drive_base.stop()
    WheelL.run(left_speed)
    WheelR.run(right_speed)
###

def EXC_TURN(param:str):
    drive_base.turn(int(param))

def EXC_ARM_STATE(param:str):
    SetArmsOpen(param)

def GET_IR_SENSOR():
    sendMessage(client, "RSP", "47")

def commandEXC(commandValue:str):
    cmdName = ""
    i = 0
    for c in commandValue:
        if c != ',':
            cmdName += str(c)
        i += 1
        if c == ',':
            break
    
    print("Command name is {}.".format(cmdName))

    cmdParam = ""
    for j in range(i, len(commandValue)):
        cmdParam += commandValue[j]

    print("Command parameter is {}.".format(cmdParam))
    
    if cmdName == "STRAIGHT":
        EXC_STRAIGHT(cmdParam)

    ## Added
    elif cmdName == "DRIVE_CONTINUOUS":
        EXC_DRIVE_CONTINUOUS(cmdParam)
    elif cmdName == "SET_SPEED":
        EXC_SET_SPEED(cmdParam)
    ##
    
    elif cmdName == "TURN":
        EXC_TURN(cmdParam)
    elif cmdName == "ARM_STATE":
        EXC_ARM_STATE(cmdParam)
    

def commandGET(commandValue:str):
    if commandValue == "IR_SENSOR":
        GET_IR_SENSOR()

def handleMessage(command:str, value:str):
    if command == "EXC":
        commandEXC(value)
    elif command == "GET":
        commandGET(value)

def receiveMessage(socket):
    print("Waiting for a message...")
    size_str = socket.recv(8)
    size = int(size_str)
    print("Message of size {} received.".format(size))
    command = socket.recv(3).decode()
    print("Command is {}.".format(command))
    value = socket.recv(size).decode()
    print("Command value is {}.".format(value))

    handleMessage(command, value)

def sendMessage(socket, command:str, value:str):
    packet = ""
    packet += str(len(value))
    packet += command
    packet += value

    print("Sending message {} to server.".format(packet))
    socket.send(packet.encode())



while True:
    receiveMessage(client)