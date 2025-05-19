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
    """
    Charge le QR code de référence et en extrait le contenu

    Args:
        filename (str): chemin vers l'image du QR code

    Returns:
        dict: Contenu et image du QR code de référence
    """
    reference_img = cv2.imread(filename)
    if reference_img is None:
        print(f"Erreur: Impossible de charger l'image {filename}")
        return None

    gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY)
    qcd = cv2.QRCodeDetector()
    retval, decoded_info, _, _ = qcd.detectAndDecodeMulti(gray)

    if not retval:
        print("Aucun QR code trouvé dans l'image de référence")
        return None

    return {'content': decoded_info, 'image': reference_img}


REFERENCE_QR_CODE = load_reference_qr_code()


############################
# Prétraitement de l'image
############################
def preprocess_for_qr(image):
    """
    Prépare l'image pour une meilleure détection de QR code : contraste, netteté, adaptatif.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Histogramme adaptatif (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)

    # Amélioration de la netteté
    blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=3)
    sharpened = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)

    return sharpened

def warp_candidate_region(gray, box, size=300):
    """
    Corrige la perspective d'une région candidate pour lecture du QR code.

    Args:
        gray (np.ndarray): Image en niveaux de gris
        box (np.ndarray): 4 points de contour (shape: 4x1x2)
        size (int): Taille de sortie normalisée (pixels carrés)

    Returns:
        np.ndarray: ROI redressée
    """
    pts = box.reshape(4, 2).astype(np.float32)
    
    # Ordre: top-left, top-right, bottom-right, bottom-left
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    ordered = np.array([
        pts[np.argmin(s)],
        pts[np.argmin(diff)],
        pts[np.argmax(s)],
        pts[np.argmax(diff)]
    ], dtype=np.float32)

    dst = np.array([
        [0, 0],
        [size - 1, 0],
        [size - 1, size - 1],
        [0, size - 1]
    ], dtype=np.float32)

    M = cv2.getPerspectiveTransform(ordered, dst)
    warped = cv2.warpPerspective(gray, M, (size, size))
    return warped




def detect_qr_code(frame, debug_display=False):
    """
    Détecte un QR code même vu en perspective, en cherchant les zones blanches dans l'image.

    Args:
        frame (np.ndarray): Image couleur
        debug_display (bool): Si True, affiche un point rose sur chaque candidat

    Returns:
        tuple: (détecté: bool, points: np.ndarray ou None, contenu: str ou None)
    """
    if REFERENCE_QR_CODE is None:
        return False, None, None

    scale = 2
    resized = cv2.resize(frame, None, fx=scale, fy=scale)
    gray = preprocess_for_qr(resized)

    # 1. Détection directe classique
    qcd = cv2.QRCodeDetector()
    retval, decoded_info, points, _ = qcd.detectAndDecodeMulti(gray)
    if retval:
        for i, content in enumerate(decoded_info):
            if content and content in REFERENCE_QR_CODE['content']:
                pts = (points[i] / scale).astype(np.int32)
                return True, pts, content

    # 2. Recherche de zones blanches (luminance élevée)
    _, white_mask = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8)
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 1000 or area > 50000:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        roi = gray[y:y+h, x:x+w]
        roi = cv2.resize(roi, (300, 300))
        content, _, _ = qcd.detectAndDecode(roi)

        if content and content in REFERENCE_QR_CODE['content']:
            # Retourner les 4 coins estimés du rectangle
            points = np.array([
                [x, y],
                [x + w, y],
                [x + w, y + h],
                [x, y + h]
            ], dtype=np.float32) / scale
            return True, points, content

        if debug_display:
            # Dessiner un point rose au centre du contour candidat
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"] / scale)
                cy = int(M["m01"] / M["m00"] / scale)
                cv2.circle(frame, (cx, cy), 6, (255, 0, 255), -1)

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
