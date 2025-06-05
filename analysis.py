"""
analysis.py — Computer-vision utilities for the EV3 ball-fetch project.

Detects red and blue balls, and two ArUco markers (Gabriel and Isis).
Computes direction and distance to the nearest ball from each marker.
Arena filtering is done using polygonal shapes instead of circles to better handle camera perspective distortions.
Includes line-of-sight checking to avoid targeting balls blocked by arena boundaries.
"""

from __future__ import annotations

import cv2
import numpy as np
import os
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Arena Configuration - polygons instead of circles
# ---------------------------------------------------------------------------

# Define your arena polygons here: each polygon is an np.array of (x, y) points.
# Modify these points to fit the actual shape of your arena on the frame.
ARENA_POLYGONS = [
    np.array([(640, 360), (250, 360), (155, 306), (129, 262), (122, 203), (139, 153), (169,111), (209,78), (259,57), (314,42), (372,35), (427,35), (487,44), (547,65), (590,89), (635,125)], np.int32),  # Polygon 1 - example points
    np.array([(610,720), (85,720), (62,697), (49,669), (43,594), (65,529), (101,479), (151,436), (209,408), (271,390), (333,378), (397,379), (461,384), (527,406), (594,439), (640,477), (640,720)], np.int32),              # Polygon 2 - example points
]

# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Ball:
    x: int
    y: int
    r: int
    color: str

@dataclass(frozen=True)
class ArucoMarker:
    marker_id: int
    center: Tuple[int, int]

@dataclass(frozen=True)
class TargetInfo:
    color: str
    ball: Ball
    distance_px: float
    direction_deg: float

@dataclass
class AnalysisResult:
    balls: Dict[str, List[Ball]]
    aruco_gabriel: Optional[ArucoMarker]
    aruco_isis: Optional[ArucoMarker]
    target_gabriel: Optional[TargetInfo]
    target_isis: Optional[TargetInfo]
    annotated: Optional[np.ndarray] = None

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

_COLOR_THRESHOLDS = {
    'red': [{'lower': np.array([0, 30, 70]), 'upper': np.array([30, 255, 255])}],
    'blue': [{'lower': np.array([80, 50, 5]), 'upper': np.array([230, 255, 250])}]
}

_ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_1000)
_ARUCO_ID_GABRIEL = 71
_ARUCO_ID_ISIS = 74
_KERNEL = np.ones((5, 5), np.uint8)

# ---------------------------------------------------------------------------
# Arena Filtering (Polygon version)
# ---------------------------------------------------------------------------

def create_arena_mask(frame_shape: Tuple[int, int]) -> np.ndarray:
    """
    Creates a binary mask where pixels inside the arena polygons are white (255)
    and pixels outside are black (0).
    
    Args:
        frame_shape: (height, width) of the frame
    
    Returns:
        Binary mask with same dimensions as frame
    """
    height, width = frame_shape
    mask = np.zeros((height, width), dtype=np.uint8)
    
    # Draw filled polygons on the mask
    for polygon in ARENA_POLYGONS:
        cv2.fillPoly(mask, [polygon], 255)
    
    return mask

def apply_arena_filter(frame: np.ndarray) -> np.ndarray:
    """
    Applies arena filter to frame, setting pixels outside arena polygons to black.
    
    Args:
        frame: Input BGR frame
    
    Returns:
        Filtered frame with arena regions preserved, rest blackened
    """
    mask = create_arena_mask(frame.shape[:2])
    
    # Create 3-channel mask for BGR image
    mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    
    # Apply mask: keep arena pixels, set others to black
    filtered_frame = cv2.bitwise_and(frame, mask_3ch)
    
    return filtered_frame

# ---------------------------------------------------------------------------
# Line-of-sight checking
# ---------------------------------------------------------------------------

def has_line_of_sight(frame: np.ndarray, start: Tuple[int, int], end: Tuple[int, int], 
                      sample_points: int = 50) -> bool:
    """
    Check if there's a clear line of sight between two points by sampling points along the line
    and verifying none of them are black pixels (0,0,0).
    
    Args:
        frame: BGR image to check
        start: Starting point (x, y)
        end: Ending point (x, y)
        sample_points: Number of points to sample along the line
    
    Returns:
        True if line of sight is clear, False if blocked by black pixels
    """
    x1, y1 = start
    x2, y2 = end
    
    # Generate points along the line using linear interpolation
    for i in range(sample_points + 1):
        t = i / sample_points
        x = int(x1 + t * (x2 - x1))
        y = int(y1 + t * (y2 - y1))
        
        # Check bounds
        if 0 <= y < frame.shape[0] and 0 <= x < frame.shape[1]:
            # Check if pixel is black (0,0,0)
            pixel = frame[y, x]
            if np.array_equal(pixel, [0, 0, 0]):
                return False
        else:
            # Point is out of bounds, consider it blocked
            return False
    
    return True

# ---------------------------------------------------------------------------
# Detection Logic
# ---------------------------------------------------------------------------

def _create_mask(hsv: np.ndarray, color: str) -> np.ndarray:
    combined_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for threshold in _COLOR_THRESHOLDS[color]:
        mask = cv2.inRange(hsv, threshold['lower'], threshold['upper'])
        combined_mask = cv2.bitwise_or(combined_mask, mask)
    return combined_mask

def _postprocess_mask(mask: np.ndarray) -> np.ndarray:
    cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, _KERNEL)
    return cv2.dilate(cleaned, _KERNEL, iterations=2)

def detect_balls(frame: np.ndarray) -> Dict[str, List[Ball]]:
    """
    Detects red and blue balls in the given frame.
    
    Args:
        frame: BGR image
    
    Returns:
        Dictionary with keys 'red' and 'blue' mapping to lists of detected Ball objects
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv[:, :, 2] = cv2.equalizeHist(hsv[:, :, 2])  # Equalize brightness channel for better detection
    detected: Dict[str, List[Ball]] = {"red": [], "blue": []}

    for color in detected:
        mask = _create_mask(hsv, color)
        mask = _postprocess_mask(mask)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 30:
                continue  # Ignore very small contours (noise)
            
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 50 or h > 50:
                continue  # Ignore very large contours (likely not balls)
            
            perimeter = cv2.arcLength(cnt, True)
            circularity = 4 * np.pi * area / (perimeter**2) if perimeter > 0 else 0
            if circularity < 0.5:
                continue  # Ignore contours that are not circular enough
            
            (cx, cy), radius = cv2.minEnclosingCircle(cnt)
            if 3 <= radius <= 25:
                detected[color].append(Ball(int(cx), int(cy), int(radius), color))
    
    return detected

def detect_arucos(frame: np.ndarray) -> Tuple[Optional[ArucoMarker], Optional[ArucoMarker]]:
    """
    Detects ArUco markers Gabriel and Isis in the frame.
    
    Args:
        frame: BGR image
    
    Returns:
        Tuple with ArucoMarker for Gabriel and Isis respectively (or None if not found)
    """
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(_ARUCO_DICT, parameters)
    corners, ids, _ = detector.detectMarkers(frame)

    marker_gabriel = None
    marker_isis = None

    if ids is not None:
        ids = ids.flatten()
        for i, marker_id in enumerate(ids):
            center = corners[i][0].mean(axis=0)
            center = tuple(map(int, center))
            if marker_id == _ARUCO_ID_GABRIEL:
                marker_gabriel = ArucoMarker(int(marker_id), center)
            elif marker_id == _ARUCO_ID_ISIS:
                marker_isis = ArucoMarker(int(marker_id), center)

    return marker_gabriel, marker_isis

# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def euclidean(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
    """Calculate Euclidean distance between two points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def compute_direction(origin: Tuple[int, int], target: Tuple[int, int]) -> float:
    """
    Compute direction angle (degrees) from origin to target.
    Angle is measured clockwise from the positive X-axis.
    
    Args:
        origin: (x, y) coordinates of origin
        target: (x, y) coordinates of target
    
    Returns:
        Angle in degrees [0, 360)
    """
    dx = target[0] - origin[0]
    dy = origin[1] - target[1]
    angle = math.degrees(math.atan2(dy, dx))
    return (angle + 360) % 360

def find_nearest_ball_with_line_of_sight(aruco_center: Tuple[int, int], balls: Dict[str, List[Ball]], 
                                        frame: np.ndarray) -> Optional[TargetInfo]:
    """
    Find the nearest detected ball from an ArUco marker center that has a clear line of sight
    (no black pixels blocking the path).
    
    Args:
        aruco_center: (x, y) coordinates of the ArUco marker
        balls: Dictionary of detected balls
        frame: BGR image to check for line of sight
    
    Returns:
        TargetInfo of the nearest accessible ball, or None if no balls are accessible
    """
    nearest = None
    min_dist = float('inf')
    
    for color, blist in balls.items():
        for b in blist:
            ball_center = (b.x, b.y)
            
            # Check if there's a clear line of sight
            if has_line_of_sight(frame, aruco_center, ball_center):
                d = euclidean(aruco_center, ball_center)
                if d < min_dist:
                    min_dist = d
                    direction = compute_direction(aruco_center, ball_center)
                    nearest = TargetInfo(color=color, ball=b, distance_px=d, direction_deg=direction)
    
    return nearest

def find_nearest_ball(aruco_center: Tuple[int, int], balls: Dict[str, List[Ball]]) -> Optional[TargetInfo]:
    """
    Find the nearest detected ball from an ArUco marker center (legacy function without line-of-sight check),
    with vertical boundary at y=368. Only considers balls on the same side of the line as the marker.
    
    Args:
        aruco_center: (x, y) coordinates of the ArUco marker
        balls: Dictionary of detected balls
    
    Returns:
        TargetInfo of the nearest ball, or None if no valid balls are found
    """
    nearest = None
    min_dist = float('inf')
    marker_y = aruco_center[1]

    for color, blist in balls.items():
        for b in blist:
            # Only consider balls on the same vertical side as the marker
            if (marker_y < 368 and b.y < 368) or (marker_y >= 368 and b.y >= 368):
                d = euclidean(aruco_center, (b.x, b.y))
                if d < min_dist:
                    min_dist = d
                    direction = compute_direction(aruco_center, (b.x, b.y))
                    nearest = TargetInfo(color=color, ball=b, distance_px=d, direction_deg=direction)

    return nearest

# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------

def _draw_annotations(frame: np.ndarray, result: AnalysisResult) -> np.ndarray:
    """
    Draws annotations on the frame for balls, ArUco markers, targets, and arena polygons.
    
    Args:
        frame: BGR image
        result: AnalysisResult containing detection info
    
    Returns:
        Annotated image copy
    """
    img = frame.copy()
    
    # Draw arena polygons for reference (optional)
    for polygon in ARENA_POLYGONS:
        cv2.polylines(img, [polygon], isClosed=True, color=(128, 128, 128), thickness=2)
    
    # Draw detected balls
    for blist in result.balls.values():
        for b in blist:
            col = (0, 0, 255) if b.color == "red" else (255, 0, 0)
            cv2.circle(img, (b.x, b.y), b.r, col, 2)
            cv2.circle(img, (b.x, b.y), 2, (0, 255, 0), 3)
            cv2.putText(img, f"{b.color} {b.r}", (b.x - b.r, b.y - b.r - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Draw ArUco markers
    if result.aruco_gabriel:
        center = result.aruco_gabriel.center
        cv2.putText(img, f"Gabriel ({result.aruco_gabriel.marker_id})", (center[0]-20, center[1]-20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        cv2.circle(img, center, 8, (0, 255, 255), 2)

    if result.aruco_isis:
        center = result.aruco_isis.center
        cv2.putText(img, f"Isis ({result.aruco_isis.marker_id})", (center[0]-20, center[1]-20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        cv2.circle(img, center, 8, (255, 255, 0), 2)

    # Draw lines to nearest balls
    if result.target_gabriel and result.aruco_gabriel:
        ac = result.aruco_gabriel.center
        bc = (result.target_gabriel.ball.x, result.target_gabriel.ball.y)
        cv2.line(img, ac, bc, (0, 255, 255), 2)
        text = f"G → {result.target_gabriel.color} | {result.target_gabriel.distance_px:.0f}px | {result.target_gabriel.direction_deg:.1f}°"
        mid = ((ac[0] + bc[0]) // 2, (ac[1] + bc[1]) // 2)
        cv2.putText(img, text, mid, cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 2)

    if result.target_isis and result.aruco_isis:
        ac = result.aruco_isis.center
        bc = (result.target_isis.ball.x, result.target_isis.ball.y)
        cv2.line(img, ac, bc, (255, 255, 0), 2)
        text = f"I → {result.target_isis.color} | {result.target_isis.distance_px:.0f}px | {result.target_isis.direction_deg:.1f}°"
        mid = ((ac[0] + bc[0]) // 2, (ac[1] + bc[1]) // 2)
        cv2.putText(img, text, mid, cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 2)

    return img

# ---------------------------------------------------------------------------
# Analysis Pipeline
# ---------------------------------------------------------------------------

def _save_detected_frame(frame: np.ndarray, folder: str = "detections") -> None:
    """
    Saves annotated frame to disk with timestamp.
    
    Args:
        frame: Image to save
        folder: Folder to save images
    """
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{folder}/frame_{timestamp}.png"
    cv2.imwrite(filename, frame)
    print(f"Frame saved: {filename}")

def analyze_frame(frame: np.ndarray, *, with_annotations: bool = True, save_detections: bool = False, 
                 use_arena_filter: bool = True, use_line_of_sight: bool = True) -> AnalysisResult:
    """
    Performs the full analysis pipeline on a frame:
    - Applies arena filter (polygon masking)
    - Detects balls and ArUco markers
    - Finds nearest ball from each marker (with optional line-of-sight checking)
    - Annotates results if requested
    
    Args:
        frame: Input BGR image
        with_annotations: Whether to draw and return annotated image
        save_detections: Whether to save annotated images to disk
        use_arena_filter: Whether to apply arena polygon masking
        use_line_of_sight: Whether to check for clear line of sight when finding nearest balls
    
    Returns:
        AnalysisResult containing all detections and optional annotated image
    """
    # Keep original frame for line-of-sight checking
    original_frame = frame.copy()
    
    # Apply arena filter first if enabled
    if use_arena_filter:
        frame = apply_arena_filter(frame)
    
    balls = detect_balls(frame)
    aruco_gabriel, aruco_isis = detect_arucos(frame)
    
    
    
    target_gabriel = find_nearest_ball(aruco_gabriel.center, balls) if aruco_gabriel else None
    target_isis = find_nearest_ball(aruco_isis.center, balls) if aruco_isis else None

    result = AnalysisResult(
        balls=balls,
        aruco_gabriel=aruco_gabriel,
        aruco_isis=aruco_isis,
        target_gabriel=target_gabriel,
        target_isis=target_isis
    )

    if with_annotations:
        result.annotated = _draw_annotations(frame, result)
    if save_detections and result.annotated is not None:
        _save_detected_frame(result.annotated)

    return result