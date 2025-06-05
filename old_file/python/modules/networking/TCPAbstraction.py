import select

from .Buffer import Buffer

class DisconnectedException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class TCPAbstraction:
    def __init__(self,bufferSize):
        self.mainSocket = None
        self.connected = False
        self.bufferSize = bufferSize
    def _awaitingMessage(self,socket):
        if not self.connected: return False
        try:
            readable, writable, errored = select.select([socket], [], [],0.00001)
            for s in readable:
                if s is socket: return True
            return False
        except Exception:
            raise DisconnectedException()
    def _receive(self,socket,size):
        if not self.connected: return None
        try:
            remaining = size
            frameBuffer = bytearray()
            while True:
                data = socket.recv(self.bufferSize if self.bufferSize < remaining else remaining)
                if len(data) == 0:
                    raise DisconnectedException()
                frameBuffer = frameBuffer + data
                remaining = remaining - len(data)
                if remaining == 0: break
            return Buffer(frameBuffer)
        except Exception:
            raise DisconnectedException()
    def _send(self,socket,buffer):
        if not self.connected: return
        try:
            socket.sendall(buffer.buffer)
        except Exception:
            raise DisconnectedException()

    