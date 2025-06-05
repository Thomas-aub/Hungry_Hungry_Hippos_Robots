import sys
import os

absolute_path = os.path.dirname(__file__)
relative_path = "../../Idefix/python/modules"
full_path = os.path.join(absolute_path, relative_path)
sys.path.append(full_path)

import argparse
import cv2

from networking import TCPClientAbstraction, DisconnectedException
from encoding import Packer

# Tools imports
relative_path_tools = "../../Idefix/python/tools"
full_path = os.path.join(absolute_path, relative_path_tools)
sys.path.append(full_path)

from jpeg_traits import JpegImage

class Client(TCPClientAbstraction):
    def __init__(self):
        super().__init__(2048)
        self.size = None
        self.frame = None
    def incomingMessage(self,buffer):
        if buffer is None:
            self.stop()
            return
        if buffer.length == 0:
            self.stop()
            return
        index, self.frame = Packer.unpack(buffer.buffer,0)
    def start(self,args):
        self.initialize(args.server,args.port)
        buffer = self.receive()
        if buffer is None:
            self.finalize()
            return
        if buffer.length == 0:
            self.finalize()
            return
        index, size = Packer.unpack(buffer.buffer, 0)
        print(size)
        self.passiveReceive(self.incomingMessage)
    def stop(self):
        self.finalize()

millisecondsToWait = 1000 // 30

if __name__ == "__main__":
    client = Client()
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', action='store', default='127.0.0.1', type=str, help='address of server to connect')
    parser.add_argument('-p', '--port', action='store', default=2120, type=int, help='port on server')
    args = parser.parse_args()
    try:
        client.start(args)
        while client.connected:
            if client.frame is not None:
                cv2.imshow('test',client.frame)
            key = cv2.waitKey(millisecondsToWait) & 0x0FF
            if key == ord('q'): break
        client.stop ()
    except DisconnectedException:
        print("Plantage du serveur et/ou de la connexion")
        client.stop()
 