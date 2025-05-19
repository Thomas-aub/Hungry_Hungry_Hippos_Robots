import cv2
import numpy as np
import os
from datetime import datetime

def save_detected_frame(frame):
    """
    Sauvegarde l'image avec les balles détectées et les marqueurs ArUco.
    
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
    Analyse l'image pour détecter les balles rouges, bleues et le marqueur ArUco (DICT_6X6_50, id:10).
    
    Args:
        frame (numpy.ndarray): Image à analyser
        
    Returns:
        tuple: (image annotée, dictionnaire contenant les positions des balles et du marqueur ArUco détectés)
            - L'image annotée contient les cercles et informations sur les balles détectées et le marqueur ArUco
            - Le dictionnaire est structuré: {
                  'red': [(x1,y1,r1), ...], 
                  'blue': [(x2,y2,r2), ...],
                  'aruco': {'id10': {'corners': [...], 'center': (x,y)}}
              où x,y sont les coordonnées et r est le rayon
              
    Note:
        Pour les balles:
        - Utilise des filtres HSV pour détecter les couleurs
        - Taille maximale de 25px
        - Circularité minimale de 0.5
        - Rayon entre 5 et 20 pixels
        
        Pour l'ArUco:
        - Détecte uniquement le marqueur avec id=10 du dictionnaire DICT_6X6_50
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
    detected_balls = {'red': [], 'blue': [], 'aruco': {}}
    
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
            if circularity < 0.5:
                continue
            
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            center = (int(x), int(y))
            radius = int(radius)
            
            if  3 <= radius <= 25:
                detected_balls[color].append((center[0], center[1], radius))
                color_bgr = (0, 0, 255) if color == 'red' else (255, 0, 0)
                cv2.circle(result_frame, center, radius, color_bgr, 2)
                cv2.circle(result_frame, center, 2, (0, 255, 0), 3)
                cv2.putText(result_frame, f"{color} {radius}", (center[0]-radius, center[1]-radius-5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
    
    # Détection du marqueur ArUco (nouveau code)
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_50)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
    
    corners, ids, rejected = detector.detectMarkers(frame)
    
    if ids is not None:
        for i in range(len(ids)):
            if ids[i] == 10:  # Nous ne nous intéressons qu'au marqueur avec id=10
                # Dessiner le marqueur détecté
                cv2.aruco.drawDetectedMarkers(result_frame, [corners[i]], np.array([ids[i]]))
                
                # Calculer le centre du marqueur
                center = corners[i][0].mean(axis=0)
                center = tuple(map(int, center))
                
                # Stocker les informations dans le dictionnaire
                detected_balls['aruco']['id10'] = {
                    'corners': corners[i][0].tolist(),
                    'center': center
                }
                
                # Ajouter un texte avec l'ID
                cv2.putText(result_frame, f"ArUco ID:10", (center[0]-20, center[1]-20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    
    return result_frame, detected_balls

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