import socket
import cv2
import numpy as np
import struct
import threading
import select
import os
from datetime import datetime

class Frame:
    def __init__(self,w,h):
        self.mat = np.zeros((h,w,3),dtype=np.uint8)
        self.id = -1
        self.analysis_result = None

# Variable globale pour le compteur de frames enregistrées
frame_counter = 0
MAX_SAVED_FRAMES = 5

def save_detected_frame(frame, analysis_result):
    """Enregistre la frame avec les balles détectées"""
    global frame_counter
    
    if frame_counter >= MAX_SAVED_FRAMES:
        return
    
    # Créer un dossier pour les captures s'il n'existe pas
    if not os.path.exists('detections'):
        os.makedirs('detections')
    
    # Générer un nom de fichier avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"detections/frame_{timestamp}_{frame_counter}.png"
    
    # Sauvegarder l'image
    cv2.imwrite(filename, frame)
    print(f"Frame enregistrée: {filename}")
    
    # Incrémenter le compteur
    frame_counter += 1

def analysis(frame):
    """
    Analyse une image pour détecter des balles rouges et bleues
    Retourne un tuple contenant:
    - L'image annotée avec les détections
    - Un dictionnaire des positions des balles
    """
    # Définition des plages de couleurs HSV (à calibrer selon votre environnement)
    color_thresholds = {
        'red': [
            {'lower': np.array([0, 120, 70]), 'upper': np.array([10, 255, 255])},  # Rouge clair
            {'lower': np.array([170, 120, 70]), 'upper': np.array([180, 255, 255])}  # Rouge foncé
        ],
        'blue': [
            {'lower': np.array([90, 120, 70]), 'upper': np.array([120, 255, 255])}  # Bleu
        ]
    }
    
    # Préparation de l'image de résultat
    result_frame = frame.copy()
    detected_balls = {'red': [], 'blue': []}
    
    # Conversion en HSV et normalisation
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv[:,:,2] = cv2.equalizeHist(hsv[:,:,2])
    
    # Traitement pour chaque couleur
    for color in color_thresholds:
        # Création d'un masque combiné pour les différentes plages de la couleur
        combined_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for threshold in color_thresholds[color]:
            mask = cv2.inRange(hsv, threshold['lower'], threshold['upper'])
            combined_mask = cv2.bitwise_or(combined_mask, mask)
        
        # Amélioration du masque
        kernel = np.ones((5,5), np.uint8)
        cleaned_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        cleaned_mask = cv2.dilate(cleaned_mask, kernel, iterations=2)
        
        # Détection des contours
        contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrage des contours et détection des cercles
        min_radius = 5
        max_radius = 100
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 30:  # Filtre les petits artefacts
                continue
                
            (x,y), radius = cv2.minEnclosingCircle(cnt)
            center = (int(x), int(y))
            radius = int(radius)
            
            if min_radius <= radius <= max_radius:
                # Valid circle detected
                detected_balls[color].append((center[0], center[1], radius))
                
                # Dessin sur l'image de résultat
                color_bgr = (0, 0, 255) if color == 'red' else (255, 0, 0)
                cv2.circle(result_frame, center, radius, color_bgr, 2)
                cv2.circle(result_frame, center, 2, (0, 255, 0), 3)
                cv2.putText(result_frame, f"{color} {radius}", 
                           (center[0]-radius, center[1]-radius-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
    
    return result_frame, detected_balls

def incomingFrame(frame, iframe, frame_id):
    # Analyse l'image et stocke les résultats
    analyzed_frame, balls_data = analysis(frame)
    iframe.mat = analyzed_frame
    iframe.analysis_result = balls_data
    iframe.id = frame_id
    
    # Enregistrement des premières frames avec détections
    if any(balls_data.values()):  # Si au moins une balle détectée
        save_detected_frame(analyzed_frame, balls_data)

def gotFullData(data_buffer,iframe, frame_id):
    # Reconstruct the full frame
    full_data = b''.join([data_buffer[i] for i in sorted(data_buffer)])
    messageLength = struct.unpack("I",full_data[0:4])[0]
    frame_data = full_data[4:]
    if len(frame_data) == messageLength:
        #do we have all data
        frame_buffer = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(frame_buffer,1)
        if frame is not None:
            # is frame ok
            incomingFrame(frame,iframe, frame_id)

def captureThread(sock,frame,stopThread,threadRunning):
    MaximumPacketSize = 1400
    timeout_ms = 0.01
    data_buffer = {}
    current_frame_id = -1
    threadRunning.set()
    while not stopThread.is_set():
        try:
            read_ready, _, _ = select.select([sock], [], [], timeout_ms)
            readSet = bool(read_ready)  # True if data is ready to be read
            if read_ready and readSet:
                packet, addr = sock.recvfrom(MaximumPacketSize)
                packet_id, frame_id = struct.unpack('II', packet[:8])
                payload = packet[8:]
                if frame_id != current_frame_id:
                    if current_frame_id != -1:
                        gotFullData(data_buffer,frame, frame_id)
                    # Reset buffer for new frame
                    data_buffer = {}
                    current_frame_id = frame_id
                data_buffer[packet_id] = payload
        except socket.error:
            continue
    threadRunning.clear()

def main():
    stopProgram = threading.Event()
    stopThread = threading.Event()
    threadRunning = threading.Event()
    # Configuration
    ip = ""  # listen to all interfaces
    port = 8080
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    sock.bind((ip, port))
    print("Listening for UDP frames...")
    frame = Frame(100,100)
    stopProgram.clear()
    stopThread.clear()
    thread = threading.Thread(target=captureThread,args = [sock,frame,stopThread,threadRunning], daemon=True)
    thread.start()
    while not stopProgram.is_set():
        if frame is not None:
            cv2.imshow("Received Frame", frame.mat)
            
            # Accès aux données d'analyse
            if frame.analysis_result:
                print(f"Balles rouges: {frame.analysis_result['red']}")
                print(f"Balles bleues: {frame.analysis_result['blue']}")
                
        ch = chr(cv2.waitKey(int(1)) & 0xFF)
        if ch=='q' or ch=='Q': stopProgram.set()
    
    stopThread.set()
    while threadRunning.is_set(): pass
    sock.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()