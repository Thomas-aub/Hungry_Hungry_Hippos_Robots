import socket
import cv2
import numpy as np
import struct
import threading
import select
import matplotlib.pyplot as plt

# Classe Frame et fonctions du fichier receive.py
class Frame:
    def __init__(self, w, h):
        self.mat = np.zeros((h, w, 3), dtype=np.uint8)
        self.id = -1

def incomingFrame(frame, iframe, frame_id):
    iframe.mat = frame.copy()
    iframe.id = frame_id

def gotFullData(data_buffer, iframe, frame_id):
    # Reconstruct the full frame
    full_data = b''.join([data_buffer[i] for i in sorted(data_buffer)])
    messageLength = struct.unpack("I", full_data[0:4])[0]
    frame_data = full_data[4:]
    if len(frame_data) == messageLength:
        frame_buffer = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(frame_buffer, 1)
        if frame is not None:
            incomingFrame(frame, iframe, frame_id)

def captureThread(sock, frame, stopThread, threadRunning):
    MaximumPacketSize = 1400
    timeout_ms = 0.01
    data_buffer = {}
    current_frame_id = -1
    threadRunning.set()
    while not stopThread.is_set():
        try:
            read_ready, _, _ = select.select([sock], [], [], timeout_ms)
            readSet = bool(read_ready)
            if read_ready and readSet:
                packet, addr = sock.recvfrom(MaximumPacketSize)
                packet_id, frame_id = struct.unpack('II', packet[:8])
                payload = packet[8:]
                if frame_id != current_frame_id:
                    if current_frame_id != -1:
                        gotFullData(data_buffer, frame, frame_id)
                    data_buffer = {}
                    current_frame_id = frame_id
                data_buffer[packet_id] = payload
        except socket.error:
            continue
    threadRunning.clear()

# Fonctions de détection de balles du fichier ball_tracking.py
# Ajustement des seuils HSV
lower_orange = np.array([5, 100, 100])  
upper_orange = np.array([25, 255, 255])  

lower_blue = np.array([80, 100, 50])  
upper_blue = np.array([120, 255, 255])  

def detect_balls(frame):
    if frame is None or frame.size == 0:
        return frame, []
        
    # Conversion en HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Normalisation de la luminosité
    hsv[:,:,2] = cv2.equalizeHist(hsv[:,:,2])

    # Détection du bleu
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
    
    # Détection de l'orange
    mask_orange = cv2.inRange(hsv, lower_orange, upper_orange)
    
    # Combinaison des masques
    mask = cv2.bitwise_or(mask_blue, mask_orange)

    # Morphologie pour séparer les objets collés
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # Appliquer un flou pour lisser les bords
    blurred = cv2.GaussianBlur(mask, (9, 9), 2)

    # Détection des cercles
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1, 50,
                              param1=50, param2=30, minRadius=1, maxRadius=250)

    detected_circles = []
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            # Dessiner le cercle et son centre
            cv2.circle(frame, (i[0], i[1]), i[2], (0, 255, 0), 2)
            cv2.circle(frame, (i[0], i[1]), 2, (0, 0, 255), 3)
            detected_circles.append((i[0], i[1], i[2]))
            
    return frame, detected_circles

def main():
    # Configuration
    ip = ""  # écouter sur toutes les interfaces
    # ip = "192.168.1.181"  # écouter sur une interface spécifique
    port = 8080
    
    # Création du socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    sock.bind((ip, port))
    print("Écoute des trames UDP...")
    
    # Initialisation des événements de thread et de la frame
    stopProgram = threading.Event()
    stopThread = threading.Event()
    threadRunning = threading.Event()
    frame = Frame(640, 480)  # Taille initiale, sera ajustée avec les frames reçues
    
    # Démarrage du thread de capture
    stopProgram.clear()
    stopThread.clear()
    thread = threading.Thread(target=captureThread, args=[sock, frame, stopThread, threadRunning], daemon=True)
    thread.start()
    
    # Configuration pour l'affichage avec matplotlib
    plt.ion()
    fig, ax = plt.subplots()
    
    # Boucle principale de traitement et d'affichage
    try:
        last_frame_id = -1
        while not stopProgram.is_set():
            if frame.id != last_frame_id and frame.mat is not None and frame.mat.size > 0:
                last_frame_id = frame.id
                
                # Détection des balles
                processed_frame, circles = detect_balls(frame.mat.copy())
                
                # Affichage des informations sur les cercles détectés
                for i, (x, y, r) in enumerate(circles):
                    print(f"Balle {i+1} détectée à x={x}, y={y}, rayon={r}")
                
                # Affichage avec Matplotlib
                ax.clear()
                ax.imshow(cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB))
                ax.set_title(f"Détection de balles - {len(circles)} balles trouvées")
                ax.set_xticks([])
                ax.set_yticks([])
                plt.pause(0.03)
                
            # Vérification de l'arrêt du programme
            if plt.waitforbuttonpress(0.01):
                stopProgram.set()
                
    except KeyboardInterrupt:
        print("\n🚪 Programme arrêté manuellement.")
    finally:
        # Nettoyage
        stopThread.set()
        while threadRunning.is_set():
            pass
        sock.close()
        plt.ioff()
        plt.close()
        print("Programme terminé.")

if __name__ == "__main__":
    main()