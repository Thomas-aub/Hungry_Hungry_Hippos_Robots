from server import *
import cv2

#bind_ip = "10.42.0.80" # Replace this with your own IP address
bind_ip = "192.168.82.179"
bind_port = 15666 # Feel free to change this port
# create and bind a new socket

server = BrickServer(bind_ip, bind_port)
server.listen()

while True:
    instruction = input("Command to send to the brick: ")

    if instruction == "STOP":
        break

    params = input("parameters separated with commas: ")
    
    if params == "STOP":
        break

    server.execute(instruction, params)

H = [] # Homographies


def detecter_cercles(imageBrute):
    cv2.connectedComponentsWithStats(imageBrute, )

