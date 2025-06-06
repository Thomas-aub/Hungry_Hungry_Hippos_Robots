#!/usr/bin/env python3
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor
from pybricks.parameters import Port, Direction
from pybricks.robotics import DriveBase
from pybricks.tools import wait
import socket
import threading

HOST = "0.0.0.0"
PORT = 6543

ev3 = EV3Brick()

# Attention ici : on passe la direction en 2e argument, PAS "direction="
motorL = Motor(Port.B, Direction.COUNTERCLOCKWISE)
motorR = Motor(Port.D, Direction.COUNTERCLOCKWISE)

# Paramétrage du châssis (wheel_diameter en mm, axle_track en mm)
robot = DriveBase(motorR, motorL, wheel_diameter=56, axle_track=112)
robot.settings(straight_speed=150, turn_rate=100)  # vitesses par défaut

# Fonctions de déplacement
def move_forward(distance_mm=150):
    robot.straight(distance_mm)

def move_backward(distance_mm=150):
    robot.straight(-distance_mm)

def turn_left(angle_deg=90):
    robot.turn(-angle_deg)

def turn_right(angle_deg=90):
    robot.turn(angle_deg)

def clientHandler(client_socket):
    # test si connection est prête
    client_socket.send("ready".encode())
    
    while True:
        print("Dans la boucle")
        response = client_socket.recv(1024)
        # si le serveur reçoit "stop" -> s'arrête
        if response.decode() == "stop":
            print("STOOOP")
            break
        
        if response.decode() == "up":
            print("avance")
            move_forward(150)
    
        if response.decode() == "down":
            print("recule")
            move_backward(150)
            
        if response.decode() == "left":
            print("gauche")
            turn_right(90)
            
        if response.decode() == "right":
            print("droite")
            turn_left(90)
        
    print("Oupps il ferme")
    client_socket.close()
    server.close()


if __name__ == "__main__":
    # Ouverture de la connection
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print("[ROBOT A] Server is listening on %s:%d" % (HOST, PORT))
    
    client, addr = server.accept()
    print("Client connected " + str(addr))
    
    clientHandler(client)
    
    # Client gérer par un thread
    # client_handler = threading.Thread(target = clientHandler, args=(client,))
    # client_handler.start()
    