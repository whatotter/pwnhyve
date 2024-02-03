from PIL import ImageFont
import subprocess
import os
import random, string
from core.SH1106.screen import *
from threading import Thread
from time import sleep
import netifaces as ni
from json import loads
from core.plugin import BasePwnhyvePlugin
from core.utils import config

class vars:
    font = ImageFont.truetype('core/fonts/roboto.ttf', 14)
    usbMounted = True
    usbUDCDisabled = False
    kernelGadgetDir = "/sys/kernel/config/usb_gadget/isticktoit/"

def fullClear(display):
    display.rectangle((0, 0, 200, 100), fill=1)
    return True

def isManaged(iface):
    a = loads(subprocess.getoutput("ip -j a show {}".format(iface)))

    if "BROADCAST" in a[0]["flags"]:
        return True # managed
    elif "radiotap" in a[0]["flags"]:
        return False # mon

class PWN_Storage(BasePwnhyvePlugin):

    def pMountUSB(draw, disp, image, GPIO):
        subprocess.getoutput("umount /piusb.bin -l") # lazy unmount
        subprocess.getoutput("mount /piusb.bin /mnt/otterusb")

    def pUMountUSB(draw, disp, image, GPIO):
        subprocess.getoutput("umount /piusb.bin -l") # lazy unmount

    def usbSteal(draw, disp, image, GPIO):
        """auto mount from https://gist.github.com/slobdell/7d052e01fed005f387b1c8e4994cd6d1"""
        fileSearch = config["badusb"]["exfilFiles"]

        extractPoint = "/tmp/pwnhyveExtractedUsb"

        try:
            os.mkdir(extractPoint)
        except: pass

        handler = usbRunPercentage(draw,disp,image) # init handler
        Thread(target=handler.start,daemon=True).start() # start handler

        handler.addText("creating mountdir")

        mkdirStr = ''.join([random.choice(string.ascii_letters) for _ in range(8)])

        MOUNT_DIR = "/mnt/{}".format(mkdirStr)

        foundFiles = {}

        os.mkdir(MOUNT_DIR)

        handler.addText("created mountdir")

        handler.addText("waiting for usb")

        sdaCommands = [
            "sudo fdisk -l | grep sda | grep -v Disk",
            "sudo fdisk -l | grep sdb | grep -v Disk"
        ]

        while True:
            output = None
            for x in sdaCommands:
                a = subprocess.getoutput(x)
                if len(a.strip("\n")) > 0:
                    output = a
                    continue

            if output is None: continue

            if checkIfKey(GPIO):
                handler.addText("quitting")
                handler.exit()
                sleep(1)
                return
                
            if len(output) > 0: # i dont even know anymore
                output = output.split("\n")
                handler.addText("got usb; mounting")
                o = subprocess.getstatusoutput("mount %s %s" % (output[0].split(" ")[0], MOUNT_DIR))

                if o[0] != 0: 
                    print("error mounting: {}".format(o[1]))
                    handler.addText("error mounting the usb")
                    try:
                        os.rmdir(MOUNT_DIR)
                    except: print("couldn't remove mount dir")

                    print("sudo mount %s %s" % (output[0].split(" ")[0], MOUNT_DIR))

                    waitForKey(GPIO)
                    handler.exit()

                    return

                print(output[0])
                print("sudo mount %s %s" % (output[0].split(" ")[0], MOUNT_DIR))
                break
            else:
                sleep(0.025)

        handler.addText("files to extract: {}".format('", "'.join(fileSearch)))
        handler.addText("using find command")

        for item in fileSearch:
            foundFiles[item] = []
            files = subprocess.getoutput("find {} -type f".format(MOUNT_DIR)).splitlines()
            for file in files:
                fileName = file.split("/")[-1]
                extension = fileName.split(".")[-1]
                
                if "."+extension in fileSearch:
                    foundFiles[item].append(file)

        handler.addText("now copying")

        for fileType in foundFiles:
            for file in foundFiles[fileType]:
                subprocess.getoutput("cp \"{}\" \"{}\"".format(file, extractPoint))

        handler.addText("unmounting")

        subprocess.getoutput("sudo umount {}".format(output[0].split(" ")[0]))

        handler.addText("done")
        handler.setPercentage(100)
        waitForKey(GPIO)
        sleep(0.25) # rebound

        # just for easier reading
        b = 0
        for found in foundFiles:
            b += len(foundFiles[found])

        handler.text = "total files: {}\ntarget\n{}\nextract to {}".format(b, output[0].split(" ")[0], extractPoint)

        waitForKey(GPIO)

        handler.exit()
        
        try:
            os.rmdir(MOUNT_DIR)
            subprocess.getoutput("sudo rm -rf {}".format(MOUNT_DIR))
        except Exception as e: print("couldn't remove mount dir: {}".format(str(e))); subprocess.getoutput("sudo rm -rf {}".format(MOUNT_DIR))

    def hostUmountUSB(draw, disp, image, GPIO):
        """i dont even know how i found this"""

        binFile = "/piusb.bin"

        if vars.usbMounted:
            subprocess.getoutput("echo \"\" > {}".format(vars.kernelGadgetDir+"functions/mass_storage.usb0/lun.0/file"))
        else:
            subprocess.getoutput("echo {} > {}".format(binFile, vars.kernelGadgetDir+"functions/mass_storage.usb0/lun.0/file"))

        vars.usbMounted = not vars.usbMounted

    def hostHideUSB(draw, disp, image, GPIO):
        """i dont even know how i found this v2"""


        # disable udc (or the entire gadget)
        subprocess.getoutput("echo "" > {}UDC".format(vars.kernelGadgetDir))

        if vars.usbUDCDisabled:
            # remake mass storage function
            a = subprocess.getoutput("ln -s {}functions/mass_storage.usb0 {}configs/c.1/".format(vars.kernelGadgetDir, vars.kernelGadgetDir))

            print("enable storage")
        else:
            # turn off mass storage function
            a = subprocess.getoutput("rm -rf {}configs/c.1/mass_storage.usb0".format(vars.kernelGadgetDir))

            print("disable storage")

        vars.usbUDCDisabled = not vars.usbUDCDisabled

        # turn udc back on
        subprocess.getoutput("ls /sys/class/udc > {}UDC".format(vars.kernelGadgetDir))
        
class PWN_System(BasePwnhyvePlugin):

    def setEnviroVars(draw, disp, image, GPIO):

        name, value = None, None
        
        choice = menu(draw, disp, image, ["set variable name", "set variable value"], GPIO)

        if choice == None: return
        elif choice == "set variable name":
            name = enterText(draw, disp, image, GPIO)
        elif choice == "set variable value":
            value = enterText(draw, disp, image, GPIO)

        while True:
            choice = menu(draw, disp, image,
                        ["name: {}".format(name) if name != None else "set variable name", "value: {}".format(value) if value != None else "set variable value", "set"], #wtf
                            GPIO)
            
            if choice == None or choice == "set": break
            elif choice == "set variable name":
                name = enterText(draw, disp, image, GPIO)
            elif choice == "set variable value":
                value = enterText(draw, disp, image, GPIO)
            
        os.environ[name] = value

        return


    def shutdown(draw, disp, image, GPIO):

        fullClear(draw)
        screenShow(disp, image, flipped=False, stream=True)

        print("shutdown thingy")
        print(subprocess.getoutput("sudo shutdown now"))

        sleep(5)

        return

    def reboot(draw, disp, image, GPIO):
        subprocess.getoutput("sudo reboot")
        return

    def system_info(draw, disp, image, GPIO):

        z = screenConsole(draw, disp, image)

        Thread(target=z.start, daemon=True).start()

        ifaces = {}
        jumbled = ""

        while checkIfKey(GPIO): pass

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

        sleep(1)

        z.exit()
        waitForKey(GPIO)
        while checkIfKey(GPIO): pass


    
def connectWifi(draw, disp, image, GPIO):

    fullClear(draw)

    def findNetworks():
        ssids = []
        for x in subprocess.getoutput("sudo iw dev wlan0 scan | grep SSID:").split("\n"):
            ssid = x.replace("SSID: ", "").strip()
            if len(ssid) == 0: continue
            ssids.append(ssid)
        return ssids
    
    def selectNetwork(ssids=findNetworks()):
        return menu(draw, disp, image, ssids, GPIO)


    ssid = selectNetwork()

    if ssid in findNetworks():
        pass
    else:
        return # ssid no more
    
    # copied n edited from setEnviroVars
    
    pwd = None
    
    while True:
        choice = menu(draw, disp, image,
                       ["ssid: {}".format(ssid), "password: {}".format(''.join(["*" for _ in pwd])) if pwd != None else "enter password", "connect"], #wtf
                         GPIO)
        
        if choice == None or choice == "connect": break
        elif choice == "ssid: {}".format(ssid):
            ssid = selectNetwork()
        elif choice == "enter password" or choice == "password: {}".format(''.join(["*" for _ in pwd])):
            pwd = enterText(draw, disp, image, GPIO, secret=True)
    
    subprocess.getoutput("sudo nmcli dev wifi connect {} password \"{}\"".format(ssid, pwd))
    
def fixInterfaces():
    # bandaid
    for x in ni.interfaces():
        subprocess.getoutput("sudo airmon-ng stop {}".format(x))
        subprocess.getoutput("sudo ifconfig {} up".format(x))
    subprocess.getoutput("sudo systemctl restart NetworkManager")

def functions():

    if os.path.exists("{}configs/c.1/mass_storage.usb0".format(vars.kernelGadgetDir)): vars.usbUDCDisabled = False
    else: vars.usbUDCDisabled = True

    return vars.config