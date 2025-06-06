#!/usr/bin/env python3
import cv2
import socket
from flux import UdpFrameReceiver
import analysis
import time

HOST_ROBOT = "192.168.58.10"  # Adresse IP du robot
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
    response = clientA.recv(4096)

    try:
        while True:
            global end_server

            frame = rx.get_frame()
            if frame is not None:
                result = analysis.analyze_frame(frame)
                annotated = result.annotated

                if result.target_isis:
                    if(result.target_isis.distance_px and result.target_isis.direction_deg) :
                        distance_px = result.target_isis.distance_px
                        angle_deg = result.target_isis.direction_deg
                        if (distance_px and angle_deg) :
                            if angle_deg >= 345 or angle_deg <= 15:         
                                CLIENT.send("up".encode())
                            elif 15 < angle_deg <= 180:
                                CLIENT.send("right".encode())

                            elif 180 < angle_deg < 345:
                                CLIENT.send("left".encode())
                           

                else:
                    print("👀 Aucune cible détectée.")

                cv2.imshow("Robot lab", annotated)

            if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                print("👋 Bye !")
                break

    finally:
        rx.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()