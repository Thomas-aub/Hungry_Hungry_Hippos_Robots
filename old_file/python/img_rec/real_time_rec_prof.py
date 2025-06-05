import sys
import os

absolute_path = os.path.dirname(__file__)
# Modules imports
relative_path = "../../Idefix/python/modules"
full_path = os.path.join(absolute_path, relative_path)
sys.path.append(full_path)

import argparse
import cv2
import numpy as np

from networking import TCPClientAbstraction, DisconnectedException
from encoding import Packer

# Tools imports
relative_path_tools = "../../Idefix/python/tools"
full_path = os.path.join(absolute_path, relative_path_tools)
sys.path.append(full_path)

from jpeg_traits import JpegImage

# Go back to normal path, for loading files
standard_path_tools = "../../../python/img_rec"
full_path = os.path.join(absolute_path, standard_path_tools)
sys.path.append(full_path)

class Client(TCPClientAbstraction):
    def __init__(self):
        super().__init__(2048)
        self.size = None
        self.frame = None
    def incomingMessage(self,buffer):
        if buffer is None:
            self.stop()
            return
        if buffer.length == 0:
            self.stop()
            return
        index, self.frame = Packer.unpack(buffer.buffer,0)
    def start(self,args):
        self.initialize(args.server,args.port)
        buffer = self.receive()
        if buffer is None:
            self.finalize()
            return
        if buffer.length == 0:
            self.finalize()
            return
        index, size = Packer.unpack(buffer.buffer, 0)
        print(size)
        self.passiveReceive(self.incomingMessage)
    def stop(self):
        self.finalize()

def rotate_poly(points, center, angle):
    # Define the angle of rotation in radians
    angle = np.radians(45)  # Rotate the polyline by 45 degrees

    # Subtract the center coordinates from the points to translate the polyline to the origin
    points_centered = points - center

    # Create the rotation matrix
    rotation_matrix = np.array(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]
    )

    # Rotate the points
    rotated_points = np.dot(points_centered, rotation_matrix.T)

    # Add the center coordinates to the points to translate the polyline back to the center
    rotated_points = rotated_points + center
    return rotated_points

def display_id_ico(image, points):
    for i, point in enumerate(points):
        # Define the position for the text
        # We offset the text by -10 in the y direction for better visibility
        pos = (point[0][0], point[0][1] - 10)

        # Define the font
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Define the scale (size) of the text
        scale = 0.5

        # Define the color of the text (BGR)
        color = (255, 255, 255)

        # Define the thickness of the text
        thickness = 1

        # Put the text on the image
        cv2.putText(image, str(i), pos, font, scale, color, thickness)

def display_id_sq(image, points):
    for i, point in enumerate(points):
        # Define the position for the text
        # We offset the text by -10 in the y direction for better visibility
        pos = (point[0], point[1] - 10)

        # Define the font
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Define the scale (size) of the text
        scale = 0.5

        # Define the color of the text (BGR)
        color = (255, 255, 255)

        # Define the thickness of the text
        thickness = 1

        # Put the text on the image
        cv2.putText(image, str(i), pos, font, scale, color, thickness)


def theoretical_arena():
    # height, width = 1000, 1000
    # height, width = 500, 500
    height, width = 2000, 2000
    image = np.zeros((height, width, 3), np.uint8)

    # Define the center
    center_coordinates = (height // 2, width // 2)
    # Draw a dot at the center
    cv2.circle(image, center_coordinates, radius=1, color=(0, 255, 0), thickness=2)

    # SQUARE : 2 m eachside
    # Define the side of the square
    side = 200
    # Define the top left and bottom right coordinates of the square
    top_left = (center_coordinates[0] - side // 2, center_coordinates[1] - side // 2)
    bottom_right = (
        center_coordinates[0] + side // 2,
        center_coordinates[1] + side // 2,
    )
    cv2.rectangle(image, top_left, bottom_right, (255, 0, 0), 1)
    corners = [
        top_left,
        (bottom_right[0], top_left[1]),
        bottom_right,
        (top_left[0], bottom_right[1]),
    ]
    display_id_sq(image, corners)

    # ICOSACOSAGONE : 70 cm eachside, 2.24m diameter
    # Define the diameter
    diameter = 448

    # Define the number of sides of the polygon
    num_sides = 20

    # Define the radius
    radius = diameter / 2

    # Define the points of the polygon
    points = np.array(
        [
            [
                int(center_coordinates[0] + radius * np.cos(2 * np.pi * i / num_sides)),
                int(center_coordinates[1] + radius * np.sin(2 * np.pi * i / num_sides)),
            ]
            for i in range(num_sides)
        ],
        np.int32,
    )
    points_rotated = rotate_poly(points, center_coordinates, 45)

    # Reshape the points array
    points_rotated = points_rotated.reshape((-1, 1, 2)).astype(np.int32)
    display_id_ico(image, points_rotated)

    # Draw the polygon
    cv2.polylines(
        image, [points_rotated], isClosed=True, color=(255, 0, 0), thickness=1
    )

    # cv2.imshow('Image', image)
    # cv2.waitKey(0)
    # v2.destroyAllWindows()

    return image


def click_event(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"{param} Window, Coordinates: ({x}, {y})")


def corres_finder(position, src, dest):
    # Order to click on stuff : center, square left, square right,
    #
    cv2.imshow((position + "src"), src)
    cv2.imshow("dest", dest)

    cv2.setMouseCallback((position + "src"), click_event, param="src")
    cv2.setMouseCallback("dest", click_event, param="dest")

    cv2.waitKey(0)
    cv2.destroyAllWindows()

def assign_load(file_mat):
    #     pour chaque ligne, il y a : xi yi Xi Yi
    # - (xi,yi) coordonnées du point dans l'arene (dest)
    # - (Xi,Yi) coordonnées du point correspondant dans la vignette (src)
    # remove out lines with 0 from file_mat
    epsilon = 1e-8
    file_mat = file_mat[~np.any(np.abs(file_mat) < epsilon, axis=1)]

    print(len(file_mat))

    dest = file_mat[:, :2]
    src = file_mat[:, 2:]
    return src, dest


def processing(frame):
    # Here cv2 image frame is available for processing
    height, width, _ = frame.shape
    # Divide the frame into 4 equal parts
    # For each, fix points to get the perspective transform
    # Apply transform and get 4 img result
    # Merge them ?

    arena = theoretical_arena()
    h, w = arena.shape[:2]

    # south one from entry of room
    # NEW WEST
    top_left = frame[0 : height // 2, 0 : width // 2]
    tl_src = np.float32()
    tl_dest = np.float32()
    tl_load = np.loadtxt(absolute_path + '/corres/vertices-norm-0001.txt')
    tl_src, tl_dest = assign_load(tl_load)
    # Multiply absolute coordinates by relative
    tl_src[:, 0] *= width // 2
    tl_src[:, 1] *= height // 2
    tl_dest[:, 0] *= w
    tl_dest[:, 1] *= h
    

    M_tl, _ = cv2.findHomography(tl_src, tl_dest)
    dst_tl = cv2.warpPerspective(top_left, M_tl, (h, w))
    cv2.imshow("dst_tl", dst_tl)

    # west
    top_right = frame[0 : height // 2, width // 2 :]
    tr_src = np.float32()
    tr_dest = np.float32()
    tr_load = np.loadtxt(absolute_path + '/corres/vertices-norm-0002.txt')
    tr_src, tr_dest = assign_load(tr_load)
    tr_src[:, 0] *= width // 2
    tr_src[:, 1] *= height // 2
    tr_dest[:, 0] *= w
    tr_dest[:, 1] *= h

    M_tr, _ = cv2.findHomography(tr_src, tr_dest)
    dst_tr = cv2.warpPerspective(top_right, M_tr, (h, w))
    cv2.imshow("dst_tr", dst_tr)

    # east
    bot_left = frame[height // 2 :, 0 : width // 2]
    bl_src = np.float32()
    bl_dest = np.float32()
    bl_load = np.loadtxt(absolute_path + '/corres/vertices-norm-0003.txt')
    bl_src, bl_dest = assign_load(bl_load)
    bl_src[:, 0] *= width // 2
    bl_src[:, 1] *= height // 2
    bl_dest[:, 0] *= w
    bl_dest[:, 1] *= h

    M_bl, _ = cv2.findHomography(bl_src, bl_dest)
    dst_bl = cv2.warpPerspective(bot_left, M_bl, (h, w))
    cv2.imshow("dst_bl", dst_bl)

    # north
    bot_right = frame[height // 2 :, width // 2 :]
    br_src = np.float32()
    br_dest = np.float32()
    br_load = np.loadtxt(absolute_path + '/corres/vertices-norm-0000.txt')
    br_src, br_dest = assign_load(br_load)
    br_src[:, 0] *= width // 2
    br_src[:, 1] *= height // 2
    br_dest[:, 0] *= w
    br_dest[:, 1] *= h

    M_br, _ = cv2.findHomography(br_src, br_dest)
    dst_br = cv2.warpPerspective(src=bot_right, M=M_br, dsize=(h, w))
    cv2.imshow("dst_br", dst_br)

    dest_images = [dst_tl, dst_tr, dst_bl, dst_br]

    superposed_pixels = np.zeros_like(dest_images[0])
    # Iterate over the images in dest_images
    for img in dest_images:
        # Create a binary mask for the current image
        mask = np.sum(img > 0, axis=2, dtype=np.uint8)
        # For adding with the superposed pixels
        mask = mask[:, :, np.newaxis]
        # Add the mask to the count of superposed pixels
        superposed_pixels+=mask

    avg_img = np.sum(dest_images, axis=0, dtype=np.float64)
    avg_img /= (superposed_pixels + 1e-10)
    # Normalize the image
    avg_img = ((avg_img - np.min(avg_img)) / (np.max(avg_img) - np.min(avg_img))) * 255

    avg_img = avg_img.astype(np.uint8)

    # cv2.imshow("Average", avg_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    return avg_img


millisecondsToWait = 1000 // 30

if __name__ == "__main__":
    client = Client()
    parser = argparse.ArgumentParser()
    # Replace server address by 192.168.1.134 to get real server address
    parser.add_argument(
        "-s",
        "--server",
        action="store",
        # default="127.0.0.1", # mock server
        default="192.168.1.134", # Real server address
        type=str,
        help="address of server to connect",
    )
    parser.add_argument(
        "-p", "--port", action="store", default=2120, type=int, help="port on server"
    )
    args = parser.parse_args()
    try:
        client.start(args)
        while client.connected:
            if client.frame is not None:
                cv2.imshow("test", client.frame)
                processed = processing(client.frame)
                cv2.imshow("computed", processed)
                # Here cv2 image frame is available for processing
            key = cv2.waitKey(millisecondsToWait) & 0x0FF
            if key == ord("q"):
                break
        client.stop()
    except DisconnectedException:
        print("Plantage du serveur et/ou de la connexion")
        client.stop()

    # Here cv2 image frame is available for processing
