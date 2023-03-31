import socket
from core.controlPanel.pManager import pluginManager

exitThread = False

def test(ipTuple):
    global exitThread

    unixSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    exitSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    a = pluginManager(unixSock, exitSock, unixTuple=ipTuple[0], exSock=ipTuple[1])

    # do ur plugin stuff here

    a.send("hello world!")
    a.send("how was your day?")

    response = a.recv()

    a.send("you entered: {}".format(response))

    print("reply: {}".format(response))

    # exit everything - once plugin has ended, do this

    a.exitPlugin()

def functions():
    return {
        "test": "test"
    }