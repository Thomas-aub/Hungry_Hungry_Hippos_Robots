"""
analysis.py — Computer‑vision utilities for the EV3 ball‑fetch project.

This module is *deliberately* broken into many small, composable helper
functions so that higher‑level code (e.g. `mouvement.py`) can cherry‑pick
exactly what it needs — especially **distance** and **direction** toward the
nearest ball.

Public API
----------
>>> balls = detect_balls(hsv_img)
>>> ar_marker = detect_aruco(bgr_img)
>>> target = find_nearest_ball(ar_marker.center, balls)
>>> direction = compute_direction(ar_marker.center, target.ball)

Or, in one call:
>>> result = analyze_frame(bgr_img)
>>> result.target.distance_px
>>> result.target.direction_deg

All geometric computations are done in pixel space.  Converting pixels to
centimetres is left to the `mouvement` layer (requires a calibration factor).
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Ball:
    x: int
    y: int
    r: int
    color: str  # e.g. "red", "blue"


@dataclass(frozen=True)
class ArucoMarker:
    marker_id: int
    center: Tuple[int, int]


@dataclass(frozen=True)
class TargetInfo:
    color: str
    ball: Ball
    distance_px: float      # Euclidean in pixels
    direction_deg: float    # 0° = +x axis (right); CCW positive


@dataclass
class AnalysisResult:
    balls: Dict[str, List[Ball]]          # keyed by color
    aruco: Optional[ArucoMarker]
    target: Optional[TargetInfo]          # Nearest ball — can be None
    annotated: Optional[np.ndarray] = None


# ---------------------------------------------------------------------------
# Colour definitions (HSV).  Feel free to tweak!
# ---------------------------------------------------------------------------
_COLOR_THRESHOLDS = {
    "red": [
        {"lower": np.array([0, 120, 70]), "upper": np.array([10, 255, 255])},
        {"lower": np.array([170, 120, 70]), "upper": np.array([180, 255, 255])},
    ],
    "blue": [
        {"lower": np.array([100,  50, 40]), "upper": np.array([140, 255, 255])},
    ],
}

_KERNEL = np.ones((5, 5), np.uint8)
_ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)


# ---------------------------------------------------------------------------
# Low‑level helpers
# ---------------------------------------------------------------------------

def _equalize_value_channel(hsv: np.ndarray) -> np.ndarray:
    hsv = hsv.copy()
    hsv[:, :, 2] = cv2.equalizeHist(hsv[:, :, 2])
    return hsv


def _mask_for_color(hsv: np.ndarray, color: str) -> np.ndarray:
    mask = np.zeros(hsv.shape[:2], np.uint8)
    for t in _COLOR_THRESHOLDS[color]:
        mask |= cv2.inRange(hsv, t["lower"], t["upper"])
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, _KERNEL)
    return cv2.dilate(mask, _KERNEL, iterations=2)


def _contours_to_balls(contours, color: str) -> List[Ball]:
    balls: List[Ball] = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 30:
            continue
        peri = cv2.arcLength(cnt, True)
        circ = 4 * np.pi * area / (peri * peri) if peri > 0 else 0
        if circ < 0.5:
            continue
        (x, y), r = cv2.minEnclosingCircle(cnt)
        if not (3 <= r <= 25):
            continue
        balls.append(Ball(int(x), int(y), int(r), color))
    return balls


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def detect_balls(hsv_img: np.ndarray) -> Dict[str, List[Ball]]:
    """Return a dict {color: [Ball, ...]} for all configured colours."""
    hsv = _equalize_value_channel(hsv_img)
    output: Dict[str, List[Ball]] = {}
    for color in _COLOR_THRESHOLDS:
        mask = _mask_for_color(hsv, color)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        output[color] = _contours_to_balls(contours, color)
    return output


def detect_aruco(bgr_img: np.ndarray) -> Optional[ArucoMarker]:
    """Detect the first ArUco marker found and return its centre (pixel coords)."""
    corners, ids, _ = cv2.aruco.detectMarkers(bgr_img, _ARUCO_DICT)
    if ids is None:
        return None
    idx = 0  # just take the first one for now
    c = corners[idx][0]
    center = tuple(map(int, c.mean(axis=0)))  # type: ignore[arg-type]
    return ArucoMarker(int(ids[idx][0]), center)


def euclidean(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def find_nearest_ball(
    aruco_center: Tuple[int, int],
    balls: Dict[str, List[Ball]],
) -> Optional[TargetInfo]:
    """Return the closest *single* ball to the ArUco centre (or None)."""
    nearest: Optional[TargetInfo] = None
    best_dist = float("inf")
    for color, blist in balls.items():
        for b in blist:
            d = euclidean(aruco_center, (b.x, b.y))
            if d < best_dist:
                best_dist = d
                direction = compute_direction(aruco_center, (b.x, b.y))
                nearest = TargetInfo(color, b, d, direction)
    return nearest


def compute_direction(
    origin: Tuple[int, int],
    target: Tuple[int, int],
) -> float:
    """Angle in **degrees** from +x axis (right) toward *target* (CCW positive).

    Note: Because image Y is downward, we flip the y‑component so that
    mathematically 0° is to the right and 90° is up.
    """
    dx = target[0] - origin[0]
    dy = origin[1] - target[1]  # invert Y
    angle_deg = (math.degrees(math.atan2(dy, dx)) + 360) % 360
    return angle_deg


# ---------------------------------------------------------------------------
# High‑level façade
# ---------------------------------------------------------------------------

def _draw_annotations(frame: np.ndarray, res: AnalysisResult) -> np.ndarray:
    img = frame.copy()

    # draw balls
    for blist in res.balls.values():
        for b in blist:
            col = (0, 0, 255) if b.color == "red" else (255, 0, 0)
            cv2.circle(img, (b.x, b.y), b.r, col, 2)

    # draw ArUco centre
    if res.aruco:
        cv2.circle(img, res.aruco.center, 4, (0, 255, 255), -1)

    # draw line to target ball
    if res.target:
        ac = res.aruco.center  # type: ignore[assignment]
        bc = (res.target.ball.x, res.target.ball.y)
        cv2.line(img, ac, bc, (0, 255, 255), 2)
        cv2.putText(
            img,
            f"{res.target.color}: {res.target.distance_px:.0f}px, {res.target.direction_deg:.1f}°",
            (ac[0] + 10, ac[1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1,
        )
    return img


def analyze_frame(
    bgr_img: np.ndarray,
    *,
    with_annotations: bool = True,
    save_detections: bool = False,
) -> AnalysisResult:
    """Full pipeline wrapper.

    Parameters
    ----------
    bgr_img : np.ndarray
        Raw frame from the camera (BGR).
    with_annotations : bool, default True
        If *True*, an annotated copy of the image is produced.
    save_detections : bool, default False
        Persist annotated frames to disk (folder `detections/`).
    """
    balls = detect_balls(cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV))
    ar_marker = detect_aruco(bgr_img)
    target = None
    if ar_marker:
        target = find_nearest_ball(ar_marker.center, balls)

    res = AnalysisResult(balls=balls, aruco=ar_marker, target=target)

    if with_annotations:
        res.annotated = _draw_annotations(bgr_img, res)
    if save_detections and res.annotated is not None:
        _save_detected_frame(res.annotated)
    return res


# ---------------------------------------------------------------------------
# Optional: save annotated frames for offline debugging
# ---------------------------------------------------------------------------

def _save_detected_frame(frame: np.ndarray, folder: str = "detections") -> None:
    os.makedirs(folder, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    cv2.imwrite(f"{folder}/frame_{ts}.png", frame)
