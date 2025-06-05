from math import atan2, hypot
from geometry import Complex

class TwoWheels:
    def __init__(self,pos,angle,size):
        self._position = pos
        self._angle = angle
        self._size = size
        self._leftSpeed = 0.0
        self._rightSpeed = 0.0
        self._target = None
        self._isReaching = False
        self._isTurning = False
    def update(self,dt):
        front = Complex.FromPolar(1,self._angle)
        motionDir = dt * front
        leftPos = self._position + (self._size / 2.0) * front.perp()
        rightPos = self._position - (self._size / 2.0) * front.perp()
        newLeftPos = leftPos + (self._leftSpeed / 100.0) * motionDir
        newRightPos = rightPos + (self._rightSpeed / 100.0) * motionDir
        newPosition = 0.5 * (newLeftPos + newRightPos)
        newFront = (newRightPos - newLeftPos).normalize().perp()
        cth = front.dot(newFront)
        sth = front.cross(newFront)
        deltaAngle = atan2(sth,cth)
        self._position = newPosition
        self._angle = self._angle + deltaAngle

        if (self._isReaching):
            self.reach(self._target, dt)

    def setSpeed(self,left,right):
        self._leftSpeed = left
        self._rightSpeed = right
    def Forward(self,speed):
        self.setSpeed(speed,speed)
    def Backward(self,speed):
        self.setSpeed(-speed,-speed)
    def Clockwise(self,speed):
        self.setSpeed(speed,-speed)
    def AntiClockwise(self,speed):
        self.setSpeed(-speed,speed)
    def TurnLeft(self,speed):
        self.setSpeed(0,speed)
    def TurnRight(self,speed):
        self.setSpeed(speed,0)

    def face(self, target, dt):
        self._isTurning = True
        front = Complex.FromPolar(1,self._angle)
        relative = self._target - self._position
        cth = front.dot(relative) #adjacent
        sth = front.cross(relative) #oppose
        deltaAngle = atan2(sth,cth)
        angleToReach = self._angle + deltaAngle

        if (-deltaAngle) > 0:
            #self.Clockwise(300)
            self.setSpeed(300, -50)
        elif (-deltaAngle) < 0:
            #self.AntiClockwise(300)
            self.setSpeed(-50, 300)
        if abs(deltaAngle) < 0.001:
            self.setSpeed(0, 0)
            self._isTurning = False

    def reach(self,target,dt):
        self._isReaching = True
        self._target = target
        self.face(target, dt)

        if not(self._isTurning):
            self.Forward(500)
        if (self._position.dist(target) < 0.1):
            self.setSpeed(0, 0)
            self._isReaching = False
    