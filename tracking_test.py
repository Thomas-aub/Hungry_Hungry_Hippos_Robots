import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import os

# Seuils HSV pour la détection des couleurs
color_thresholds = {
    'blue': {'lower': np.array([80, 100, 50]), 'upper': np.array([120, 255, 255])},
    'orange': {'lower': np.array([5, 100, 100]), 'upper': np.array([25, 255, 255])}
}

def load_qr_reference(qr_path):
    """Charge l'image de référence du QR code"""
    if not os.path.exists(qr_path):
        print(f"Erreur: Le fichier QR code '{qr_path}' n'existe pas.")
        return None
    
    try:
        qr_img = cv2.imread(qr_path)
        # Convertir en gris pour la détection
        qr_gray = cv2.cvtColor(qr_img, cv2.COLOR_BGR2GRAY)
        return qr_gray
    except Exception as e:
        print(f"Erreur lors du chargement du QR code: {e}")
        return None

def init_detector():
    """Initialise le détecteur de QR code"""
    try:
        qr_detector = cv2.QRCodeDetector()
        return qr_detector
    except Exception as e:
        print(f"Erreur lors de l'initialisation du détecteur de QR code: {e}")
        return None

def detect_spheres(frame, color):
    """Détecte les sphères d'une couleur spécifique dans l'image"""
    # Conversion en HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Normalisation de la luminosité
    hsv[:,:,2] = cv2.equalizeHist(hsv[:,:,2])
    
    # Création du masque pour la couleur
    lower = color_thresholds[color]['lower']
    upper = color_thresholds[color]['upper']
    mask = cv2.inRange(hsv, lower, upper)
    
    # Morphologie pour séparer les objets collés
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # Appliquer un flou pour lisser les bords
    blurred = cv2.GaussianBlur(mask, (9, 9), 2)
    
    # Détection des cercles
    circles = cv2.HoughCircles(
        blurred, 
        cv2.HOUGH_GRADIENT, 
        1, 
        50,
        param1=50, 
        param2=30, 
        minRadius=1, 
        maxRadius=250
    )
    
    detected_spheres = []
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            # Ajouter les coordonnées et le rayon à la liste
            detected_spheres.append((i[0], i[1], i[2]))
            # Dessiner les cercles sur l'image
            cv2.circle(frame, (i[0], i[1]), i[2], (0, 255, 0), 2)
            cv2.circle(frame, (i[0], i[1]), 2, (0, 0, 255), 3)
    
    return detected_spheres

def detect_qr_code(frame, qr_detector):
    """Détecte un QR code dans l'image"""
    try:
        # Conversion en niveaux de gris
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Détection du QR code
        ret_qr, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(gray)
        
        if ret_qr and points is not None:
            # Dessiner le contour du QR code
            points = points.astype(np.int32)
            for i in range(len(points)):
                cv2.polylines(frame, [points[i]], True, (0, 255, 0), 3)
                
                # Calculer le centre du QR code
                center_x = int(np.mean(points[i][:, 0]))
                center_y = int(np.mean(points[i][:, 1]))
                
                # Dessiner le centre du QR code
                cv2.circle(frame, (center_x, center_y), 5, (255, 0, 0), -1)
                
                return [(center_x, center_y, decoded_info[i] if i < len(decoded_info) else "")]
        
        return []
    
    except Exception as e:
        print(f"Erreur lors de la détection du QR code: {e}")
        return []

def print_detections(blue_spheres, orange_spheres, qr_codes):
    """Affiche les détections dans le terminal"""
    # Afficher les balles bleues
    for i, (x, y, _) in enumerate(blue_spheres):
        print(f"{i+1} - Blue ball in x:{x}, y:{y}")
    
    # Afficher les balles orange (rouges)
    for i, (x, y, _) in enumerate(orange_spheres):
        print(f"{i+len(blue_spheres)+1} - Red ball in x:{x}, y:{y}")
    
    # Afficher les QR codes
    for i, (x, y, _) in enumerate(qr_codes):
        print(f"{i+len(blue_spheres)+len(orange_spheres)+1} - QRCode in x:{x}, y:{y}")
    
    print("-" * 40)  # Séparateur pour une meilleure lisibilité

def detect_objects_from_stream(stream_url, qr_path, interval=1.0):
    """
    Fonction principale de détection d'objets depuis un flux vidéo
    
    Args:
        stream_url: URL du flux vidéo
        qr_path: Chemin vers l'image du QR code de référence
        interval: Intervalle de temps (en secondes) entre chaque affichage des détections
    """
    # Initialisation de la caméra
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        print("Erreur: Impossible de se connecter à la caméra.")
        return
    
    # Initialisation du détecteur de QR code
    qr_detector = init_detector()
    if qr_detector is None:
        print("Erreur: Impossible d'initialiser le détecteur de QR code.")
        cap.release()
        return
    
    # Chargement de l'image de référence du QR code
    qr_ref = load_qr_reference(qr_path)
    if qr_ref is None and qr_path:
        print("Avertissement: Fonctionnement sans référence de QR code.")
    
    # Initialisation de l'affichage Matplotlib
    plt.ion()
    fig, ax = plt.subplots()
    
    # Variable pour suivre le dernier moment d'affichage
    last_print_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Erreur: Impossible de lire l'image.")
                break
            
            # Détection des sphères bleues et orange
            blue_spheres = detect_spheres(frame, 'blue')
            orange_spheres = detect_spheres(frame, 'orange')
            
            # Détection du QR code
            qr_codes = detect_qr_code(frame, qr_detector)
            
            # Vérifier si c'est le moment d'afficher les détections
            current_time = time.time()
            if current_time - last_print_time >= interval:
                print_detections(blue_spheres, orange_spheres, qr_codes)
                last_print_time = current_time
            
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
        plt.close()

if __name__ == "__main__":
    # Paramètres configurables
    stream_url = "http://192.168.135.149:8080/video"  # URL de la caméra
    qr_path = "QRcode.png"  # Chemin vers l'image QR code de référence
    print_interval = 2.0  # Intervalle entre les affichages (en secondes)
    
    # Lancement de la détection
    detect_objects_from_stream(stream_url, qr_path, print_interval)