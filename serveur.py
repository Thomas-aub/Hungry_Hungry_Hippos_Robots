from ev3net import TCPServerAbstraction, Buffer
import struct

# Création du serveur
server = TCPServerAbstraction(bufferSize=1024)
server.initialize("", 9999)
server.listenToClients()

print("Serveur prêt, en attente de robots...")

# Exemple : envoyer une instruction à tous les robots
# def broadcast_instruction(direction_deg, distance_cm):
#     msg = struct.pack("!ff", direction_deg, distance_cm)
#     server.broadcast(Buffer(msg))

msg = struct.pack("!ff", "hello world")
server.broadcast(Buffer)

# Boucle d’exemple
import time
try:
    while True:
        # exemple d’envoi toutes les 5s
        broadcast_instruction(45.0, 100.0)
        print("Instruction envoyée à tous les robots.")
        time.sleep(5)
except KeyboardInterrupt:
    print("Arrêt serveur.")
    server.stop()


#while ma distance a la ball est < ... j'avance