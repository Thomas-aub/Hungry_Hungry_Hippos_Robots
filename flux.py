"""
flux.py — gestion du flux UDP multipart
Aucune dépendance vers l’analyse : on se contente de livrer la dernière image décodée.
"""
import socket, struct, select, threading
import numpy as np
import cv2
from typing import Optional


class UdpFrameReceiver:
    """
    Reconstruit un JPEG fragmenté envoyé par paquets UDP de la forme :

        [uint32 packet_id][uint32 frame_id][payload]

    Le premier packet_id (=0) commence par un uint32 messageLength qui vaut
    la taille totale de l’image encodée.
    """
    def __init__(self, ip: str = "", port: int = 8080, packet_size: int = 1400):
        self.ip, self.port, self.packet_size = ip, port, packet_size
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip, self.port))
        self.sock.setblocking(False)

        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        self._current_frame_id = -1
        self._data_buffer: dict[int, bytes] = {}
        self._latest_frame: Optional[np.ndarray] = None

    # ---------- boucle interne ------------------------------------------------
    def _push_frame(self) -> None:
        full = b"".join(self._data_buffer[i] for i in sorted(self._data_buffer))
        msg_len = struct.unpack("I", full[:4])[0]
        jpeg = full[4:]
        if len(jpeg) != msg_len:
            return                          # paquet incomplet ou corrompu
        frame = cv2.imdecode(np.frombuffer(jpeg, np.uint8), 1)
        if frame is None:
            return
        with self._lock:
            self._latest_frame = frame

    def _run(self) -> None:
        timeout = 0.01
        while not self._stop.is_set():
            try:
                r, *_ = select.select([self.sock], [], [], timeout)
                if not r:
                    continue
                packet, _ = self.sock.recvfrom(self.packet_size)
                packet_id, frame_id = struct.unpack("II", packet[:8])
                payload = packet[8:]

                if frame_id != self._current_frame_id:
                    if self._current_frame_id != -1 and self._data_buffer:
                        self._push_frame()
                    self._data_buffer, self._current_frame_id = {}, frame_id
                self._data_buffer[packet_id] = payload
            except socket.error:
                continue
        # avant de quitter, tenter de pousser la dernière frame
        if self._data_buffer:
            self._push_frame()

    # ---------- API publique ---------------------------------------------------
    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def get_frame(self) -> Optional[np.ndarray]:
        """Renvoie une **copie** de la dernière image (ou None)."""
        with self._lock:
            return None if self._latest_frame is None else self._latest_frame.copy()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join()
        self.sock.close()
