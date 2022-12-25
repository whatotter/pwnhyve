from PIL import ImageFont
import time
import subprocess

class vars:
    config = { 
        # you can have this in an external file, aslong as main file gets it in dictionary format
        # this is for your command help n stuff
        # 123456789abcdefghijkl 123456789abcdefghijkl
        "disableUSBstorage": "disable usb storage|requires reboot",
        "enableUSBstorage": "enable usb storage",
        "shutdown": "shutdown Artremis and the pi",
        "reboot": "reboot the pi",
    }

    font = ImageFont.truetype('core/fonts/roboto.ttf', 14)

def fullClear(display):
    display.rectangle((0, 0, 200, 100), fill=1)
    return True

def disableUSBstorage(args:list):
    draw, display, image, gpio = args[0], args[1], args[2], args[3]
    archived = []

    with open("/usr/bin/isticktoit_usb", "r") as data:
        filedata = data.read().split("\n")

    for s in filedata:
        if "usbEnabled=" in s:
            s = "usbEnabled=0"

        archived.append(s)

    with open("/usr/bin/isticktoit_usb", "w") as data:
        data.write('\n'.join(archived))
        data.flush()

    fullClear(draw)

    draw.text((10, 10), "disabled usb storage", fill=0, outline=255, font=vars.font)

    display.ShowImage(display.getbuffer(image))

    time.sleep(3)

    return

def enableUSBstorage(args:list):
    draw, display, image, gpio = args[0], args[1], args[2], args[3]
    archived = []

    with open("/usr/bin/isticktoit_usb", "r") as data:
        filedata = data.read().split("\n")

    for s in filedata:
        if "usbEnabled=" in s:
            s = "usbEnabled=1"

        archived.append(s)

    with open("/usr/bin/isticktoit_usb", "w") as data:
        data.write('\n'.join(archived))
        data.flush()

    fullClear(draw)

    draw.text((10, 10), "enabled usb storage", fill=0, outline=255, font=vars.font)

    display.ShowImage(display.getbuffer(image))

    time.sleep(3)

    return

def shutdown(args:list):
    subprocess.getoutput("sudo shutdown now")

    return

def reboot(args:list):
    subprocess.getoutput("sudo reboot")

    return

def functions():
    """
    put your executable functions here and your configuration
    """
    return vars.config