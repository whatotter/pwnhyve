from PIL import Image, ImageOps, ImageDraw
from time import sleep
from core.plugin import pwnhyveMenuLoader
from io import BytesIO
import base64

import core.displayDrivers.__helper__ as h

s = pwnhyveMenuLoader()
screens = s.modules
mr = None

class DispDummy():
    width = 128
    height = 64

class DisplayDriver():
    def __init__(self, screen) -> None:
        global mr
        print("[DISPLAY] initalizing display driver...", end="")


        self.image = Image.new('1', (128, 64), "WHITE") # init display
        self.draw = ImageDraw.Draw(self.image) # dsiayp
        self.GPIO = None
        self.disp = DispDummy()

        self.pinout = { # gpio pins are the buttons, like joystick, side buttons, etc.
            'up': 6,
            'down': 19,
            'left': 5,
            'right': 26,
            'press': 13,
            '1': 21,
            '2': 20,
            '3': 16,
        }

        self.gui = screen.Screen(self.draw, self, self.image)

        self.width = 128
        self.height = 64

        # from sh1106.py
        # properties of display
        self.hasColor = False
        self.invertedColor = True
        self.width = self.disp.width
        self.height = self.disp.height
        self.name = "SH1106"
        # these are variables due to PPI differences
        self.recommendedFontSize = 16 # font size for decent readability
        self.iconSize = 8
        
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

        a = h.checkSocketINput()
        if a:
            return a

        return False
        
    def showImage(self, directory):
        bmp = Image.open(directory)
        self.draw.paste(bmp, (0,0))
<<<<<<< Updated upstream
        # Himage2=Himage2.rotate(180) 	
=======
        # Himage2=Himage2.rotate(180) 	
>>>>>>> Stashed changes
