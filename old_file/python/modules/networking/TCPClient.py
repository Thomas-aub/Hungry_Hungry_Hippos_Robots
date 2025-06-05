import socket
import threading
import struct

from .TCPAbstraction import TCPAbstraction, DisconnectedException
from .Buffer import Buffer

class TCPClientAbstraction(TCPAbstraction):
    def __init__(self,bufferSize):
        super().__init__(bufferSize)
        self.threadRunning = False
        self.threadReceive = None
        self._stop = False
    def initialize(self,address,port):
        if self.connected: return
        self.mainSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mainSocket.connect((address,port))
        self.connected = True
    def finalize(self):
        if not self.connected: return
        self._stop = True
        if self.threadReceive is not None:
            if self.threadRunning:
                self.threadReceive.join()
        self.mainSocket.close()
        self.connected = False
    def receive(self):
        try:
            bufSize = super()._receive(self.mainSocket,6)
            fmt = bufSize.buffer[0:2]
            data = bufSize.buffer[2:]
            (size,) = struct.unpack('!i',data)
            return super()._receive(self.mainSocket,size)
        except DisconnectedException:
            raise DisconnectedException()
    def send(self,buffer):
        try:
            bufSize = Buffer(b'!i'+struct.pack('!i',len(buffer.buffer)))
            super()._send(self.mainSocket,bufSize)
            super()._send(self.mainSocket,buffer)
        except DisconnectedException:
            raise DisconnectedException()
    def hasMessage(self):
        return super()._awaitingMessage(self.mainSocket)
    def passiveReceive(self,callback):
        self.threadReceive = threading.Thread(target=self._threadPassiveReceive, args=(callback,))
        self.threadReceive.start()
    def _threadPassiveReceive(self,callback):
        try:
            self.threadRunning = True
            while not self._stop:
                if self.hasMessage():
                    buffer = self.receive()
                    callback(buffer)
            self.threadRunning = False
        except DisconnectedException:
            self._stop = True
            self.threadRunning = False
            self.finalize()
