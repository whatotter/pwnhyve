from PIL import Image, ImageFont, ImageOps, ImageDraw
from time import sleep
from core.plugin import pwnhyveMenuLoader
from io import BytesIO
import base64

import core.screens.__helper__ as h


s = pwnhyveMenuLoader()
screens = s.modules
mr = None

class DisplayDriver():
    def __init__(self, screen) -> None:
        global mr
        print("[DISPLAY] initalizing display driver...", end="")


        self.image = Image.new('1', (128, 64), "WHITE") # init display
        self.draw = ImageDraw.Draw(self.image) # dsiayp
        self.GPIO = None

        self.pinout = { # gpio pins are the buttons, like joystick, side buttons, etc.
            'KEY_UP_PIN': 6,
            'KEY_DOWN_PIN': 19,
            'KEY_LEFT_PIN': 5,
            'KEY_RIGHT_PIN': 26,
            'KEY_PRESS_PIN': 13,
            'KEY1_PIN': 21,
            'KEY2_PIN': 20,
            'KEY3_PIN': 16,
        }

        self.gui = screen.Screen(self.draw, self, self.image, self.GPIO)

        self.width = 128
        self.height = 64
        
        mr = self

        pass

    def fullClear(self, draw):
        draw.rectangle((0, 0, 200, 100), fill=1)
        return True

    def screenShow(self, *args, **kwargs):
        buffered = BytesIO()
        
        invimage = ImageOps.invert(self.image.convert('L'))
        invimage.save(buffered, format="JPEG")

        img_str = base64.b64encode(buffered.getvalue())

        h.sockStream.queue.append(img_str)
        h.sockStream.mostRecentImage = img_str


    def waitForKey(self, debounce=True):
        """
        wait for key press and return the key pressed

        debounce waits for the key to be released
        """

        a = None

        while 1: # wait for key press
            sockGPIO = h.checkSocketINput()
            if not sockGPIO:
                pass
            else:
                a = sockGPIO
                break

            sleep(0.05) # prevent really fast ticks

        return a
    
    def waitWhileChkKey(self, s, resolution=0.05):
        """wait s seconds while also checking for a keypress"""

        tw = round(s / resolution)

        for x in range(tw):
            a = self.getKey()
            if a != False:
                return a

            sleep(resolution)

        return False

    def checkIfKey(self):
        """check if there is a key being pressed"""

        if h.checkSocketINput():
            return True

        return False

    def getKey(self):
        """get key without waiting; return current key pressed"""

        print("z")

        a = h.checkSocketINput()
        if a:
            return a

        return False
        
    def showImage(self, disp, directory):
        img = Image.new('1', (disp.width, disp.height), 255)  # 255: clear the frame
        bmp = Image.open(directory)
        img.paste(bmp, (0,5))
        # Himage2=Himage2.rotate(180) 	
