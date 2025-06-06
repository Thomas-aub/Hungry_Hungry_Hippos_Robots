#!/usr/bin/env python3
from ev3dev2.motor import LargeMotor
from ev3dev2.motor import OUTPUT_B, OUTPUT_D, MoveTank, MoveDifferential, SpeedRPM
from ev3dev2.wheel import EV3Tire
import socket

HOST = "0.0.0.0"
PORT = 6543
STRAIGHT_SPEED = 80 # pourcentage de la vitesse

motorL = LargeMotor(OUTPUT_B)
motorR = LargeMotor(OUTPUT_D)
tank = MoveTank(OUTPUT_B, OUTPUT_D)
mdiff = MoveDifferential(OUTPUT_B, OUTPUT_D, EV3Tire, 50)

def clientHandler(client_socket):
    # test si connection est prête
    client_socket.send("ready".encode())
    
    while True:
        response = client_socket.recv(1024)
        command = response.decode()
        print(command)

        mode, degree_str, distance_str = command.split(";")
        degree = int(degree_str)
        distance = float(distance_str)
        if mode == "manual" :

            if degree== "stop":
                print("STOOOP")
                break
            
            if degree == "up":
                print("avance")
                tank.on(-STRAIGHT_SPEED,-STRAIGHT_SPEED)
        
            if degree == "down":
                print("recule")
                # tank.on(STRAIGHT_SPEED,STRAIGHT_SPEED)
                tank.stop()
                
            if degree== "left":
                print("gauche")
                tank.on(STRAIGHT_SPEED//2,-STRAIGHT_SPEED)
                # mdiff.turn_degrees(SpeedRPM(40), 90) # a essayer pour tourner de 90 degrées
                
            if degree== "right":
                print("droite")
                mdiff.turn_left(SpeedRPM(40), 180)
                # mdiff.turn_degrees(SpeedRPM(40), -90) # a essayer pour tourner de -90 degrées
        

        elif mode == "auto" :

            if degree >= 345 or degree <= 15:
                # Condition 1: near 0°
                print("avance")
                tank.on(-STRAIGHT_SPEED, -STRAIGHT_SPEED)

            elif 15 < degree <= 180:
                # Condition 2: right half
                print("droite")
                mdiff.turn_left(SpeedRPM(40), degree)

            elif 180 < degree < 345:
                # Condition 3: left half
                print("gauche")
                mdiff.turn_right(SpeedRPM(40), (360-degree))


    # print("Oupps il ferme")
    # client_socket.close()
    # server.close()


if __name__ == "__main__":
    # Ouverture de la connection
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print("[ROBOT A] Server is listening on %s:%d" % (HOST, PORT))
    
    client, addr = server.accept()
    print("Client connected " + str(addr))
    
    clientHandler(client)
    