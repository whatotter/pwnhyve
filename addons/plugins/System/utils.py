from PIL import ImageFont
import subprocess
import os
from time import sleep
import netifaces as ni
from json import loads
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow

# TODO: revamp whole thing

def isManaged(iface):
    a = loads(subprocess.getoutput("ip -j a show {}".format(iface)))

    if "BROADCAST" in a[0]["flags"]:
        return True # managed
    elif "radiotap" in a[0]["flags"]:
        return False # mon

usbMounted = False
kernelGadgetDir = "/sys/kernel/config/usb_gadget/isticktoit/"
usbUDCDisabled = False
font = ImageFont.truetype('core/fonts/roboto.ttf', 14)
USBEthernetEnabled = os.path.exists("{}configs/c.1/rndis.usb0".format(kernelGadgetDir)) # ln -s functions/rndis.usb0 configs/c.1/

class PWN_System(BasePwnhyvePlugin):
    def Set_Variables(tpil:tinyPillow):

        name, value = None, None
        
        choice = tpil.disp.menu(["set variable name", "set variable value"])

        if choice == None: return
        elif choice == "set variable name":
            name = tpil.disp.enterText()
        elif choice == "set variable value":
            value = tpil.disp.enterText()

        while True:
            choice = tpil.disp.menu(["name: {}".format(name) if name != None else "set variable name", "value: {}".format(value) if value != None else "set variable value", "set"])
            
            if choice == None or choice == "set": break
            elif choice == "set variable name":
                name = tpil.disp.enterText()
            elif choice == "set variable value":
                value = tpil.disp.enterText()
            
        os.environ[name] = value

        return

    def Shutdown(tpil):

        tpil.clear()
        tpil.show()

        print(subprocess.getoutput("sudo shutdown now"))

        sleep(5)

        return

    def Reboot(draw, disp, image):
        subprocess.getoutput("sudo reboot")
        return

    def System_Info(tpil):

        z = tpil.gui.screenConsole()

        ifaces = {}
        jumbled = ""

        for x in ni.interfaces():
            print(x)
            print(isManaged(x))
            try:
                ifaces[x] = ni.ifaddresses(x)[ni.AF_INET][0]['addr']
            except:
                ifaces[x] = "no addr assoc."

                if isManaged(x):
                    pass
                else:
                    ifaces[x] = "monitor mode"

        for x in ifaces:
            jumbled += "{}: {}\n".format(x, ifaces[x])

        z.text = "{}".format(jumbled)

        tpil.waitForKey()
        z.exit()
    
    def Connect_Wifi(tpil:tinyPillow):

        tpil.clear()

        def findNetworks():
            ssids = []
            for x in subprocess.getoutput("sudo iw dev wlan0 scan | grep SSID:").split("\n"):
                ssid = x.replace("SSID: ", "").strip()
                if len(ssid) == 0: continue
                ssids.append(ssid)
            return ssids
        
        def selectNetwork(ssids=findNetworks()):
            return tpil.gui.menu(ssids)


        ssid = selectNetwork()

        if ssid in findNetworks():
            pass
        else:
            return # ssid no more
        
        # copied n edited from setEnviroVars
        
        pwd = None

        menuDict = {
            "ssid: {}".format(ssid): "ssid",
            "password: {}".format(''.join(["*" for _ in pwd])) if pwd != None else "enter password": "pass",
            "connect": "connect"
        }
        
        while True:
            choice = tpil.gui.menu(menuDict)
            
            if choice == None or choice == "connect": break
            elif choice == "ssid: {}".format(ssid):
                ssid = selectNetwork()
            elif choice == "enter password" or choice == "password: {}".format(''.join(["*" for _ in pwd])):
                pwd = tpil.gui.enterText(secret=True)
        
            out = subprocess.getoutput("sudo nmcli dev wifi connect {} password \"{}\"".format(ssid, pwd))

            if "No network" in out:
                tpil.gui.toast("Network doesn't exist", [2,2], [tpil.width-2, 32])

    def Fix_Interfaces():
        # bandaid
        for x in ni.interfaces():
            subprocess.getoutput("sudo airmon-ng stop {}".format(x))
            subprocess.getoutput("sudo ifconfig {} up".format(x))
        subprocess.getoutput("sudo systemctl restart NetworkManager")