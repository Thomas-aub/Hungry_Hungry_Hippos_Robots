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
mdiff = MoveDifferential(OUTPUT_B, OUTPUT_D, EV3Tire, 80)

def clientHandler(client_socket):
    # test si connection est prête
    client_socket.send("ready".encode())
    
    while True:
        print(1)
        response = client_socket.recv(1024)

        # si le serveur reçoit "stop" -> s'arrête
        if response.decode() == "stop":
            print("STOOOP")
            break
        
        if response.decode() == "up":
            print("avance")
            tank.on(-STRAIGHT_SPEED,-STRAIGHT_SPEED)
    
        if response.decode() == "down":
            print("recule")
            # tank.on(STRAIGHT_SPEED,STRAIGHT_SPEED)
            tank.stop()
            
        if response.decode() == "left":
            print("gauche")
            mdiff.turn_right(SpeedRPM(40), 90)
            # mdiff.turn_degrees(SpeedRPM(40), 90) # a essayer pour tourner de 90 degrées
            
        if response.decode() == "right":
            print("droite")
            mdiff.turn_left(SpeedRPM(40), 90)
            # mdiff.turn_degrees(SpeedRPM(40), -90) # a essayer pour tourner de -90 degrées
        
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
    