
import cv2
import socket
import threading
from flux import captureThread, Frame

def main():
    stopProgram = threading.Event()
    stopThread = threading.Event()
    threadRunning = threading.Event()
    
    # Configuration
    ip = ""  # listen to all interfaces
    port = 8080
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    sock.bind((ip, port))
    
    print("Listening for UDP frames...")
    frame = Frame(100, 100)
    stopProgram.clear()
    stopThread.clear()
    
    thread = threading.Thread(target=captureThread, args=[sock, frame, stopThread, threadRunning], daemon=True)
    thread.start()
    
    while not stopProgram.is_set():
        if frame is not None:
            cv2.imshow("Received Frame", frame.mat)
            if frame.analysis_result:
                print(f"Balles rouges: {frame.analysis_result['red']}")
                print(f"Balles bleues: {frame.analysis_result['blue']}")
        
        ch = chr(cv2.waitKey(1) & 0xFF)
        if ch in ('q', 'Q'):
            stopProgram.set()
    
    stopThread.set()
    while threadRunning.is_set():
        pass
    
    sock.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()