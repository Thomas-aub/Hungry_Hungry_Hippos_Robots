import numpy as np
import math

def calculate_qr_orientation(qr_points):
    """
    Calcule l'orientation du QR code par rapport à l'image.
    
    Args:
        qr_points: Points du QR code (4 points, dans l'ordre suivant: 
                  haut-gauche, haut-droite, bas-droite, bas-gauche)
    
    Returns:
        angle: Angle en degrés (0 = vers la droite, 90 = vers le bas, etc.)
        direction_vector: Vecteur normalisé indiquant la direction du QR code
    """
    if qr_points is None or len(qr_points) < 4:
        return None, None
    
    try:
        # Les points du QR code sont généralement ordonnés comme:
        # 0: haut-gauche, 1: haut-droite, 2: bas-droite, 3: bas-gauche
        top_left = qr_points[0][0]
        top_right = qr_points[0][1]
        
        # Calculer le vecteur de direction (de haut-gauche à haut-droite)
        direction_vector = np.array([top_right[0] - top_left[0], top_right[1] - top_left[1]])
        
        # Normaliser le vecteur
        magnitude = np.linalg.norm(direction_vector)
        if magnitude == 0:
            return 0, np.array([1, 0])  # Direction par défaut si le vecteur est nul
        
        normalized_vector = direction_vector / magnitude
        
        # Calculer l'angle (en radians puis en degrés)
        angle_rad = math.atan2(normalized_vector[1], normalized_vector[0])
        angle_deg = math.degrees(angle_rad)
        
        # Normaliser l'angle entre 0 et 360
        if angle_deg < 0:
            angle_deg += 360
            
        return angle_deg, normalized_vector
    
    except Exception as e:
        print(f"Erreur lors du calcul de l'orientation du QR code: {e}")
        return 0, np.array([1, 0])

def find_nearest_ball(qr_center, blue_spheres, orange_spheres):
    """
    Trouve la balle la plus proche du QR code.
    
    Args:
        qr_center: Coordonnées (x, y) du centre du QR code
        blue_spheres: Liste de tuples (x, y, radius) pour les balles bleues
        orange_spheres: Liste de tuples (x, y, radius) pour les balles orange
    
    Returns:
        nearest_ball: Tuple (x, y, radius, color) de la balle la plus proche
        distance: Distance entre le QR code et cette balle
    """
    if qr_center is None:
        return None, float('inf')
    
    nearest_ball = None
    min_distance = float('inf')
    
    # Vérifier les balles bleues
    for ball in blue_spheres:
        x, y, radius = ball
        distance = math.sqrt((qr_center[0] - x)**2 + (qr_center[1] - y)**2)
        if distance < min_distance:
            min_distance = distance
            nearest_ball = (x, y, radius, 'blue')
    
    # Vérifier les balles orange
    for ball in orange_spheres:
        x, y, radius = ball
        distance = math.sqrt((qr_center[0] - x)**2 + (qr_center[1] - y)**2)
        if distance < min_distance:
            min_distance = distance
            nearest_ball = (x, y, radius, 'orange')
    
    return nearest_ball, min_distance

def calculate_angle_to_ball(qr_center, qr_orientation, ball_center):
    """
    Calcule l'écart d'angle nécessaire pour que le QR code soit face à la balle.
    
    Args:
        qr_center: Coordonnées (x, y) du centre du QR code
        qr_orientation: Angle actuel du QR code en degrés
        ball_center: Coordonnées (x, y) du centre de la balle
    
    Returns:
        angle_difference: Écart d'angle en degrés (positif = rotation horaire)
    """
    if qr_center is None or ball_center is None:
        return None
    
    # Vecteur du QR code vers la balle
    ball_vector = np.array([ball_center[0] - qr_center[0], ball_center[1] - qr_center[1]])
    
    # Calculer l'angle vers la balle
    angle_to_ball_rad = math.atan2(ball_vector[1], ball_vector[0])
    angle_to_ball_deg = math.degrees(angle_to_ball_rad)
    
    # Normaliser l'angle entre 0 et 360
    if angle_to_ball_deg < 0:
        angle_to_ball_deg += 360
    
    # Calculer la différence d'angle
    angle_diff = angle_to_ball_deg - qr_orientation
    
    # Normaliser la différence entre -180 et 180
    if angle_diff > 180:
        angle_diff -= 360
    elif angle_diff < -180:
        angle_diff += 360
    
    return angle_diff

def calculate_distance_to_ball(qr_center, ball_center, ball_radius):
    """
    Calcule la distance entre le QR code et la balle (en pixels et ajustée par le rayon).
    
    Args:
        qr_center: Coordonnées (x, y) du centre du QR code
        ball_center: Coordonnées (x, y) du centre de la balle
        ball_radius: Rayon de la balle en pixels
    
    Returns:
        pixel_distance: Distance en pixels
        adjusted_distance: Distance du bord du QR code au bord de la balle
    """
    if qr_center is None or ball_center is None:
        return None, None
    
    # Distance euclidienne entre les centres
    pixel_distance = math.sqrt((qr_center[0] - ball_center[0])**2 + (qr_center[1] - ball_center[1])**2)
    
    # Estimer la taille du QR code (on suppose un QR code carré)
    # Cette valeur pourrait être calculée plus précisément avec les points exacts du QR code
    qr_size_estimate = 40  # Valeur à ajuster selon la taille réelle
    
    # Distance ajustée (du bord du QR code au bord de la balle)
    adjusted_distance = pixel_distance - ball_radius - (qr_size_estimate / 2)
    adjusted_distance = max(0, adjusted_distance)  # Éviter les valeurs négatives
    
    return pixel_distance, adjusted_distance

def analyze_qr_ball_relation(qr_points, qr_center, blue_spheres, orange_spheres):
    """
    Analyse complète de la relation entre le QR code et les balles.
    Cette fonction peut être appelée depuis print_detections.
    
    Args:
        qr_points: Points du QR code
        qr_center: Centre du QR code (x, y)
        blue_spheres: Liste de tuples (x, y, radius) pour les balles bleues
        orange_spheres: Liste de tuples (x, y, radius) pour les balles orange
    
    Returns:
        Un dictionnaire contenant les résultats de l'analyse
    """
    results = {
        "qr_orientation": None,
        "nearest_ball": None,
        "angle_to_ball": None,
        "distance_to_ball": None,
        "adjusted_distance": None
    }
    
    # Vérifier si un QR code est détecté
    if qr_center is None or qr_points is None:
        return results
    
    # Calculer l'orientation du QR code
    orientation, direction_vector = calculate_qr_orientation(qr_points)
    results["qr_orientation"] = orientation
    
    # Trouver la balle la plus proche
    nearest_ball, distance = find_nearest_ball(qr_center, blue_spheres, orange_spheres)
    results["nearest_ball"] = nearest_ball
    
    # Si une balle est trouvée, calculer les autres métriques
    if nearest_ball:
        ball_x, ball_y, ball_radius, ball_color = nearest_ball
        
        # Calculer l'écart d'angle
        angle_diff = calculate_angle_to_ball(qr_center, orientation, (ball_x, ball_y))
        results["angle_to_ball"] = angle_diff
        
        # Calculer la distance
        pixel_dist, adj_dist = calculate_distance_to_ball(qr_center, (ball_x, ball_y), ball_radius)
        results["distance_to_ball"] = pixel_dist
        results["adjusted_distance"] = adj_dist
    
    return results

def print_geometric_analysis(qr_points, qr_center, blue_spheres, orange_spheres):
    """
    Fonction à appeler depuis print_detections pour afficher l'analyse géométrique.
    
    Args:
        qr_points: Points du QR code
        qr_center: Centre du QR code (x, y)
        blue_spheres: Liste de tuples (x, y, radius) pour les balles bleues
        orange_spheres: Liste de tuples (x, y, radius) pour les balles orange
    """
    # Obtenir les résultats de l'analyse
    results = analyze_qr_ball_relation(qr_points, qr_center, blue_spheres, orange_spheres)
    
    # Afficher les résultats
    print("\n--- Analyse Géométrique ---")
    
    if results["qr_orientation"] is not None:
        print(f"Orientation du QR code: {results['qr_orientation']:.2f}°")
    else:
        print("Orientation du QR code: Non détectée")
    
    if results["nearest_ball"]:
        ball_x, ball_y, ball_radius, ball_color = results["nearest_ball"]
        print(f"Balle la plus proche: {ball_color} à ({ball_x}, {ball_y})")
        print(f"Distance au centre: {results['distance_to_ball']:.2f} pixels")
        print(f"Distance bord à bord: {results['adjusted_distance']:.2f} pixels")
        print(f"Angle à tourner pour faire face: {results['angle_to_ball']:.2f}°")
    else:
        print("Aucune balle détectée")
    
    print("---------------------------\n")