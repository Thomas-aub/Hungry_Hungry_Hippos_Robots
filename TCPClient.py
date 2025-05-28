import socket

# Infos sur le serveur (remplacer par l'IP Et le port du serveur)
target_host = "10.42.0.1"
target_port = 27700

# create a socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.settimeout(1) # attente en secondes avant de considérer que la connexion a échoué
# connect to the server
client.connect((target_host, target_port))

# receive
response = client.recv(4096) # maximum size of the response
if response.decode() == "ready":
    print("Successful")
else:
    print("Not successful")
# send
client.send("hello world".encode())

192