# move.py — logique de mouvement basée sur la détection

import os
from analysis import AnalysisResult
from typing import Optional
import subprocess

def generate(result: AnalysisResult, output_path: str = "commands.txt") -> Optional[str]:
    if not result or not result.aruco or not result.target:
        print("Aucune cible détectée.")
        return None

    angle = result.target.direction_deg
    distance = result.target.distance_px  

    movements = []


    # Tourner vers l'angle de la balle
    movements.append(f"TURN")
    
    # Avancer vers la balle
    movements.append(f"MOVE_FORWARD")

    # Enregistrer le fichier
    with open(output_path, "w") as f:
        for cmd in movements:
            f.write(cmd + "\n")

    print(f"Fichier de mouvements écrit : {output_path}")
    return output_path


def send(file_path: str, remote_user="ev3", remote_host="192.168.1.42", remote_path="~/commands.txt"):
    """
    Envoie le fichier via SCP à un robot distant.
    Assurez-vous que la clé SSH est configurée ou que le mot de passe est géré autrement.
    """
    if not file_path or not os.path.exists(file_path):
        print("Fichier à envoyer introuvable.")
        return

    cmd = [
        "scp",
        file_path,
        f"{remote_user}@{remote_host}:{remote_path}"
    ]

    try:
        subprocess.run(cmd, check=True)
        print("Fichier envoyé avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'envoi SCP : {e}")














#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, TouchSensor, ColorSensor,InfraredSensor, UltrasonicSensor, GyroSensor
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile


# Create your objects here.
ev3 = EV3Brick()

motorL= Motor(Port.B,Direction.COUNTERCLOCKWISE )
motorR= Motor(Port.D, Direction.COUNTERCLOCKWISE)

robot = DriveBase(motorR, motorL, wheel_diameter=56, axle_track=112)
robot.settings(straight_speed=100, turn_rate=90)


def traball(angle=0, distance=7):
    if (angle<0):
        motorR.run(angle)
        motorL.run(-angle)
    else:
        motorR.run(-angle)
        motorL.run(angle)
    robot.straight(distance)
    



    
    


