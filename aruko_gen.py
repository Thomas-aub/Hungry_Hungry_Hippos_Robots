import cv2
import cv2.aruco as aruco

def detect_aruco_with_different_dictionaries(image_path):
    # Charger l'image
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Liste des dictionnaires ArUco à essayer
    aruco_dicts = [
        aruco.DICT_4X4_50,
        aruco.DICT_4X4_100,
        aruco.DICT_4X4_250,
        aruco.DICT_4X4_1000,
        aruco.DICT_5X5_50,
        aruco.DICT_5X5_100,
        aruco.DICT_5X5_250,
        aruco.DICT_5X5_1000,
        aruco.DICT_6X6_50,
        aruco.DICT_6X6_100,
        aruco.DICT_6X6_250,
        aruco.DICT_6X6_1000,
        aruco.DICT_7X7_50,
        aruco.DICT_7X7_100,
        aruco.DICT_7X7_250,
        aruco.DICT_7X7_1000,
        aruco.DICT_ARUCO_ORIGINAL
    ]

    # Initialiser le détecteur ArUco
    detector = aruco.ArucoDetector()

    # Essayer chaque dictionnaire
    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_50)
    detector.setDictionary(aruco_dict)

    # Détecter les marqueurs ArUco
    corners, ids, rejectedImgPoints = detector.detectMarkers(gray)

    print(f"Marqueurs détectés avec le dictionnaire : {ids.flatten()}")


# Chemin vers l'image
image_path = '/home/tom/Documents/Code/Hungry_Hungry_Hippos_Robots/unnamed.jpg'

# Appeler la fonction pour détecter les marqueurs ArUco
detect_aruco_with_different_dictionaries(image_path)
