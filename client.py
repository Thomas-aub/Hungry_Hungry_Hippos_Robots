from ev3net import TCPClientAbstraction, Buffer
import struct
import time

# Adresse IP du PC (passerelle du robot)
HOST = "10.42.0.1"  # à adapter
PORT = 9999

client = TCPClientAbstraction(bufferSize=1024)
client.initialize(HOST, PORT)

# Fonction appelée quand un message arrive
def on_instruction(buffer: Buffer):
    direction_deg, distance_cm = struct.unpack("!ff", buffer.buffer)
    print(f"[Robot] Direction: {direction_deg:.1f}°, Distance: {distance_cm:.1f}cm")
    # ➜ Tu peux ici appeler une fonction de déplacement moteur

client.passiveReceive(on_instruction)

print("Client EV3 prêt, connecté au serveur.")

try:
    while True:
        # ping pour garder la connexion active
        client.send(Buffer(b"EV3_READY"))
        time.sleep(2)
except KeyboardInterrupt:
    print("Déconnexion.")
    client.stop()
