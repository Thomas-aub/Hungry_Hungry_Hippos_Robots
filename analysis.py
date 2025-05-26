"""
analysis.py — Computer‑vision utilities for the EV3 ball‑fetch project.

Updated using the improved detection logic provided by the user.
Modular and easily integrable with movement logic.
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
# Data structures
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
    aruco: Optional[ArucoMarker]
    target: Optional[TargetInfo]
    annotated: Optional[np.ndarray] = None

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
_COLOR_THRESHOLDS = {
    'red': [
        {'lower': np.array([0, 120, 70]), 'upper': np.array([30, 255, 255])},
    ],
    'blue': [
        {'lower': np.array([100, 50, 40]), 'upper': np.array([240, 255, 255])}
    ]
}

_ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_50)
_ARUCO_ID = 71 # 72, 73, 74
_KERNEL = np.ones((5, 5), np.uint8)

# ---------------------------------------------------------------------------
# Core detection and analysis logic
# ---------------------------------------------------------------------------

def _equalize_value_channel(hsv):
    hsv = hsv.copy()
    hsv[:,:,2] = cv2.equalizeHist(hsv[:,:,2])
    return hsv

def _create_mask(hsv, color: str) -> np.ndarray:
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
    hsv[:,:,2] = cv2.equalizeHist(hsv[:,:,2])
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

def detect_aruco(frame: np.ndarray) -> Optional[ArucoMarker]:
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(_ARUCO_DICT, parameters)
    corners, ids, _ = detector.detectMarkers(frame)
    if ids is not None:
        for i, marker_id in enumerate(ids):
            if marker_id == _ARUCO_ID:
                center = corners[i][0].mean(axis=0)
                center = tuple(map(int, center))
                return ArucoMarker(int(marker_id), center)
    return None

def euclidean(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def compute_direction(origin: Tuple[int, int], target: Tuple[int, int]) -> float:
    dx = target[0] - origin[0]
    dy = origin[1] - target[1]  # image y-axis goes down
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
# Visualization and final wrapper
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

    if result.aruco:
        center = result.aruco.center
        cv2.putText(img, f"ArUco ID:{_ARUCO_ID}", (center[0]-20, center[1]-20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        cv2.circle(img, center, 4, (0, 255, 255), -1)

    if result.target:
        ac = result.aruco.center
        bc = (result.target.ball.x, result.target.ball.y)
        cv2.line(img, ac, bc, (0, 255, 255), 2)
        mid = ((ac[0] + bc[0]) // 2, (ac[1] + bc[1]) // 2)
        text = f"Dist: {result.target.distance_px:.1f}px | Angle: {result.target.direction_deg:.1f}°"
        cv2.putText(img, text, (mid[0]-40, mid[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    return img

def _save_detected_frame(frame: np.ndarray, folder: str = "detections") -> None:
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{folder}/frame_{timestamp}.png"
    cv2.imwrite(filename, frame)
    print(f"Frame enregistrée: {filename}")

def analyze_frame(frame: np.ndarray, *, with_annotations: bool = True, save_detections: bool = False) -> AnalysisResult:
    balls = detect_balls(frame)
    aruco = detect_aruco(frame)
    target = find_nearest_ball(aruco.center, balls) if aruco else None

    result = AnalysisResult(balls=balls, aruco=aruco, target=target)

    if with_annotations:
        result.annotated = _draw_annotations(frame, result)
    if save_detections and result.annotated is not None:
        _save_detected_frame(result.annotated)

    return result