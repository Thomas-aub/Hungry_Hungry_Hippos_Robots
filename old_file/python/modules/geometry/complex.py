
from math import cos, sin, sqrt

class Complex:
    def __init__(self,x,y):
        self.x = x
        self.y = y
    def __add__(self, c):
        return Complex.Cart(self.x+c.x,self.y+c.y)
    def __sub__(self,c):
        return Complex.Cart(self.x-c.x,self.y-c.y)
    def __neg__(self,c):
        return Complex.Cart(-self.x,-self.y)
    def __mul__(self,c):
        if isinstance(c,Complex):
            return Complex.Cart(
                self.x * c.x - self.y * c.y,
                self.x * c.y + self.y * c.x
            )
        else:
            return Complex.Cart(self.x*c,self.y*c)
    def __rmul__(self,c):
        if isinstance(c,Complex):
            return Complex.Cart(
                c.x * self.x - c.y * self.y,
                c.x * self.y + c.y * self.x
            )
        else:
            return Complex.Cart(c*self.x,c*self.y)
    def __truediv__(self,c):
        return Complex.Cart(self.x/c,self.y/c)
    def perp(self):
        return Complex.Cart(-self.y,self.x)
    def norm(self):
        return sqrt(self.dot(self))
    def normalize(self):
        return self / self.norm()
    def dot(self,c):
        return self.x * c.x + self.y * c.y
    def cross(self,c):
        return self.x * c.y - self.y * c.x
    def dist(self, c):
        return sqrt((self.x - c.x)**2 + (self.y - c.y)**2)
    def tuple(self):
        return (self.x,self.y)
    def mirror(self,p,n):
        pq = self - p
        proj = (pq.dot(n) / n.dot(n)) * n
        return self - 2 * proj
    def reflect(self,p,n):
        proj = (self.dot(n) / n.dot(n)) * n
        perp = self - proj
        return self - 2 * proj
    def rotate(self,center,angle):
        r = Complex.FromPolar(1,angle)
        return (self - center) * r + center
    def translate(self,displacement):
        return self + displacement
    def __str__(self):
        return "({:8.3f},{:8.3f})".format(self.x,self.y)
    @staticmethod
    def Cart(x,y):
        return Complex(x,y)
    @staticmethod
    def FromPolar(rho,theta):
        return Complex(rho*cos(theta),rho*sin(theta))
