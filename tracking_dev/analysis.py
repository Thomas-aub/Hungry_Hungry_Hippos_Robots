import cv2
import numpy as np
import os
from datetime import datetime

# Nouvelle fonction pour charger l'image du QR code de référence
def load_reference_qr_code(filename="QR_Code.jpeg"):
    """
    Charge le QR code de référence et extrait ses caractéristiques
    
    Args:
        filename (str): Chemin vers le fichier QR code de référence
        
    Returns:
        tuple: (image de référence, caractéristiques du QR code)
    """
    reference_img = cv2.imread(filename)
    if reference_img is None:
        print(f"Erreur: Impossible de charger l'image de référence {filename}")
        return None, None
    
    # Convertir en niveaux de gris pour la détection
    reference_gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY)
    
    # Détecter le QR code dans l'image de référence
    qcd = cv2.QRCodeDetector()
    retval, decoded_info, points, straight_qrcode = qcd.detectAndDecodeMulti(reference_gray)
    
    if not retval:
        print("Aucun QR code détecté dans l'image de référence")
        return reference_img, None
    
    # Extraire le contenu du QR code comme identifiant
    reference_data = {
        'content': decoded_info,
        'image': reference_img
    }
    
    return reference_data

# Variable globale pour stocker les données de référence du QR code
REFERENCE_QR_CODE = load_reference_qr_code()

def detect_qr_code(frame):
    """
    Détecte et identifie le QR code spécifique dans l'image
    
    Args:
        frame (numpy.ndarray): Image à analyser
        
    Returns:
        tuple: (booléen indiquant si le QR code de référence est détecté,
                points des coins du QR code, contenu décodé)
    """
    # Vérifier si l'image de référence a été chargée correctement
    if REFERENCE_QR_CODE is None:
        return False, None, None
    
    # Convertir en niveaux de gris pour la détection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Détecter le QR code
    qcd = cv2.QRCodeDetector()
    retval, decoded_info, points, straight_qrcode = qcd.detectAndDecodeMulti(gray)
    
    if not retval:
        return False, None, None
    
    # Vérifier si l'un des QR codes détectés correspond à notre référence
    for i, content in enumerate(decoded_info):
        if content in REFERENCE_QR_CODE['content']:
            # C'est notre QR code de référence
            return True, points[i], content
    
    # Aucun QR code correspondant trouvé
    return False, None, None

def save_detected_frame(frame):
    """
    Sauvegarde l'image avec les balles détectées.
    
    Args:
        frame (numpy.ndarray): Image avec les annotations de détection
        
    Returns:
        None
    
    Note:
        Les images sont sauvegardées dans le dossier 'detections' avec un timestamp
    """
    if not os.path.exists('detections'):
        os.makedirs('detections')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"detections/frame_{timestamp}.png"
    cv2.imwrite(filename, frame)
    print(f"Frame enregistrée: {filename}")

def analysis(frame):
    """
    Analyse l'image pour détecter les balles rouges et bleues et le QR code spécifique.
    
    Args:
        frame (numpy.ndarray): Image à analyser
        
    Returns:
        tuple: (image annotée, dictionnaire contenant les positions des balles et du QR code détectés)
            - L'image annotée contient les cercles et informations sur les balles détectées
            - Le dictionnaire est structuré: {
                'red': [(x1,y1,r1), ...], 
                'blue': [(x2,y2,r2), ...],
                'qr_code': {
                    'detected': bool,
                    'points': [(x1,y1), (x2,y2), (x3,y3), (x4,y4)],
                    'content': str
                }
              }
    """
    color_thresholds = {
        'red': [
            {'lower': np.array([0, 120, 70]), 'upper': np.array([30, 255, 255])},
        ],
        'blue': [
            {'lower': np.array([100, 50, 40]), 'upper': np.array([240, 255, 255])}
        ]
    }
    
    result_frame = frame.copy()
    detected_balls = {'red': [], 'blue': []}
    detected_qr = {'detected': False, 'points': None, 'content': None}
    
    # Détection du QR code
    is_detected, qr_points, qr_content = detect_qr_code(frame)
    if is_detected:
        detected_qr['detected'] = True
        detected_qr['points'] = qr_points
        detected_qr['content'] = qr_content
        
        # Dessiner le contour du QR code
        qr_points = qr_points.astype(np.int32)
        cv2.polylines(result_frame, [qr_points], True, (0, 255, 0), 3)
        
        # Identifier l'orientation en marquant le premier point
        if len(qr_points) > 0:
            cv2.circle(result_frame, (int(qr_points[0][0]), int(qr_points[0][1])), 10, (0, 0, 255), -1)
            
        # Ajouter le texte d'identification
        cv2.putText(result_frame, f"QR: {qr_content}", 
                   (int(qr_points[0][0]), int(qr_points[0][1]) - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Détection des balles (code existant)
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
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 30:
                continue
                
            # Calculer dimensions du rectangle englobant
            x, y, w, h = cv2.boundingRect(cnt)
            
            # Filtrer les objets trop grands (>25px dans les deux dimensions)
            if w > 50 or h > 50:
                continue
                
            # Vérifier la circularité pour identifier les sphères
            perimeter = cv2.arcLength(cnt, True)
            circularity = 0
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            # Filtre pour les objets circulaires (les sphères ont une circularité proche de 1)
            if circularity < 0.5:  # Un seuil de 0.7 est généralement bon pour les cercles
                continue
            
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            center = (int(x), int(y))
            radius = int(radius)
            
            if  3 <= radius <= 25:  # Réduire la plage de rayon pour mieux cibler les balles
                detected_balls[color].append((center[0], center[1], radius))
                color_bgr = (0, 0, 255) if color == 'red' else (255, 0, 0)
                cv2.circle(result_frame, center, radius, color_bgr, 2)
                cv2.circle(result_frame, center, 2, (0, 255, 0), 3)
                cv2.putText(result_frame, f"{color} {radius}", (center[0]-radius, center[1]-radius-5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
    
    # Ajouter les données QR au résultat
    result_data = detected_balls
    result_data['qr_code'] = detected_qr
    
    return result_frame, result_data

def incomingFrame(frame, iframe, frame_id):
    """
    Traite une nouvelle frame reçue du flux vidéo.
    
    Args:
        frame (numpy.ndarray): Image brute reçue du flux
        iframe (Frame): Objet Frame où stocker les résultats
        frame_id (int): Identifiant de la frame
        
    Returns:
        None
        
    Note:
        Modifie l'objet iframe en place pour stocker:
        - L'image analysée avec les annotations (iframe.mat)
        - Les résultats de détection (iframe.analysis_result)
        - L'identifiant de frame (iframe.id)
    """
    analyzed_frame, balls_data = analysis(frame)
    iframe.mat = analyzed_frame
    iframe.analysis_result = balls_data
    iframe.id = frame_id