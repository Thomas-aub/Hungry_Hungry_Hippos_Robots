import cv2
import numpy as np

pts_img = np.array([[255, 510], [250, 207], [553, 520], [554, 220]], dtype=np.float32)

ptsreal = np.array([[247, 451], [291, 250], [512, 455], [515, 457]], dtype=np.float32)

H  = cv2.findHomography(pts_img, ptsreal)
def transform_point(pt):
    print(pt)
    p = np.array([pt[0], pt[1], 1.0])
    p_trans = H @ p
    return (p_trans[0] / p_trans[2], p_trans[1] / p_trans[2])