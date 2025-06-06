import socket
import threading
from pynput import keyboard
import move 

end_server = False
bind_ip = "0.0.0.0" # Replace this with your own IP address
bind_port = 6534 # Feel free to change this port
# create and bind a new socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((bind_ip, bind_port))
server.settimeout(1.0)
server.listen(5)
print("Server is listening on %s:%d" % (bind_ip, bind_port))

def on_press(key):
    global end_server
    if key == keyboard.Key.up:
        move.distance(0, 10000)
    elif key == keyboard.Key.down:
        move.distance(0, -10000)
    elif key == keyboard.Key.left:
        move.distance(90, 10000)
    elif key == keyboard.Key.right:
        move.distance(-90, 10000)

    elif hasattr(key, "char") and key.char == 'q':
        print("QUIT PRESSED! Arrêt en cours")
        end_server = True
        return False

def clientHandler(client_socket):
    # send a message to the client
    client_socket.send("ready".encode())
    # receive and display a message from the client
    request = client_socket.recv(1024)
    print("Received \"" + request.decode() + "\" from client")
    # close the connection again
    client_socket.close()
    print("Connection closed")
    
listener = keyboard.Listener(on_press=on_press)
listener.start()

while not end_server:
    
    # wait for client to connect
    try:
        client, addr = server.accept()
    except socket.timeout:
        continue
    except OSError:
        break
    
    print("Client connected " + str(addr))
    # create and start a thread to handle the client
    client_handler = threading.Thread(target = clientHandler, args=(client,))
    client_handler.start()

print("Arrêt du serveur…")
try:
    server.close()
except:
    pass
# si le listener n'est pas déjà arrêté, on le stoppe
listener.stop()
listener.join()
print("Serveur fermé.")
    