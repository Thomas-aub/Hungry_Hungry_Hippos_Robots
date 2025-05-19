import cv2
from cv2 import aruco

print("cv2 version:", cv2.__version__)
print("aruco module present:", hasattr(aruco, "drawMarker"))
