import socket

class BrickServer:
    def __init__(self, this_ip, port) -> None:
        self.ip = this_ip
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.ip, self.port))
        self.server.settimeout(8)
        self.client, self.addr = "", ""
    
    def listen(self) -> None:
        self.server.listen(5)
        print("Server is listening on %s:%d" % (self.ip, self.port))
        self.client, self.addr = self.server.accept()
        
        self.send_string("ready")
    
    def send_string(self, str) -> None:
        self.client.send(str.encode())

    def execute(self, instruction, params) -> None:
        value = str(instruction) + "," + str(params)
        packet = ""
        valueLen = len(value)
        valueLenLen = len(str(valueLen))
        for _ in range(0, 8-valueLenLen):
            packet += '0'
        packet += str(valueLen)
        packet += "EXC"
        packet += value
        self.client.send(packet.encode())
            

        
