import cv2
import numpy as np
import matplotlib.pyplot as plt

# Ajustement des seuils HSV
lower_orange = np.array([5, 100, 100])  
upper_orange = np.array([25, 255, 255])  

lower_blue = np.array([80, 100, 50])  
upper_blue = np.array([120, 255, 255])  

def detect_spheres_from_stream(stream_url):
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        print("Erreur: Impossible de se connecter à la caméra.")
        return

    plt.ion()
    fig, ax = plt.subplots()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Erreur: Impossible de lire l'image.")
                break

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Normalisation de la luminosité
            hsv[:,:,2] = cv2.equalizeHist(hsv[:,:,2])

            # Détection du bleu
            mask = cv2.inRange(hsv, lower_blue, upper_blue)

            # Morphologie pour séparer les objets collés
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            # Appliquer un flou pour lisser les bords
            blurred = cv2.GaussianBlur(mask, (9, 9), 2)

            # Détection des cercles
            circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1, 50,
                                       param1=50, param2=30, minRadius=1, maxRadius=250)

            if circles is not None:
                circles = np.uint16(np.around(circles))
                for i in circles[0, :]:
                    cv2.circle(frame, (i[0], i[1]), i[2], (0, 255, 0), 2)
                    cv2.circle(frame, (i[0], i[1]), 2, (0, 0, 255), 3)
                    print(f"🟠 Sphère détectée à x={i[0]}, y={i[1]}, rayon={i[2]}")

            # Affichage avec Matplotlib
            ax.clear()
            ax.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            ax.set_xticks([]), ax.set_yticks([])
            plt.pause(0.03)

    except KeyboardInterrupt:
        print("\n🚪 Programme arrêté proprement.")
    finally:
        cap.release()
        plt.ioff()
        plt.show()

# Remplace par l'URL de ta caméra
detect_spheres_from_stream("http://192.168.135.149:8080/video")

#412030
