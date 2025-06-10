#!/usr/bin/env python3
import cv2
import socket
from flux import UdpFrameReceiver
import analysis
import time

HOST_ROBOT = "192.168.58.11"  # Adresse IP du robot
PORT = 6543

def main():
    rx = UdpFrameReceiver(port=8080)
    rx.start()
    print("📡 Listening on UDP port 8080 — press Q to quit")

    clientA = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientA.settimeout(1)
    clientA.connect((HOST_ROBOT, PORT))

    CLIENT = clientA
    print("Connection to ROBOT A server : %s:%d" % (HOST_ROBOT, PORT))

    last_send_time = 0

    try:
        while True:
            frame = rx.get_frame()
            if frame is not None:
                result = analysis.analyze_frame(frame)
                annotated = result.annotated
                current_time = time.time()
                if result.target_isis:
                    if result.target_isis.distance_px and result.target_isis.direction_deg:
                        distance_px = result.target_isis.distance_px
                        angle_deg = result.target_isis.direction_deg
                        if distance_px and angle_deg:
                            res = f"Distance: {distance_px}, Angle: {angle_deg}, Commande: "

                            if current_time - last_send_time >= 0.3:
                                if(distance_px < 20) :
                                    res += "DOWN\n"
                                    CLIENT.send("down".encode())
                                    print(res)
                                elif angle_deg >= 350 or angle_deg <= 10:
                                    res += "UP\n"
                                    CLIENT.send("up".encode())
                                    print(res)

                                elif 10 < angle_deg <= 180:
                                    CLIENT.send("left".encode())
                                    res += "LEFT\n"
                                    print(res)
                                elif 180 < angle_deg < 350:
                                    CLIENT.send("right".encode())
                                    res += "RIGHT\n"
                                    print(res)

                                last_send_time = current_time
                elif(current_time - last_send_time >= 5 and last_send_time > 0) :
                    if( (current_time - last_send_time)%2 == 1) :
                        print("Je suis perdu, je tourne à droite")
                        CLIENT.send("right".encode())
                    else :
                        print("Je suis perdu, j'avance")
                        CLIENT.send("up".encode())
                elif(current_time - last_send_time >= 4):
                    print("Je suis perdu, je tourne à droite")
                    CLIENT.send("right".encode())
                elif(current_time - last_send_time >= 4.5):
                    print("Je suis perdu, j'avance")
                    CLIENT.send("up".encode())


                cv2.imshow("Robot lab", annotated)

            if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                print("👋 Bye !")
                break

    finally:
        rx.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
