
import cv2
import numpy as np
import os
from datetime import datetime

def save_detected_frame(frame):
    if not os.path.exists('detections'):
        os.makedirs('detections')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"detections/frame_{timestamp}.png"
    cv2.imwrite(filename, frame)
    print(f"Frame enregistrée: {filename}")

def analysis(frame):
    color_thresholds = {
        'red': [
            {'lower': np.array([0, 120, 70]), 'upper': np.array([10, 255, 255])},
            {'lower': np.array([170, 120, 70]), 'upper': np.array([180, 255, 255])}
        ],
        'blue': [
            {'lower': np.array([90, 120, 70]), 'upper': np.array([120, 255, 255])}
        ]
    }
    
    result_frame = frame.copy()
    detected_balls = {'red': [], 'blue': []}
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv[:,:,2] = cv2.equalizeHist(hsv[:,:,2])
    
    for color in color_thresholds:
        combined_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for threshold in color_thresholds[color]:
            mask = cv2.inRange(hsv, threshold['lower'], threshold['upper'])
            combined_mask = cv2.bitwise_or(combined_mask, mask)
        
        kernel = np.ones((5,5), np.uint8)
        cleaned_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        cleaned_mask = cv2.dilate(cleaned_mask, kernel, iterations=2)
        
        contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 30:
                continue
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            center = (int(x), int(y))
            radius = int(radius)
            
            if 5 <= radius <= 100:
                detected_balls[color].append((center[0], center[1], radius))
                color_bgr = (0, 0, 255) if color == 'red' else (255, 0, 0)
                cv2.circle(result_frame, center, radius, color_bgr, 2)
                cv2.circle(result_frame, center, 2, (0, 255, 0), 3)
                cv2.putText(result_frame, f"{color} {radius}", (center[0]-radius, center[1]-radius-5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
    
    return result_frame, detected_balls

def incomingFrame(frame, iframe, frame_id):
    analyzed_frame, balls_data = analysis(frame)
    iframe.mat = analyzed_frame
    iframe.analysis_result = balls_data
    iframe.id = frame_id
    if any(balls_data.values()):
        save_detected_frame(analyzed_frame)
