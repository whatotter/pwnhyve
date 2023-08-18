from PIL import ImageFont
import subprocess
import os
import random, string
from core.SH1106.screen import *
from threading import Thread
from time import sleep
import netifaces as ni
from json import loads

class vars:
    config = { 
        # you can have this in an external file, aslong as main file gets it in dictionary format
        # this is for your command help n stuff
        # 123456789abcdefghijkl 123456789abcdefghijkl
        "usbUtils": {
            "usbSteal": "steal files with a filetype or keyword set in the script; auto mounts",

            "hostUmountUSB": "unmount the .bin file from host for reading on the pi",
            "hostHideUSB": "completely disable usb mass - as if you unplugged a usb",

            "pUMountUSB": "unmount the .bin file from the pi for using it on a victim",
            "pMountUSB": "mount the .bin file on the pi to read"
            
        },

        "systemUtils": {
            "shutdown": "shutdown Artremis and the pi",
            "reboot": "reboot the pi",
            "system_info": "info about the pi",
            #"localSSHMode": "enable ssh via usb, disables all other things",
            "setEnviroVars": "set enviroment variables for things",
            "connectWifi": "connect to a wifi network",
            "fixInterfaces": "bandaid fix to issues with interfaces"
        },

        "icons": {
            "shutdown": "./core/icons/tool.bmp",
            "reboot": "./core/icons/tool.bmp",
            "disableUSBstorage": "./core/icons/tool.bmp",
            "enableUSBstorage": "./core/icons/tool.bmp",
            "usbSteal": "./core/icons/usbfolder.bmp",

            "hostUmountUSB": "./core/icons/tool.bmp",
            "hostHideUSB": "./core/icons/tool.bmp",
            "pUMountUSB": "./core/icons/tool.bmp",
            "pMountUSB": "./core/icons/tool.bmp",

            "usbUtils": "./core/icons/usbfolder.bmp",
            "systemUtils": "./core/icons/tool.bmp",
            "setEnviroVars": "./core/icons/tool.bmp",
            "system_info": "./core/icons/graph.bmp",
            "nwkUtils": "./core/icons/ethfolder.bmp",

            "connectWifi": "./core/icons/wifi.bmp",
            "fixInterfaces": "./core/icons/tool.bmp",
            #"localSSHMode": "./core/icons/eth.bmp"
        }
    }

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

def pMountUSB(args:list):
    subprocess.getoutput("umount /piusb.bin -l") # lazy unmount
    subprocess.getoutput("mount /piusb.bin /mnt/otterusb")

def pUMountUSB(args:list):
    subprocess.getoutput("umount /piusb.bin -l") # lazy unmount

def terminal(args:list):
    """
    when i took this with me and had no access to my laptop (or any place to reliably fix bugs), i was left with rebooting the pi over and over
    if i had a terminal, it would've solved 90% of my problems and helped me diagnose most bugs
    this might be super hard to use, but its something
    """

    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

    z = screenConsole(draw, disp, image)
    Thread(target=z.start, daemon=True).start()

    while True:
        z.stopWriting = True # make the screen console stop writing so it doesn't overlap with the keyboard
        command = enterText(draw, disp, image, GPIO)
        if command == "": z.exit(); return
        z.stopWriting = False # allow the screen console to write once more

        z.text = subprocess.getoutput(command)
        waitForKey(GPIO, debounce=True)


    

def setEnviroVars(args:list):
    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

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

def usbSteal(args:list):
    """auto mount from https://gist.github.com/slobdell/7d052e01fed005f387b1c8e4994cd6d1"""
    fileSearch = open("./core/UsbExfilFiles", "r").read().split("\n")

    extractPoint = "/tmp/pwnhyveExtractedUsb"

    try:
        os.mkdir(extractPoint)
    except: pass

    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

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

def hostUmountUSB(args:list):
    """i dont even know how i found this"""

    binFile = "/piusb.bin"

    if vars.usbMounted:
        subprocess.getoutput("echo \"\" > {}".format(vars.kernelGadgetDir+"functions/mass_storage.usb0/lun.0/file"))
    else:
        subprocess.getoutput("echo {} > {}".format(binFile, vars.kernelGadgetDir+"functions/mass_storage.usb0/lun.0/file"))

    vars.usbMounted = not vars.usbMounted

def hostHideUSB(args:list):
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
    
def shutdown(args:list):
    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

    fullClear(draw)
    screenShow(disp, image, flipped=False, stream=True)

    print("shutdown thingy")
    print(subprocess.getoutput("sudo shutdown now"))

    sleep(5)

    return

def reboot(args:list):
    subprocess.getoutput("sudo reboot")
    return

def system_info(args:list):
    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

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

def connectWifi(args:list):
    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

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