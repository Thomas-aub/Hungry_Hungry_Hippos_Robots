import cv2
import numpy as np
import os
import math
from datetime import datetime

def save_detected_frame(frame):
    """
    Sauvegarde l'image avec les détections.
    """
    if not os.path.exists('detections'):
        os.makedirs('detections')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"detections/frame_{timestamp}.png"
    cv2.imwrite(filename, frame)
    print(f"Frame enregistrée: {filename}")

def calculate_distance(point1, point2):
    """
    Calcule la distance euclidienne entre deux points.
    
    Args:
        point1 (tuple): (x1, y1)
        point2 (tuple): (x2, y2)
        
    Returns:
        float: Distance entre les points
    """
    return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

def find_nearest_ball(aruco_center, balls_data):
    """
    Trouve la balle la plus proche du marqueur ArUco.
    
    Args:
        aruco_center (tuple): Centre du marqueur ArUco (x, y)
        balls_data (dict): Dictionnaire contenant les données des balles
        
    Returns:
        tuple: (ball_type, ball_info, distance) ou (None, None, None) si aucune balle
    """
    nearest_ball = None
    min_distance = float('inf')
    ball_type = None
    
    for color in ['red', 'blue']:
        for ball in balls_data[color]:
            ball_center = (ball[0], ball[1])
            distance = calculate_distance(aruco_center, ball_center)
            
            if distance < min_distance:
                min_distance = distance
                nearest_ball = ball
                ball_type = color
    
    return (ball_type, nearest_ball, min_distance) if nearest_ball else (None, None, None)

def display_distance_info(frame, aruco_center, ball_type, ball_info, distance):
    """
    Affiche les informations de distance sur l'image.
    
    Args:
        frame: Image sur laquelle dessiner
        aruco_center: Centre du marqueur ArUco
        ball_type: Type de balle ('red' ou 'blue')
        ball_info: Informations de la balle (x, y, radius)
        distance: Distance entre l'ArUco et la balle
    """
    if ball_info is None:
        return
    
    ball_center = (ball_info[0], ball_info[1])
    
    # Dessiner la ligne entre l'ArUco et la balle
    cv2.line(frame, aruco_center, ball_center, (0, 255, 255), 2)
    
    # Calculer le point milieu pour afficher la distance
    mid_point = (
        (aruco_center[0] + ball_center[0]) // 2,
        (aruco_center[1] + ball_center[1]) // 2
    )
    
    # Afficher les informations
    info_text = f"Dist: {distance:.1f}px"
    cv2.putText(frame, info_text, (mid_point[0]-40, mid_point[1]), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    
    # Afficher les coordonnées
    cv2.putText(frame, f"ArUco: {aruco_center}", (10, 20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    cv2.putText(frame, f"{ball_type} ball: {ball_center}", (10, 40), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    
    # Afficher dans la console
    print(f"\nArUco position: {aruco_center}")
    print(f"Nearest ball: {ball_type} at {ball_center}")
    print(f"Distance: {distance:.1f} pixels")

def analysis(frame):
    """
    Analyse l'image pour détecter les balles et l'ArUco, et trouve la balle la plus proche.
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
    
    # Détection des balles
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
                
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 50 or h > 50:
                continue
                
            perimeter = cv2.arcLength(cnt, True)
            circularity = 0
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            if circularity < 0.5:
                continue
            
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            center = (int(x), int(y))
            radius = int(radius)
            
            if 3 <= radius <= 25:
                detected_balls[color].append((center[0], center[1], radius))
                color_bgr = (0, 0, 255) if color == 'red' else (255, 0, 0)
                cv2.circle(result_frame, center, radius, color_bgr, 2)
                cv2.circle(result_frame, center, 2, (0, 255, 0), 3)
                cv2.putText(result_frame, f"{color} {radius}", (center[0]-radius, center[1]-radius-5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
    
    # Détection de l'ArUco
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_50)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
    
    corners, ids, rejected = detector.detectMarkers(frame)
    
    if ids is not None:
        for i in range(len(ids)):
            if ids[i] == 10:
                cv2.aruco.drawDetectedMarkers(result_frame, [corners[i]], np.array([ids[i]]))
                
                center = corners[i][0].mean(axis=0)
                center = tuple(map(int, center))
                
                detected_balls['aruco']['id10'] = {
                    'corners': corners[i][0].tolist(),
                    'center': center
                }
                
                cv2.putText(result_frame, f"ArUco ID:10", (center[0]-20, center[1]-20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                
                # Trouver la balle la plus proche
                ball_type, ball_info, distance = find_nearest_ball(
                    center, 
                    detected_balls
                )
                
                # Afficher les informations de distance
                if ball_info is not None:
                    display_distance_info(
                        result_frame, 
                        center, 
                        ball_type, 
                        ball_info, 
                        distance
                    )
    
    return result_frame, detected_balls

def incomingFrame(frame, iframe, frame_id):
    """
    Traite une nouvelle frame reçue du flux vidéo.
    """
    analyzed_frame, balls_data = analysis(frame)
    iframe.mat = analyzed_frame
    iframe.analysis_result = balls_data
    iframe.id = frame_id