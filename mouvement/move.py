# #!/usr/bin/env pybricks-micropython
# from pybricks.hubs import EV3Brick
# from pybricks.ev3devices import (Motor, TouchSensor, ColorSensor,
#                                  InfraredSensor, UltrasonicSensor, GyroSensor)
# from pybricks.parameters import Port, Stop, Direction, Button, Color
# from pybricks.tools import wait, StopWatch, DataLog
# from pybricks.robotics import DriveBase
# from pybricks.media.ev3dev import SoundFile, ImageFile


# # This program requires LEGO EV3 MicroPython v2.0 or higher.
# Click "Open user guide" on the EV3 aextension tab for more information.


# # Create your objects here.
# ev3 = EV3Brick()

# motorL= Motor(Port.B,Direction.COUNTERCLOCKWISE )
# motorR= Motor(Port.D, Direction.COUNTERCLOCKWISE)

# robot = DriveBase(motorR, motorL, wheel_diameter=56, axle_track=112)
# robot.settings(straight_speed=100, turn_rate=90)


# def traball(angle=0, distance=7):
#     if (angle<0):
#         motorR.run(angle)
#         motorL.run(-angle)
#     else:
#         motorR.run(-angle)
#         motorL.run(angle)
#     robot.straight(distance)
    
# #calcul la distance entre la balle et nous odnc reconnaitre son QR code 
# def distance(MaPosition, BallPosition):
#     return MaPosition.x+BallPosition.x


    
    


