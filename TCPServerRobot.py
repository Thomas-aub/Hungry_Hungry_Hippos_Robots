#!/usr/bin/env python3
import socket
import threading

HOST = "0.0.0.0"
PORT = 6543

def clientHandler(client_socket):
    # test si connection est prête
    client_socket.send("ready".encode())
    
    while True:
        response = client_socket.recv(1024)
        # si le serveur reçoit "stop" -> s'arrête
        if response.decode() == "stop":
            break
        # TODO: Faire les cas "up", "down", "left", "right"
        
    print("Fermeture du serveur")
    server.close()
    
    client_socket.close()
    print("Connection closed")


if __name__ == "__main__":
    # Ouverture de la connection
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print("[ROBOT B] Server is listening on %s:%d" % (HOST, PORT))
    
    client, addr = server.accept()
    print("Client connected " + str(addr))
    # Client gérer par un thread
    client_handler = threading.Thread(target = clientHandler, args=(client,))
    client_handler.start()
    