import time,socket,threading

class pluginManager():
    def __init__(self, unSock:socket.socket, exSock:socket.socket, unixTuple=("127.0.0.1", 62117), exitTuple=("127.0.0.1", 62117)) -> None:
        self.exitThread = False
        
        # socks
        self.unixSock = unSock # data sock - send stuff through here, and it'll show up in the control panel; MUST BE UTF8 ENCODED
        self.exitSock = exSock # sock to receive exit command

        print("[WEBSERVER PLUGIN] attempting connection to webserver")

        self.unixSock.connect(unixTuple)

        print("[WEBSERVER PLUGIN] starting exitsock handler")
        threading.Thread(target=self.exitSockHandler, args=(exitTuple,), daemon=True).start()

        print("[WEBSERVER PLUGIN] started exitsock handler; ready")

        return None
    
    def send(self, string):
        try:
            return self.unixSock.sendall(str(string).encode("utf-8"))
        except:
            return False
        
    def recv(self, buffer:int=1024):
        self.unixSock.sendall("userIntervention".encode("utf-8")) # start reading from input
        return self.unixSock.recv(buffer).decode("utf-8")

    def exitSockHandler(self, serverTuple):

        self.exitSock.connect(serverTuple)

        self.exitSock.setblocking(False)

        while True:
            try:
                a = self.exitSock.recv(512).decode('utf-8')
            except: a = None

            if self.exitThread == True: # if someone else put exitThread
                #print("exitSock: ive been told to die from a bool")
                self.exitThread = False
                quit() # die

            if a == "exit":
                #print("exitSock: ive been told to die from socket")
                self.exitThread = True # tells main plugin thread to pack up and die

                while self.exitThread: # waits for main plugin thread to pack up
                    pass

                a.sendall("ok".encode("utf-8")) # tells server "we packed up and are now dying"

                return # dies
            
            time.sleep(0.05) # not eat cpu

    def exitPlugin(self):
        self.exitThread = True # set other thread to die
        while self.exitThread: pass

        self.unixSock.sendall("exit".encode("utf-8")) # send closing through socket - SEND THIS BEFORE CLOSING SOCKET
        self.unixSock.close() # completely die
        self.exitSock.close() # ^