import sys
from .complex import Complex

class Particle:
    def __init__(self,p,v,m):
        self.position = p
        self.speed = v
        self.mass = m
        self.forces = Complex.Cart(0,0)
        self.oldPosition = Complex.Cart(0,0)
    def setPosition(self,p):
        self.position = p
    def setSpeed(self,v):
        self.speed = v
    def addForce(self,f):
        self.forces = self.forces + f
    def resetForces(self):
        self.forces = Complex.Cart(0,0)
    def update(self,dt):
        self.oldPosition = self.position
        acceleration = self.forces / self.mass
        self.speed = self.speed + acceleration * dt
        self.position = self.position + self.speed * dt
        self.forces = Complex.Cart(0,0)
    def collidePlane(self,p,n):
        p1 = self.oldPosition
        v1 = (self.position - self.oldPosition)
        v2 = n.perp()
        r = p1 - p
        t = r.cross(v2) / v1.cross(v2)
        if t >= 0 and t <= 1: return True, p1 + t * v1
        return False, None
    def collideSegment(self,p1,p2,invert=False):
        x1, y1 = p1.tuple()
        x2, y2 = p2.tuple()
        x3, y3 = self.oldPosition.tuple() if not invert else self.position.tuple()
        x4, y4 = self.position.tuple() if not invert else self.oldPosition.tuple()
        det1 = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
        det2 = (x4 - x3) * (y2 - y3) - (y4 - y3) * (x2 - x3)
        det3 = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
        det4 = (x2 - x1) * (y4 - y1) - (y2 - y1) * (x4 - x1)
        if det1 * det2 < 0 and det3 * det4 < 0:
            # Calcul du point d'intersection
            x = x1 + (x2 - x1) * abs(det1) / (abs(det1) + abs(det2))
            y = y1 + (y2 - y1) * abs(det1) / (abs(det1) + abs(det2))
            return True, Complex.Cart(x,y)
        return False, None
    def bouncePlane(self,p,n,friction=1.0):
        ret, inter = self.collidePlane(p,n)
        if ret:
            self.position = self.position.mirror(p,n)
            self.speed = friction * self.speed.reflect(p,n)
    def bounceSegment(self,p0,p1,invert=False,friction = 1.0):
        ret, inter = self.collideSegment(p0,p1,invert)
        if ret:
            p = p0
            n = (p1-p0).normalize().perp()
            self.position = self.position.mirror(p,n)
            self.speed = friction * self.speed.reflect(p,n)

    