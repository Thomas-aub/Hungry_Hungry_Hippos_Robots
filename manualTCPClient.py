#!/usr/bin/env python3
import socket
from pynput import keyboard

HOST_ROBOT_A = "192.168.58.11" #robot avec la pelle
HOST_ROBOT_B = "192.168.58.11" #long robot
PORT = 6543
CLIENT = None

def on_press(key):
    global end_server
    if key == keyboard.Key.up:
        CLIENT.send("up".encode())
        print("UP PRESSED!")
        
    elif key == keyboard.Key.down:
        CLIENT.send("down".encode())
        print("DOWN PRESSED!")
        
    elif key == keyboard.Key.left:
        CLIENT.send("left".encode())
        print("LEFT PRESSED!")
        
    elif key == keyboard.Key.right:
        CLIENT.send("right".encode())
        print("RIGHT PRESSED!")
        
    elif hasattr(key, "char") and (key.char == 's' or key.char ==' S'):
        CLIENT.send("arret".encode())
        print("QUIT PRESSED! Arrêt du client")
        return False
        
    elif hasattr(key, "char") and (key.char == 'q' or key.char ==' Q'):
        CLIENT.send("stop".encode())
        print("QUIT PRESSED! Arrêt du client")
        return False

if __name__ == "__main__":
    ### clientA -> gère la connection avec le robot A
    ### Si serveur sur le robot A ouvert, décommenté le code suivant
    clientA = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientA.settimeout(1)
    clientA.connect((HOST_ROBOT_A, PORT))
    CLIENT = clientA
    print("Connection to ROBOT A server : %s:%d" % (HOST_ROBOT_A, PORT))
    response = clientA.recv(4096)
    
    ### clientB -> gère la connection avec le robot B
    ### Si serveur sur le robot B ouvert, décommenté le code suivant
    # clientB = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # clientB.settimeout(1)
    # clientB.connect((HOST_ROBOT_B, PORT))
    # CLIENT = clientB
    # print("Connection to ROBOT B server : %s:%d" % (HOST_ROBOT_B, PORT))
    # response = clientB.recv(4096)
    
    if response.decode() == "ready":
        print("Successful")
        
    with keyboard.Listener(on_press=on_press) as listener: listener.join()