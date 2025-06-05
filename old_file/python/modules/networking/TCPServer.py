import socket
import select
import threading
import struct

from .TCPAbstraction import TCPAbstraction, DisconnectedException
from .Buffer import Buffer

class TCPServerAbstraction(TCPAbstraction):
    def __init__(self,bufferSize):
        super().__init__(bufferSize)
        self.clientSockets = []
        self.clientLock = threading.Lock()
        self._stop = False
        self.connectionThreadRunning = False
        self.connectionThread = None
        self.receiveThreadRunning = False
        self.receiveThread = None
    def initialize(self,interface,port):
        if self.connected: return
        self.mainSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mainSocket.bind((interface, port))
        self.connected = True
    def finalize(self):
        if not self.connected: return
        self._stop = True
        if self.connectionThread is not None:
            if self.connectionThreadRunning:
                self.connectionThread.join()
        if self.receiveThread is not None:
            if self.receiveThreadRunning:
                self.receiveThread.join()
        for client in self.clientSockets:
            if client[2]:
                client[0].close()
        self.mainSocket.close()
        self.connected = False
    ###
    #   communication callbacks
    ###
    def onConnected(self,client):
        return False
    def onDisconnected(self,client):
        pass
    def onMessage(self,client,buffer):
        pass
    ###
    #   Client connection
    ###
    def waitForClient(self):
        self.mainSocket.listen()
        socketClient, addresseClient = self.mainSocket.accept()
        client = [socketClient, addresseClient, True, True]
        client[3] = self.onConnected(client)
        with self.clientLock:
            self.clientSockets.append(client)
        return client
    def listenToClients(self):
        self.connectionThread = threading.Thread(target=self._threadListenToClients,name='client listener')
        self.connectionThread.daemon = True
        self.connectionThread.start()
    def _threadListenToClients(self):
        self.mainSocket.listen()
        self.connectionThreadRunning = True
        while not self._stop:
            readable, writable, errored = select.select([self.mainSocket], [], [],0.00001)
            for s in readable:
                if s is self.mainSocket:
                    socketClient, addresseClient = self.mainSocket.accept()
                    client = [socketClient, addresseClient, True, True]
                    client[3] = self.onConnected(client)
                    with self.clientLock:
                        self.clientSockets.append(client)
            self._cleanUp()
        self.connectionThreadRunning = False
    ###
    #   Message to client
    ###
    def sendTo(self,client,buffer):
        if not client[2]: return
        bufSize = Buffer(b'!i'+struct.pack('!i',len(buffer.buffer)))
        try:
            super()._send(client[0],bufSize)
            super()._send(client[0],buffer)
        except DisconnectedException:
            self.onDisconnected(client)
            client[2] = False
    def broadcast(self,buffer):
        bcaster = []
        with self.clientLock:
            bcaster = list(filter(lambda x: x[3], self.clientSockets))
        for client in bcaster:
            self.sendTo(client,buffer)
    ###
    #   Message from client
    ###
    def receiveFrom(self,client):
        buffer = None
        if not client[2]: return
        try:
            bufSize = super()._receive(client[0],6)
            fmt = bufSize.buffer[0:2]
            data = bufSize.buffer[2:]
            (size,) = struct.unpack('!i',data)
            buffer = super()._receive(client[0],size)
            return buffer
        except DisconnectedException:
            self.onDisconnected(client)
            client[2] = False
        return None
    def passiveReceive(self):
        self.receiveThread = threading.Thread(target=self._threadPassiveReceive,name='client receiver')
        self.receiveThread.daemon = True
        self.receiveThread.start()
    def _threadPassiveReceive(self):
        self.receiveThreadRunning = True
        while not self._stop:
            sockets = None
            if len(self.clientSockets)>0:
                clients = []
                with self.clientLock:
                    clients = [x for x in self.clientSockets]
                sockets = [x[0] for x in clients]
                readable, writable, errored = select.select(sockets, [], [],0.00001)
                for s in readable:
                    if s in sockets:
                        index = sockets.index(s)
                        client = clients[index]
                        if client[2]:
                            try:
                                buffer = None
                                bufSize = super()._receive(client[0],6)
                                fmt = bufSize.buffer[0:2]
                                data = bufSize.buffer[2:]
                                (size,) = struct.unpack('!i',data)
                                buffer = super()._receive(client[0],size)
                                if buffer is None:
                                    self.onDisconnected(client)
                                    client[2] = False
                                else:
                                    self.onMessage(client,buffer)
                            except DisconnectedException:
                                self.onDisconnected(client)
                                client[2] = False
                self._cleanUp()
        self.receiveThreadRunning = False
    ###
    #   Cleanup client list
    ###
    def _cleanUp(self):
        with self.clientLock:
            self.clientSockets = list(filter(lambda x: x[2], self.clientSockets))
            for client in self.clientSockets:
                try:
                    self._check(client[0])
                except DisconnectedException:
                    self.onDisconnected(client)
                    client[2] = False
            self.clientSockets = list(filter(lambda x: x[2], self.clientSockets))
    @property
    def nClients(self):
        return len(self.clientSockets)
    @property
    def clients(self):
        return [x[1] for x in self.clientSockets]
