
from math import pi
from .complex import Complex


class Polygon:
    def __init__(self):
        self.points = []
        self.inverted = False
    def tuple(self):
        return list(map(lambda x: x.tuple(),self.points))
    def bounce(self,p):
        for i in range(len(self.points)):
            p.bounceSegment(self.points[i],self.points[(i+1)%len(self.points)],invert=self.inverted)
    def rotate(self,center,angle):
        for i in range(len(self.points)):
            self.points[i] = self.points[i].rotate(center,angle)
        return self
    def translate(self,displacement):
        for i in range(len(self.points)):
            self.points[i] = self.points[i].translate(displacement)
        return self
    def debug(self):
        print("[",end="")
        for i in range(len(self.points)):
            print(self.points[i],end="")
        print("]")
    @staticmethod
    def Box(center,size,inside = False):
        result = Polygon()
        result.points.append(Complex.Cart(center.x-size.x/2,center.y-size.y/2))
        result.points.append(Complex.Cart(center.x+size.x/2,center.y-size.y/2))
        result.points.append(Complex.Cart(center.x+size.x/2,center.y+size.y/2))
        result.points.append(Complex.Cart(center.x-size.x/2,center.y+size.y/2))
        result.inverted = inside
        return result
    @staticmethod
    def Ngone(center,radius,theta,numSides,inside = False):
        result = Polygon()
        for i in range(numSides):
            result.points.append(
                Complex.FromPolar(radius,theta + i * 2 * pi / numSides) + center
            )
        result.inverted = inside
        return result
