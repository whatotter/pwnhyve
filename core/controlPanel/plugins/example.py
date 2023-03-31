import socket, time

exitThread = False

def exitSockHandler(sock, serverTuple):
    global exitThread

    sock.connect(serverTuple)

    sock.setblocking(False)

    while True:
        try:
            a = sock.recv(512).decode('utf-8')
        except: a = None

        if exitThread == True: # if someone else put exitThread
            quit() # die

        if a == "exit":
            exitThread = True # tells main plugin thread to pack up and die

            while exitThread: # waits for main plugin thread to pack up
                pass

            a.sendall("ok".encode("utf-8")) # tells server "we packed up and are now dying"

            return # dies
        
        time.sleep(0.1) # not eat cpu

def test(ipTuple):
    global exitThread
    # ipTuple[0] is data sock; you send to data
    # ipTuple[1] is exit sock; you recieve from
    # doesn't matter which thread you connect to first
    # !!!!!!!!data will/must always be encoded in utf-8!!!!!!!!

    unixSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    exitSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    unixSock.connect(ipTuple[0])
    exitSockHandler(exitSock, ipTuple[1])

    # plugin do stuff

    unixSock.sendall("hello world!".encode("utf-8"))
    unixSock.sendall("how was your day?".encode("utf-8"))

    unixSock.sendall("userIntervention".encode("utf-8")) # start reading from input
    response = unixSock.recv(1024).decode("utf-8")

    unixSock.sendall("you entered: {}".format(response))

    exitThread = True # set other thread to die
    time.sleep(0.2) # wait for other thread to die
    unixSock.close() # completely die
    exitSock.close() # ^

def functions():
    return {
        "test": "test"
    }