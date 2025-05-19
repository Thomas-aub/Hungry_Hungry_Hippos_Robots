"""
Module d'analyse pour la détection de QR codes et de balles colorées (rouges et bleues)
Auteur : (ton nom ici)
Date : 2025-05-19

Ce module est conçu pour être utilisé dans un flux vidéo en temps réel. Il contient les fonctions suivantes :
- Chargement et traitement d'un QR code de référence
- Détection de QR codes dans les images
- Détection de balles rouges et bleues
- Sauvegarde de frames annotées
- Intégration dans un pipeline de traitement d'image
"""

import cv2
import numpy as np
import os
from datetime import datetime


############################
# Chargement QR de référence
############################
def load_reference_qr_code(filename="QR_Code.jpeg"):
    """Charge le QR code de référence"""
    reference_img = cv2.imread(filename)
    if reference_img is None:
        print(f"Erreur: Impossible de charger l'image {filename}")
        return None

    # Détection multiple pour les QR codes composites
    qcd = cv2.QRCodeDetector()
    retval, decoded_info, _, _ = qcd.detectAndDecodeMulti(reference_img)
    
    if not retval:
        # Essayer avec prétraitement si l'image est difficile
        processed = preprocess_for_qr(reference_img)
        retval, decoded_info, _, _ = qcd.detectAndDecodeMulti(processed)
        
        if not retval:
            print("Aucun QR code trouvé dans l'image de référence")
            return None

    print(f"QR code de référence chargé: {decoded_info}")
    return {'content': decoded_info, 'image': reference_img}
REFERENCE_QR_CODE = load_reference_qr_code()


############################
# Prétraitement de l'image
############################
def preprocess_for_qr(image):
    """Prépare l'image pour une meilleure détection de QR code"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Égalisation d'histogramme adaptative
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Démélangeage (débruitage)
    denoised = cv2.fastNlMeansDenoising(enhanced, None, h=10, templateWindowSize=7, searchWindowSize=21)
    
    # Amélioration du contraste
    alpha = 1.5  # Contraste (1.0-3.0)
    beta = 0     # Luminosité (0-100)
    adjusted = cv2.convertScaleAbs(denoised, alpha=alpha, beta=beta)
    
    # Binarisation adaptative
    binary = cv2.adaptiveThreshold(adjusted, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                 cv2.THRESH_BINARY, 11, 2)
    
    return binary

def detect_qr_code(frame, debug_display=False):
    """Détecte un QR code même vu en perspective"""
    if REFERENCE_QR_CODE is None:
        print("Aucun QR code de référence chargé")
        return False, None, None

    # 1. Essayer d'abord la détection directe
    qcd = cv2.QRCodeDetector()
    retval, decoded_info, points, _ = qcd.detectAndDecodeMulti(frame)
    
    # Ajout du log ici
    print(f"Détection directe - Résultat: {retval}, Contenu: {decoded_info}")
    
    if retval:
        for i, content in enumerate(decoded_info):
            if content and content in REFERENCE_QR_CODE['content']:
                print(f"QR code reconnu (méthode directe): {content}")
                return True, points[i], content

    # 2. Si échec, essayer avec prétraitement amélioré
    processed = preprocess_for_qr(frame)
    retval, decoded_info, points, _ = qcd.detectAndDecodeMulti(processed)
    
    # Ajout du log ici aussi
    print(f"Détection avec prétraitement - Résultat: {retval}, Contenu: {decoded_info}")
    
    if retval:
        for i, content in enumerate(decoded_info):
            if content and content in REFERENCE_QR_CODE['content']:
                print(f"QR code reconnu (avec prétraitement): {content}")
                return True, points[i], content

    # 3. Dernier recours: recherche de motifs carrés
    if debug_display:
        debug_img = frame.copy()
    
    # Trouver les contours dans l'image prétraitée
    contours, _ = cv2.findContours(processed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        # Approximer le contour
        epsilon = 0.02 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        
        # Nous cherchons des quadrilatères (4 côtés)
        if len(approx) == 4:
            # Vérifier la convexité et la surface raisonnable
            area = cv2.contourArea(approx)
            if 1000 < area < 50000 and cv2.isContourConvex(approx):
                # Essayer de lire le QR code dans cette région
                warped = warp_candidate_region(processed, approx)
                content, _, _ = qcd.detectAndDecode(warped)
                
                if content and content in REFERENCE_QR_CODE['content']:
                    return True, approx.reshape(4, 2), content
                
                if debug_display:
                    cv2.drawContours(debug_img, [approx], -1, (0, 255, 255), 2)
    
    if debug_display:
        cv2.imshow("QR Debug", debug_img)
    
    return False, None, None


############################
# Sauvegarde d'image
############################
def save_detected_frame(frame):
    """
    Sauvegarde une image avec un nom horodaté dans le dossier 'detections'
    """
    os.makedirs('detections', exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"detections/frame_{timestamp}.png"
    cv2.imwrite(filename, frame)
    print(f"Frame enregistrée : {filename}")


############################
# Analyse principale
############################
def analysis(frame):
    """
    Détecte les balles rouges/bleues et le QR code dans une frame

    Args:
        frame (np.ndarray): image à analyser

    Returns:
        tuple: (image annotée, résultats de détection)
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

    # QR code
    is_detected, qr_points, qr_content = detect_qr_code(frame, debug_display=True)
    if is_detected:
        detected_qr['detected'] = True
        detected_qr['points'] = qr_points
        detected_qr['content'] = qr_content
        qr_points = qr_points.astype(np.int32)
        cv2.polylines(result_frame, [qr_points], True, (0, 255, 0), 3)
        cv2.circle(result_frame, tuple(qr_points[0]), 10, (0, 0, 255), -1)
        cv2.putText(result_frame, f"QR: {qr_content}", (qr_points[0][0], qr_points[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Balles
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv[:, :, 2] = cv2.equalizeHist(hsv[:, :, 2])

    for color in color_thresholds:
        combined_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for threshold in color_thresholds[color]:
            mask = cv2.inRange(hsv, threshold['lower'], threshold['upper'])
            combined_mask = cv2.bitwise_or(combined_mask, mask)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.dilate(mask, kernel, iterations=2)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 30:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 50 or h > 50:
                continue
            perimeter = cv2.arcLength(cnt, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            if circularity < 0.5:
                continue

            (cx, cy), radius = cv2.minEnclosingCircle(cnt)
            center = (int(cx), int(cy))
            radius = int(radius)
            if 3 <= radius <= 25:
                detected_balls[color].append((center[0], center[1], radius))
                color_bgr = (0, 0, 255) if color == 'red' else (255, 0, 0)
                cv2.circle(result_frame, center, radius, color_bgr, 2)
                cv2.circle(result_frame, center, 2, (0, 255, 0), 3)
                cv2.putText(result_frame, f"{color} {radius}", (center[0]-radius, center[1]-radius-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    detected_balls['qr_code'] = detected_qr
    return result_frame, detected_balls


############################
# Intégration à la pipeline
############################
def incomingFrame(frame, iframe, frame_id):
    """
    Traite une nouvelle frame et stocke les résultats dans un objet iframe

    Args:
        frame (np.ndarray): image BGR
        iframe (Frame): objet contenant les résultats
        frame_id (int): identifiant de frame
    """
    analyzed_frame, balls_data = analysis(frame)
    iframe.mat = analyzed_frame
    iframe.analysis_result = balls_data
    iframe.id = frame_id
