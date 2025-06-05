from math import atan2, hypot
from geometry import Complex
import os
import sys

absolute_path = os.path.dirname(__file__)

relative_path1 = "../../computer"
sys.path.insert(0, os.path.join(absolute_path, relative_path1))
from server import *

## todo: Conversion distance point pixel -> distance point mm
 
class ClientRobotInterface:

	def __init__(self, bind_ip, bind_port):
		self._bind_ip = bind_ip
		self._bind_port = bind_port
		self._leftSpeed = 0.0
		self._rightSpeed = 0.0
		self._server = BrickServer(bind_ip, bind_port)
		self._position = Complex.Cart(0, 0)
		self._target = None
		self._isReaching = False
		self._isTurning = False
		self._isClosed = False

	def listen(self):
		self._server.listen()

	def setSpeed(self, left, right):
		self._leftSpeed, self._rightSpeed = left, right
		self._server.execute("SET_SPEED", f"{left},{right}")

	# Drive Forever
	def Forward(self, speed):
		self._leftSpeed, self._rightSpeed = speed, speed
		self._server.execute("DRIVE_CONTINUOUS", f"{speed},0")

	def Backward(self, speed):
		self._leftSpeed, self._rightSpeed = -speed, -speed
		self._server.execute("DRIVE_CONTINUOUS", f"{-speed},0")

	def Clockwise(self, turnrate): #turnrate = deg/s
		self._server.execute("DRIVE_CONTINUOUS", f"0,{turnrate}")
		
	def AntiClockwise(self, turnrate):
		self._server.execute("DRIVE_CONTINUOUS", f"0,{-turnrate}")
	
	# Drive by Distance/angle
	def StraightDist(self, distance): #distance in mm
		self._server.execute("STRAIGHT", distance)

	def TurnDeg(self, degree):
		self._server.execute("TURN", degree)

	def Close(self):
		self._server.execute("ARM_STATE", "close")
		self._isClosed = True
	
	def Open(self):
		self._server.execute("ARM_STATE", "open")
		self._isClosed = False
	
	def Reach(self, target: Complex):
		pass

	def Face(self, target: Complex):
		pass
