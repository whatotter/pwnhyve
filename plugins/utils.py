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
            "umountUSB": "toggle mounting usb to read on current system",
            "mountUSB": "mount .bin file on the pi and read stuff on it",
            "toggleUSB": "toggle usb storage",
        },

        "nwkUtils": {
            "monitorMode": "toggle monitor mode"
        },

        "systemUtils": {
            "shutdown": "shutdown Artremis and the pi",
            "reboot": "reboot the pi",
            "system_info": "info about the pi",
            "localSSHMode": "enable ssh via usb, disables all other things"
        },

        "icons": {
            "shutdown": "./core/icons/tool.bmp",
            "reboot": "./core/icons/tool.bmp",
            "disableUSBstorage": "./core/icons/tool.bmp",
            "enableUSBstorage": "./core/icons/tool.bmp",
            "usbSteal": "./core/icons/usbfolder.bmp",
            "umountUSB": "./core/icons/tool.bmp",
            "mountUSB": "./core/icons/tool.bmp",
            "toggleUSB": "./core/icons/tool.bmp",
            "usbUtils": "./core/icons/usbfolder.bmp",
            "systemUtils": "./core/icons/tool.bmp",
            "system_info": "./core/icons/graph.bmp",
            "nwkUtils": "./core/icons/ethfolder.bmp",
            "localSSHMode": "./core/icons/eth.bmp"
        }
    }

    font = ImageFont.truetype('core/fonts/roboto.ttf', 14)
    usbMounted = True
    usbUDCDisabled = False
    kernelGadgetDir = "/sys/kernel/config/usb_gadget/isticktoit/"

def fullClear(display):
    display.rectangle((0, 0, 200, 100), fill=1)
    return True

def mountUSB(args:list):
    subprocess.getoutput("umount /piusb.bin -l") # lazy unmount
    subprocess.getoutput("mount /piusb.bin /mnt/otterusb")

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

def umountUSB(args:list):
    """i dont even know how i found this"""

    binFile = "/piusb.bin"

    if vars.usbMounted:
        subprocess.getoutput("echo \"\" > {}".format(vars.kernelGadgetDir+"functions/mass_storage.usb0/lun.0/file"))
    else:
        subprocess.getoutput("echo {} > {}".format(binFile, vars.kernelGadgetDir+"functions/mass_storage.usb0/lun.0/file"))

    vars.usbMounted = not vars.usbMounted

def toggleUSB(args:list):
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
    print("shutdown thingy")
    print(subprocess.getoutput("sudo shutdown now"))

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
        try:
            ifaces[x] = ni.ifaddresses(x)[ni.AF_INET][0]['addr']
        except:
            ifaces[x] = "no addr assoc."

    for x in ifaces:
        jumbled += "{}: {}\n".format(x, ifaces[x])

    z.text = "{}".format(jumbled)

    sleep(1)

    z.exit()
    waitForKey(GPIO)
    while checkIfKey(GPIO): pass

def monitorMode(args:list):
    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

    print("monitor mode shit")

    ifaces = ni.interfaces()
    priority = loads(open("./config.json", "r").read())

    if priority["normalInterface"] in ifaces:
        jsond = loads(subprocess.getoutput("ip -j a"))[0]

        subprocess.getoutput("sudo airmon-ng start {}".format(priority["normalInterface"]))
        draw.text([8,8], "started interface", fill=1, outline=255, font=None)

    """elif priority["monitorInterface"] in ifaces:
        subprocess.getoutput("sudo airmon-ng stop {}".format(priority["monitorInterface"]))
        draw.text([8,8], "stopped interface", fill=1, outline=255, font=None)"""

    disp.ShowImage(disp.getbuffer(image))

    waitForKey(GPIO)
    while checkIfKey(GPIO): pass

def localSSHMode(args:list):
    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

    fullClear(draw)

    draw.text((2,2), "this will reboot the pi, are you sure?\n\nup = yes\ndown = no")

    disp.ShowImage(disp.getbuffer(image))

    waitForKey(GPIO)
    if getKey(GPIO) == 6:
        pass
    else:
        return
    
    fullClear(draw)
    disp.ShowImage(disp.getbuffer(image))
    
    if "pwnhyveusb001" not in os.listdir("/bin"):
        subprocess.getoutput("sudo mv /bin/pwnhyveusb /bin/pwnhyveusb001")
        subprocess.getoutput("sudo mv /bin/pwnhyvessh /bin/pwnhyveusb")
    else:
        subprocess.getoutput("sudo mv /bin/pwnhyveusb /bin/pwnhyvessh")
        subprocess.getoutput("sudo mv /bin/pwnhyveusb001 /bin/pwnhyveusb")

    reboot(args)


def functions():

    if os.path.exists("{}configs/c.1/mass_storage.usb0".format(vars.kernelGadgetDir)): vars.usbUDCDisabled = False
    else: vars.usbUDCDisabled = True

    return vars.config