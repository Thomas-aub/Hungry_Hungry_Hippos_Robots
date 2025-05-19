# Python + OpenCV

# Exemple de code pour détecter l’ID d’un marqueur
import cv2
aruco_dict = cv2.aruco.Dictionary(cv2.aruco.DICT_4X4_50)
parameters = cv2.aruco.DetectorParameters_create()
frame = cv2.imread("aruco1.jpeg")
corners, ids, _ = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=parameters)
print("IDs détectés :", ids)