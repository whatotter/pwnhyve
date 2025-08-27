import threading
import subprocess
import time
import core.remotecontrol.serve as WebUI
from core.utils import *

class WebUIWorker():
    """
    just runs the webui in the background
    """
    def __init__(self) -> None:
        pass

    def start(self, tpil):
        WebUI.socketio.run(WebUI.app, port=5000, host="0.0.0.0")

class USBNotifyWorker():
    """
    usb notification class
    """

    def __init__(self) -> None:
        pass

    def parseUSBText(self, text):
        # i don't wanna talk about it
        devices = [x.split("ID ",1)[-1].split(" ",1)[-1].strip() for x in text.split("\n")]
        return [x.split(". ", 1)[-1] for x in list(filter(lambda x: True if "Linux" not in x else False, devices))]

    def start(self, tpil):
        pluggedIn = self.parseUSBText(subprocess.getoutput("lsusb"))

        while True:
            currentUSB = self.parseUSBText(subprocess.getoutput("lsusb"))

            if len(currentUSB) != len(pluggedIn): # there is a difference between what we know, and what's plugged in
                
                if len(currentUSB) > len(pluggedIn):
                    difference = list(filter(lambda x: True if x not in pluggedIn else False, currentUSB)) # find the difference
                else:
                    difference = list(filter(lambda x: True if x not in currentUSB else False, pluggedIn)) # find the difference

                if len(pluggedIn) > len(currentUSB):
                    tpil.gui.toast("USB removed:\n{}".format(difference[0]), [1,2], [tpil.width-3, 26],
                                   timeout=3)
                else:
                    tpil.gui.toast("USB inserted:\n{}".format(difference[0]), [1,2], [tpil.width-3, 26], 
                                   timeout=3)

            pluggedIn = currentUSB.copy()
            time.sleep(0.25)


class ThreadedWorker():
    """for notifications and stuff to be ran in the bg"""
    def __init__(self, workerObject, args=()) -> None:
        self.object = workerObject
        self.thread = None
        self.args = args
        pass

    def startWorker(self):
        self.thread = threading.Thread(target=self.object.start, args=self.args, daemon=True)
        self.thread.start()
        uStatus("[BackgroundWorker] background thread started for {}".format(self.object))

        return self.thread