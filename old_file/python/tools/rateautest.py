import os
import sys

absolute_path = os.path.dirname(__file__)

relative_path1 = "../computer"
relative_path2 = "../modules"

sys.path.insert(0, os.path.join(absolute_path, relative_path1))
sys.path.insert(0, os.path.join(absolute_path, relative_path2))

from server import *
from geometry import Complex
from robotic import TwoWheels


import math
import sys
import pygame
import os

#bind_ip = "10.42.0.80" # Replace this with your own IP address
bind_ip = "192.168.82.179"
bind_port = 15666 # Feel free to change this port
# create and bind a new socket

server = BrickServer(bind_ip, bind_port)
server.listen()

def toScreenPoint(c):
    return Complex.Cart(c.x + width / 2.0, -c.y + height / 2.0)

def toScreenVector(c):
    return Complex.Cart(c.x, -c.y)

def fromScreenPoint(c):
    return Complex.Cart(c.x - width / 2.0, -c.y + height / 2.0)

def drawRobot(screen,robot,bodyColor,frontColor,wheelColor):
    front = toScreenVector(Complex.FromPolar(1,robot._angle).normalize())
    toLeft = -1.0 * front.perp()
    pos = toScreenPoint(Complex.Cart(robot._position.x,robot._position.y))
    tool = pos + (robot._size / 2.0) * front
    left = pos + (robot._size / 2.0) * toLeft
    right = pos - (robot._size / 2.0) * toLeft
    pygame.draw.circle(screen,bodyColor,pos.tuple(),robot._size/2.0)
    pygame.draw.line(screen,frontColor,pos.tuple(),tool.tuple(),1)
    pygame.draw.circle(screen,wheelColor,left.tuple(),3.0)
    pygame.draw.circle(screen,wheelColor,right.tuple(),3.0)
    if robot._target is not None:
        pygame.draw.circle(screen,(255,0,0),toScreenPoint(robot._target).tuple(),3)

width, height = 1024, 1024
robot = TwoWheels(Complex.Cart(100,100),math.pi/2,50)
timeMultiplicator = 10.0
pygame.init()
screen = pygame.display.set_mode((width,height))
oldTime = pygame.time.get_ticks()
trackMouse = False
drive_speed = 100
turnrate = 100

while True:
    newTime = pygame.time.get_ticks()
    deltaTime = (newTime - oldTime) / 1000.0
    if deltaTime < 0.001: deltaTime = 0.001
    deltaTime = timeMultiplicator * deltaTime
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sys.exit()
                
            elif event.key == pygame.K_LEFT:
                robot.setSpeed(0,100)
                server.execute("TURN", -100)
                
            elif event.key == pygame.K_RIGHT:
                robot.setSpeed(100,0)
                server.execute("TURN", 100)
                
            elif event.key == pygame.K_UP:
                robot.setSpeed(100,100)
                server.execute("STRAIGHT", 1000)
                
            elif event.key == pygame.K_DOWN:
                robot.setSpeed(-100,-100)
                server.execute("STRAIGHT", -100)
                
            elif event.key == pygame.K_c:
                server.execute("ARM_STATE", "close")

            elif event.key == pygame.K_o:
                server.execute("ARM_STATE", "open")
            
            # DRIVE FOREVER
            elif event.key == pygame.K_DELETE:
                robot.setSpeed(0,0)
                server.execute("DRIVE_CONTINUOUS", "0,0")
            elif event.key == pygame.K_z:
                server.execute("DRIVE_CONTINUOUS", f"{drive_speed},0")
            elif event.key == pygame.K_s:
                server.execute("DRIVE_CONTINUOUS", f"{-drive_speed},0")
            elif event.key == pygame.K_d:
                server.execute("DRIVE_CONTINUOUS", f"0,{turnrate}")
            elif event.key == pygame.K_q:
                server.execute("DRIVE_CONTINUOUS", f"0,{-turnrate}")                

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            target = fromScreenPoint(Complex.Cart(pos[0],pos[1]))
            robot.reach(target,deltaTime)
            trackMouse = True
            
        elif event.type == pygame.MOUSEBUTTONUP:
            pos = pygame.mouse.get_pos()
            target = fromScreenPoint(Complex.Cart(pos[0],pos[1]))
            robot.reach(target,deltaTime)
            trackMouse = False
        elif event.type == pygame.MOUSEMOTION and trackMouse:
            pos = pygame.mouse.get_pos()
            target = fromScreenPoint(Complex.Cart(pos[0],pos[1]))
            robot.reach(target,deltaTime)
    ###
    screen.fill((0,0,0))
    ####
    drawRobot(screen,robot,(0,255,0),(255,0,0),(0,0,255))
    ####
    robot.update(deltaTime)
    oldTime = newTime
    ####
    pygame.display.flip()