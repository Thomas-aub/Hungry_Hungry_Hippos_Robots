import os
import sys

absolute_path = os.path.dirname(__file__)

relative_path2 = "../modules"

sys.path.insert(0, os.path.join(absolute_path, relative_path2))

from geometry import Complex
from robotic import TwoWheels, ClientRobotInterface

import math
import sys
import pygame
import os

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
robotSim = TwoWheels(Complex.Cart(100,100),math.pi/2,50)

#serverRateau = ClientRobotInterface("192.168.82.179", 15666) 
serverRateau = ClientRobotInterface("10.42.0.80", 15666)
serverRateau.listen()

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
            
            # Drive Forever
            elif event.key == pygame.K_LEFT:
                robotSim.setSpeed(0,850)
                serverRateau.AntiClockwise(100)
                
            elif event.key == pygame.K_RIGHT:
                robotSim.setSpeed(850,0)
                serverRateau.Clockwise(100)
                
            elif event.key == pygame.K_UP:
                robotSim.setSpeed(500,500)
                serverRateau.Forward(500)
                
            elif event.key == pygame.K_DOWN:
                robotSim.setSpeed(-500,-500)
                serverRateau.Backward(500)
                
            elif event.key == pygame.K_c:
                serverRateau.Close()

            elif event.key == pygame.K_x:
                serverRateau.Open()
            
            elif event.key == pygame.K_w:
                robotSim.setSpeed(0, 0)
                serverRateau.setSpeed(0, 0)
            
            # Drive distance/angle
            elif event.key == pygame.K_z:
                serverRateau.StraightDist(1000)
            elif event.key == pygame.K_s:
                serverRateau.StraightDist(-1000)
            elif event.key == pygame.K_d:
                serverRateau.TurnDeg(360)
            elif event.key == pygame.K_q:
                serverRateau.TurnDeg(-90)         

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            target = fromScreenPoint(Complex.Cart(pos[0],pos[1]))
            robotSim.reach(target,deltaTime)
            trackMouse = True
            
        elif event.type == pygame.MOUSEBUTTONUP:
            pos = pygame.mouse.get_pos()
            target = fromScreenPoint(Complex.Cart(pos[0],pos[1]))
            robotSim.reach(target,deltaTime)
            trackMouse = False
        elif event.type == pygame.MOUSEMOTION and trackMouse:
            pos = pygame.mouse.get_pos()
            target = fromScreenPoint(Complex.Cart(pos[0],pos[1]))
            robotSim.reach(target,deltaTime)
    ###
    screen.fill((0,0,0))
    ####
    drawRobot(screen,robotSim,(0,255,0),(255,0,0),(0,0,255))
    ####
    robotSim.update(deltaTime)
    oldTime = newTime
    ####
    pygame.display.flip()