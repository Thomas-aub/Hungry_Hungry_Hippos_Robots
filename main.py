"""
main.py — point d’entrée
Récupère l’image → l’analyse → (optionnel) l’affiche ou l’envoie au robot
"""
import cv2, threading
from flux import UdpFrameReceiver
import analysis
# import move


def main():
    rx = UdpFrameReceiver(port=8080)
    rx.start()
    print("Listening on UDP port 8080 — press Q to quit")

    try:
        while True:
            frame = rx.get_frame()
            if frame is not None:
                result = analysis.analyze_frame(frame)
                annotated = result.annotated
                """"
                file = move.generate(result)
                if file:
                    move.send(file)
                """
                cv2.imshow("Robot lab", annotated)
            if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                break

    finally:
        rx.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
