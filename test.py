#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor
from pybricks.parameters import Port, Direction
from pybricks.robotics import DriveBase
from pybricks.tools import wait

import socket

# --- Initialisation EV3 / Pybricks ---
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


# --- Configuration du serveur TCP ---
HOST = "0.0.0.0"  # Écoute sur toutes les interfaces
PORT = 6543

# Création du socket et mise en écoute
server = socket.socket()
server.bind((HOST, PORT))
server.listen(1)
ev3.screen.clear()
ev3.screen.print("[ROBOT B] Listening on {}:{}".format(HOST, PORT))

while True:
    client, addr = server.accept()
    ev3.screen.clear()
    ev3.screen.print("Client:", addr)

    # On envoie “ready” dès que la connexion est OK
    try:
        client.send(b"ready")
    except Exception as e:
        ev3.screen.clear()
        ev3.screen.print("Error sending ready:", e)
        client.close()
        continue

    # Boucle de réception et d'exécution des commandes
    while True:
        try:
            data = client.recv(1024)
        except Exception as e:
            ev3.screen.clear()
            ev3.screen.print("Recv error:", e)
            break

        if not data:
            ev3.screen.clear()
            ev3.screen.print("Client disconnected")
            break

        command = data.decode().strip()

        if command == "stop":
            ev3.screen.clear()
            ev3.screen.print("Stop demandé")
            break

        elif command == "up":
            ev3.screen.clear()
            ev3.screen.print("Avance")
            move_forward(150)

        elif command == "down":
            ev3.screen.clear()
            ev3.screen.print("Recule")
            move_backward(150)

        elif command == "left":
            ev3.screen.clear()
            ev3.screen.print("Tourne ←")
            turn_left(90)

        elif command == "right":
            ev3.screen.clear()
            ev3.screen.print("Tourne →")
            turn_right(90)

        else:
            ev3.screen.clear()
            ev3.screen.print("Commande inconnue:")
            ev3.screen.print(command)

        wait(100)

    # Fin de la connexion client
    client.close()
    ev3.screen.clear()
    ev3.screen.print("Conn. fermée")
    wait(500)

# (on ne tombe jamais ici sauf si tu arrêtes manuellement)
server.close()
ev3.screen.clear()
ev3.screen.print("Serveur arrêté")