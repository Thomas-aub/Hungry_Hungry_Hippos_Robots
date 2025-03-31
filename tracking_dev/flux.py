
import socket
import struct
import numpy as np
import cv2
import threading
import select
from tracking import incomingFrame

class Frame:
    def __init__(self, w, h):
        self.mat = np.zeros((h, w, 3), dtype=np.uint8)
        self.id = -1
        self.analysis_result = None

def gotFullData(data_buffer, iframe, frame_id):
    full_data = b''.join([data_buffer[i] for i in sorted(data_buffer)])
    messageLength = struct.unpack("I", full_data[:4])[0]
    frame_data = full_data[4:]
    
    if len(frame_data) == messageLength:
        frame_buffer = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(frame_buffer, 1)
        if frame is not None:
            incomingFrame(frame, iframe, frame_id)

def captureThread(sock, frame, stopThread, threadRunning):
    MaximumPacketSize = 1400
    timeout_ms = 0.01
    data_buffer = {}
    current_frame_id = -1
    threadRunning.set()
    
    while not stopThread.is_set():
        try:
            read_ready, _, _ = select.select([sock], [], [], timeout_ms)
            if read_ready:
                packet, addr = sock.recvfrom(MaximumPacketSize)
                packet_id, frame_id = struct.unpack('II', packet[:8])
                payload = packet[8:]
                
                if frame_id != current_frame_id:
                    if current_frame_id != -1:
                        gotFullData(data_buffer, frame, frame_id)
                    data_buffer = {}
                    current_frame_id = frame_id
                
                data_buffer[packet_id] = payload
        except socket.error:
            continue
    
    threadRunning.clear()
