"""
analysis.py — Computer-vision utilities for the EV3 ball-fetch project.

Detects red and blue balls, and two ArUco markers (Gabriel and Isis).
Computes direction and distance to the nearest ball from each marker.
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
    'red': [{'lower': np.array([0, 120, 70]), 'upper': np.array([30, 255, 255])}],
    'blue': [{'lower': np.array([100, 50, 40]), 'upper': np.array([240, 255, 255])}]
}

_ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_1000)
_ARUCO_ID_GABRIEL = 71
_ARUCO_ID_ISIS = 74
_KERNEL = np.ones((5, 5), np.uint8)

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
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv[:, :, 2] = cv2.equalizeHist(hsv[:, :, 2])
    detected: Dict[str, List[Ball]] = {"red": [], "blue": []}

    for color in detected:
        mask = _create_mask(hsv, color)
        mask = _postprocess_mask(mask)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 30:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 50 or h > 50:
                continue
            perimeter = cv2.arcLength(cnt, True)
            circularity = 4 * np.pi * area / (perimeter**2) if perimeter > 0 else 0
            if circularity < 0.5:
                continue
            (cx, cy), radius = cv2.minEnclosingCircle(cnt)
            if 3 <= radius <= 25:
                detected[color].append(Ball(int(cx), int(cy), int(radius), color))
    return detected

def detect_arucos(frame: np.ndarray) -> Tuple[Optional[ArucoMarker], Optional[ArucoMarker]]:
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(_ARUCO_DICT, parameters)
    corners, ids, _ = detector.detectMarkers(frame)

    marker_gabriel = None
    marker_isis = None

    print(ids)
    if ids is not None:
        ids = ids.flatten()
        for i, marker_id in enumerate(ids):
            center = corners[i][0].mean(axis=0)
            center = tuple(map(int, center))
            if marker_id == _ARUCO_ID_GABRIEL:
                marker_gabriel = ArucoMarker(int(marker_id), center)
            elif marker_id == _ARUCO_ID_ISIS:
                marker_isis = ArucoMarker(int(marker_id), center)
    print("Gabriel :", marker_gabriel)
    print("Isis :", marker_isis)
    return marker_gabriel, marker_isis

# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def euclidean(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def compute_direction(origin: Tuple[int, int], target: Tuple[int, int]) -> float:
    dx = target[0] - origin[0]
    dy = origin[1] - target[1]
    angle = math.degrees(math.atan2(dy, dx))
    return (angle + 360) % 360

def find_nearest_ball(aruco_center: Tuple[int, int], balls: Dict[str, List[Ball]]) -> Optional[TargetInfo]:
    nearest = None
    min_dist = float('inf')
    for color, blist in balls.items():
        for b in blist:
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
    img = frame.copy()
    for blist in result.balls.values():
        for b in blist:
            col = (0, 0, 255) if b.color == "red" else (255, 0, 0)
            cv2.circle(img, (b.x, b.y), b.r, col, 2)
            cv2.circle(img, (b.x, b.y), 2, (0, 255, 0), 3)
            cv2.putText(img, f"{b.color} {b.r}", (b.x - b.r, b.y - b.r - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

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
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{folder}/frame_{timestamp}.png"
    cv2.imwrite(filename, frame)
    print(f"Frame saved: {filename}")

def analyze_frame(frame: np.ndarray, *, with_annotations: bool = True, save_detections: bool = False) -> AnalysisResult:
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
