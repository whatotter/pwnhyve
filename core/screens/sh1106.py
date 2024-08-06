from PIL import Image, ImageFont, ImageOps, ImageDraw
from time import sleep
from core.utils import redir, config
from core.plugin import pwnhyveMenuLoader
from io import BytesIO
import base64
from core.screens.sh1106 import *
import RPi.GPIO as GPIO
import core.screens.__helper__ as h

import core.SH1106.SH1106m as SH1106

#GPIO define
RST_PIN        = 22
CS_PIN         = 24
DC_PIN         = 18

KEY_UP_PIN     = 31 
KEY_DOWN_PIN   = 35
KEY_LEFT_PIN   = 29
KEY_RIGHT_PIN  = 37
KEY_PRESS_PIN  = 33

KEY1_PIN       = 40
KEY2_PIN       = 38
KEY3_PIN       = 36

programCoords = {}
s = pwnhyveMenuLoader()
screens = s.modules

class DisplayDriver():
    def __init__(self, screen) -> None:
        print("[DISPLAY] initalizing display driver...", end="")

        self.pinout = { # gpio pins are the buttons, like joystick, side buttons, etc.
            'u': 31,
            'd': 35,
            'l': 29,
            'r': 37,
            'p': 33,
            '1': 40,
            '2': 38,
            '3': 36,
        }

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)

        self.disp = SH1106.SH1106()
        self.disp.Init()
        self.disp.clear()

        self.image = Image.new('1', (self.disp.width, self.disp.height), "WHITE") # init display
        self.draw = ImageDraw.Draw(self.image) # dsiayp
        self.GPIO = GPIO

        self.keysBeingHeld = []

        print("/ [GPIO] initalizing GPIO pins...")
        for gpioPin in self.pinout: # init gpio
            print("| [GPIO] initializing GPIO pin {}...".format(self.pinout[gpioPin]), end="")
            GPIO.setup(self.pinout[gpioPin],GPIO.IN,pull_up_down=GPIO.PUD_UP)
            print("initalized")
        print("\\ [GPIO] done initalizing GPIO pins.\n")

        self.gui = screen.Screen(self.draw, self, self.image, self.GPIO)
        
        pass

    def waitWhileChkKey(self, s, resolution=0.05):
        """wait s seconds while also checking for a keypress"""

        tw = round(s / resolution)

        for x in range(tw):
            a = self.getKey()
            if a != False:
                return a

            sleep(resolution)

        return False

    def waitForKey(self, debounce=True):
        """
        wait for key press and return the key pressed

        debounce waits for the key to be released
        """

        a = None
        b = None

        # this makes holding down a key like how it does on a usb keyboard, if you hold it down it'll send the key once, \
        # then wait a bit (around a quarter of a second/half a second), then repeatedly send it while it's held down
        for x in self.keysBeingHeld.copy():
            c = self.checkIfKey(debounce=False, key=x)
            if c:
                sleep(0.1)
                return x
            else:
                self.keysBeingHeld.remove(x)
            
        while 1: # wait for key press
            sockGPIO = h.checkSocketINput()
            if not sockGPIO:
                pass
            else:
                a = sockGPIO
                break

            if not self.GPIO.input(KEY_UP_PIN): a = "u"; b=KEY_UP_PIN; break

            if not self.GPIO.input(KEY_LEFT_PIN): a = "l"; b=KEY_LEFT_PIN; break
            
            if not self.GPIO.input(KEY_RIGHT_PIN): a = "r"; b=KEY_RIGHT_PIN; break
            
            if not self.GPIO.input(KEY_DOWN_PIN): a = "d"; b=KEY_DOWN_PIN; break

            if not self.GPIO.input(KEY_PRESS_PIN): a = 'p'; b=KEY_PRESS_PIN; break
            
            if not self.GPIO.input(KEY1_PIN): a = '1'; b=KEY1_PIN; break
            
            if not self.GPIO.input(KEY2_PIN): a = '2'; b=KEY2_PIN; break
            
            if not self.GPIO.input(KEY3_PIN): a = '3'; b=KEY3_PIN; break

            sleep(0.01) # prevent really fast ticks

        if debounce:
            downcycles = 0
            while not self.GPIO.input(b):
                downcycles += 1
                if downcycles >= 250:
                    self.keysBeingHeld.append(a)
                    return a # it's being held down
                
                sleep(0.001)

        return a

    def checkIfKey(self, debounce=True, key=False):
        """check if there is a key being pressed"""

        if key != False:
            return not self.GPIO.input(self.pinout[key[0]])

        a = h.checkSocketINput()
        b = None
        if a:
            return True

        if key == False:
            if not self.GPIO.input(KEY_UP_PIN): b=KEY_UP_PIN; return True

            if not self.GPIO.input(KEY_LEFT_PIN): b=KEY_LEFT_PIN; return True
            
            if not self.GPIO.input(KEY_RIGHT_PIN): b=KEY_RIGHT_PIN; return True
            
            if not self.GPIO.input(KEY_DOWN_PIN): b=KEY_DOWN_PIN; return True

            if not self.GPIO.input(KEY_PRESS_PIN): b=KEY_PRESS_PIN; return True
            
            if not self.GPIO.input(KEY1_PIN): b=KEY1_PIN; return True
            
            if not self.GPIO.input(KEY2_PIN): b=KEY2_PIN; return True
            
            if not self.GPIO.input(KEY3_PIN): b=KEY3_PIN; return True

        return False

    def getKey(self):
        """get key without waiting; return current key pressed"""

        a = h.checkSocketINput()
        if a:
            return a

        if not self.GPIO.input(KEY_UP_PIN): return KEY_UP_PIN

        if not self.GPIO.input(KEY_LEFT_PIN): return KEY_LEFT_PIN
            
        if not self.GPIO.input(KEY_RIGHT_PIN): return KEY_RIGHT_PIN
            
        if not self.GPIO.input(KEY_DOWN_PIN): return KEY_DOWN_PIN

        if not self.GPIO.input(KEY_PRESS_PIN): return KEY_PRESS_PIN
            
        if not self.GPIO.input(KEY1_PIN): return KEY1_PIN
            
        if not self.GPIO.input(KEY2_PIN): return KEY2_PIN
            
        if not self.GPIO.input(KEY3_PIN): return KEY3_PIN

        return False
        
    def showImage(self, directory):
        self.fullClear(self.draw)
        bmp = Image.open(directory)
        self.image.paste(bmp, (0,0))
        self.screenShow()

    def showImage2(self, rawImage):
        self.fullClear(self.draw)
        self.image.paste(rawImage, (0,0))
        self.screenShow()

    def fullClear(self, draw):
        draw.rectangle((0, 0, 200, 100), fill=1)
        return True

    def screenShow(self, *args, flipped=False, stream=True):

        if stream:

            buffered = BytesIO()
            
            invimage = ImageOps.invert(self.image.convert('L'))
            invimage.save(buffered, format="JPEG")

            img_str = base64.b64encode(buffered.getvalue())

            h.sockStream.queue.append(img_str)
            h.sockStream.mostRecentImage = img_str

        if not config["menu"]["disableWrite"]:
            if flipped:
                a = ImageOps.flip(self.image)
                self.disp.ShowImage(self.disp.getbuffer(a.transpose(Image.FLIP_LEFT_RIGHT)))
            else:
                self.disp.ShowImage(self.disp.getbuffer(self.image))

        return self.disp.getbuffer(self.image)
