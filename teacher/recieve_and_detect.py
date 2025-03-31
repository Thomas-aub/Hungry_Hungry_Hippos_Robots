import socket
import cv2
import numpy as np
import struct
import threading
import select
import os
from datetime import datetime

class Frame:
    """
    Classe représentant une trame vidéo avec résultats d'analyse.
    
    Attributs:
        mat (numpy.ndarray): Matrice contenant les données de l'image
        id (int): Identifiant unique de la trame
        analysis_result (dict): Résultats de l'analyse des balles détectées
        qr_data (tuple): Données du QR code détecté (points, angle, info)
    """
    def __init__(self, w, h):
        """
        Initialise une nouvelle instance de Frame.
        
        Args:
            w (int): Largeur de l'image en pixels
            h (int): Hauteur de l'image en pixels
        """
        self.mat = np.zeros((h, w, 3), dtype=np.uint8)
        self.id = -1
        self.analysis_result = None
        self.qr_data = None  # Stocke les infos du QR code

# Variables globales
frame_counter = 0
MAX_SAVED_FRAMES = 5
QR_REFERENCE = "QR_Code.jpeg"  # Chemin vers votre QR code de référence

def load_qr_reference():
    """
    Charge le QR code de référence pour la comparaison.
    
    Returns:
        numpy.ndarray ou None: Image en niveaux de gris du QR code de référence,
                               ou None si le fichier n'est pas trouvé
    """
    if not os.path.exists(QR_REFERENCE):
        print(f"Attention: Fichier QR référence {QR_REFERENCE} non trouvé")
        return None
    return cv2.imread(QR_REFERENCE, cv2.IMREAD_GRAYSCALE)

# Chargement du QR code de référence au démarrage
qr_reference = load_qr_reference()
qr_detector = cv2.QRCodeDetector()

def detect_and_orient_qr(frame):
    """
    Détecte le QR code dans l'image et détermine son orientation.
    
    Args:
        frame (numpy.ndarray): Image à analyser
        
    Returns:
        tuple: Contenant:
            - points (numpy.ndarray ou None): Coordonnées des coins du QR code détecté
            - angle (float ou None): Angle d'orientation du QR code en degrés
            - info (str ou None): Données décodées du QR code
    """
    global qr_reference
    
    # Détection des QR codes
    ret_qr, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(frame)
    
    if not ret_qr or points is None:
        return None, None, None
    
    # Recherche du QR code spécifique
    for i, (info, qr_points) in enumerate(zip(decoded_info, points)):
        # Si on a une référence, on compare avec le QR code détecté
        if qr_reference is not None:
            # Extraire la région du QR code détecté
            qr_pts = qr_points.astype(np.int32)
            x, y, w, h = cv2.boundingRect(qr_pts)
            qr_region = frame[y:y+h, x:x+w]
            qr_region_gray = cv2.cvtColor(qr_region, cv2.COLOR_BGR2GRAY)
            qr_region_gray = cv2.resize(qr_region_gray, (qr_reference.shape[1], qr_reference.shape[0]))
            
            # Comparaison avec la référence
            match_score = cv2.matchTemplate(qr_region_gray, qr_reference, cv2.TM_CCOEFF_NORMED)[0][0]
            if match_score < 0.7:  # Seuil de similarité
                continue
        
        # Calcul de l'orientation
        center = np.mean(qr_points, axis=0)[0]
        top_center = (qr_points[0][0] + qr_points[1][0]) / 2
        direction = top_center - center
        angle = np.degrees(np.arctan2(direction[1], direction[0])) % 360
        
        return qr_points, angle, info if info else "No data"
    
    return None, None, None

def save_detected_frame(frame, analysis_result, qr_data):
    """
    Enregistre l'image avec les résultats de détection (balles et QR code).
    
    Args:
        frame (numpy.ndarray): Image à enregistrer
        analysis_result (dict): Résultats de détection des balles
        qr_data (tuple ou None): Données du QR code détecté (points, angle, info)
    """
    global frame_counter
    
    if frame_counter >= MAX_SAVED_FRAMES:
        return
    
    if not os.path.exists('detections'):
        os.makedirs('detections')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"detections/frame_{timestamp}_{frame_counter}.png"
    
    # Ajout des infos QR code si détecté
    if qr_data is not None:
        points, angle, info = qr_data
        cv2.polylines(frame, [points.astype(np.int32)], True, (0, 255, 0), 3)
        center = np.mean(points, axis=0)[0]
        cv2.putText(frame, f"QR: {info} ({angle:.1f}°)", 
                   (int(center[0])-50, int(center[1])-20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    cv2.imwrite(filename, frame)
    print(f"Frame enregistrée: {filename}")
    frame_counter += 1

def analysis(frame):
    """
    Analyse une image pour détecter les balles colorées et les QR codes.
    
    Args:
        frame (numpy.ndarray): Image à analyser
        
    Returns:
        tuple: Contenant:
            - result_frame (numpy.ndarray): Image avec annotations des détections
            - detected_balls (dict): Dictionnaire des balles détectées par couleur
            - qr_data (tuple ou None): Données du QR code détecté (points, angle, info)
    """
    # Détection des balles (code existant)
    color_thresholds = {
        'red': [
            {'lower': np.array([0, 120, 70]), 'upper': np.array([10, 255, 255])},
            {'lower': np.array([170, 120, 70]), 'upper': np.array([180, 255, 255])}
        ],
        'blue': [
            {'lower': np.array([90, 120, 70]), 'upper': np.array([120, 255, 255])}
        ]
    }
    
    result_frame = frame.copy()
    detected_balls = {'red': [], 'blue': []}
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv[:,:,2] = cv2.equalizeHist(hsv[:,:,2])
    
    for color in color_thresholds:
        combined_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for threshold in color_thresholds[color]:
            mask = cv2.inRange(hsv, threshold['lower'], threshold['upper'])
            combined_mask = cv2.bitwise_or(combined_mask, mask)
        
        kernel = np.ones((5,5), np.uint8)
        cleaned_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        cleaned_mask = cv2.dilate(cleaned_mask, kernel, iterations=2)
        
        contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        min_radius = 5
        max_radius = 100
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 30:
                continue
                
            (x,y), radius = cv2.minEnclosingCircle(cnt)
            center = (int(x), int(y))
            radius = int(radius)
            
            if min_radius <= radius <= max_radius:
                detected_balls[color].append((center[0], center[1], radius))
                color_bgr = (0, 0, 255) if color == 'red' else (255, 0, 0)
                cv2.circle(result_frame, center, radius, color_bgr, 2)
                cv2.circle(result_frame, center, 2, (0, 255, 0), 3)
                cv2.putText(result_frame, f"{color} {radius}", 
                           (center[0]-radius, center[1]-radius-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
    
    # Détection du QR code
    qr_points, qr_angle, qr_info = detect_and_orient_qr(frame)
    qr_data = None
    
    if qr_points is not None:
        # Dessiner le contour et l'orientation
        cv2.polylines(result_frame, [qr_points.astype(np.int32)], True, (0, 255, 0), 3)
        center = np.mean(qr_points, axis=0)[0]
        
        # Dessiner une flèche pour l'orientation
        top_center = (qr_points[0][0] + qr_points[1][0]) / 2
        cv2.arrowedLine(result_frame, 
                       (int(center[0]), int(center[1])), 
                       (int(top_center[0]), int(top_center[1])), 
                       (0, 255, 255), 2)
        
        # Ajouter le texte
        cv2.putText(result_frame, f"QR: {qr_info} ({qr_angle:.1f}°)", 
                   (int(center[0])-50, int(center[1])-20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        qr_data = (qr_points, qr_angle, qr_info)
    
    return result_frame, detected_balls, qr_data

def incomingFrame(frame, iframe, frame_id):
    """
    Traite une nouvelle trame reçue, effectue l'analyse et met à jour l'objet Frame.
    
    Args:
        frame (numpy.ndarray): Nouvelle image à traiter
        iframe (Frame): Objet Frame à mettre à jour
        frame_id (int): Identifiant de la trame
    """
    analyzed_frame, balls_data, qr_data = analysis(frame)
    iframe.mat = analyzed_frame
    iframe.analysis_result = balls_data
    iframe.qr_data = qr_data
    iframe.id = frame_id
    
    if any(balls_data.values()) or qr_data is not None:
        save_detected_frame(analyzed_frame, balls_data, qr_data)


def main():
    """
    Fonction principale qui initialise le socket UDP, lance le thread de capture
    et gère l'affichage des résultats de détection.
    """
    stopProgram = threading.Event()
    stopThread = threading.Event()
    threadRunning = threading.Event()
    ip = ""
    port = 8080
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    sock.bind((ip, port))
    print("Listening for UDP frames...")
    frame = Frame(100,100)
    stopProgram.clear()
    stopThread.clear()
    thread = threading.Thread(target=captureThread, args=[sock,frame,stopThread,threadRunning], daemon=True)
    thread.start()
    
    while not stopProgram.is_set():
        if frame is not None:
            cv2.imshow("Received Frame", frame.mat)
            
            if frame.analysis_result:
                print(f"Balles rouges: {frame.analysis_result['red']}")
                print(f"Balles bleues: {frame.analysis_result['blue']}")
            
            if frame.qr_data is not None:
                _, angle, info = frame.qr_data
                print(f"QR Code détecté: {info} (Orientation: {angle:.1f}°)")
        
        ch = chr(cv2.waitKey(int(1)) & 0xFF)
        if ch=='q' or ch=='Q': stopProgram.set()
    
    stopThread.set()
    while threadRunning.is_set(): pass
    sock.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()