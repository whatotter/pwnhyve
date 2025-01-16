from PIL import Image, ImageFont, ImageOps, ImageDraw
from time import sleep
from core.utils import redir, config
from core.plugin import pwnhyveMenuLoader
from io import BytesIO
import base64
from core.displayDrivers.sh1106 import *
import gpiozero as gpioz
import core.displayDrivers.__helper__ as h
import core.displayDrivers.SH1106.SH1106m as SH1106

#GPIO define
RST_PIN        = 22
CS_PIN         = 24
DC_PIN         = 18

KEY_UP_PIN     = 6 
KEY_DOWN_PIN   = 19
KEY_LEFT_PIN   = 5
KEY_RIGHT_PIN  = 26
KEY_PRESS_PIN  = 13

KEY1_PIN       = 21
KEY2_PIN       = 20
KEY3_PIN       = 16

programCoords = {}
s = pwnhyveMenuLoader()
screens = s.modules

class DisplayDriver():
    def __init__(self, screen) -> None:
        print("[DISPLAY] initalizing display driver...", end="")

        self.pinout = { # gpio pins are the buttons, like joystick, side buttons, etc.
            'up': KEY_UP_PIN, # up (joystick)
            'down': KEY_DOWN_PIN, # down (joystick)
            'left': KEY_LEFT_PIN, # left (joystick)
            'right': KEY_RIGHT_PIN, # right (joystick)
            'press': KEY_PRESS_PIN, # press (joystick)
            '1': KEY1_PIN, # key1
            '2': KEY2_PIN, # key2
            '3': KEY3_PIN, # key3
        }

        self.gpiodev = {
            
        }

        self.disp = SH1106.SH1106()
        self.disp.Init()
        self.disp.clear()

        self.image = Image.new('1', (self.disp.width, self.disp.height), "WHITE") # init display
        self.draw = ImageDraw.Draw(self.image) # dsiayp

        # properties of display
        self.hasColor = False
        self.invertedColor = True
        self.width = self.disp.width
        self.height = self.disp.height
        self.name = "SH1106"
        # these are variables due to PPI differences
        self.recommendedFontSize = 16 # font size for decent readability
        self.iconSize = 8

        self.keysBeingHeld = []

        print("/ [GPIO] initalizing GPIO pins...")
        for gpioPin in self.pinout: # init gpio
            print("| [GPIO] initializing GPIO pin {}...".format(self.pinout[gpioPin]), end="")

            self.gpiodev[self.pinout[gpioPin]] = gpioz.DigitalInputDevice(self.pinout[gpioPin], pull_up=True, active_state=None)

            print("initalized")

        print("\\ [GPIO] done initalizing GPIO pins.\n")

        self.gui = screen.Screen(self.draw, self, self.image)
        
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
    
    def dgRead(self, pin):
        return self.gpiodev[pin].value

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
            c = self.checkIfKey(key=x)
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

            if self.dgRead(KEY_UP_PIN): a = "up"; b=KEY_UP_PIN; break #ku

            if self.dgRead(KEY_LEFT_PIN): a = "left"; b=KEY_LEFT_PIN; break #kl
            
            if self.dgRead(KEY_RIGHT_PIN): a = "right"; b=KEY_RIGHT_PIN; break #kr
            
            if self.dgRead(KEY_DOWN_PIN): a = "down"; b=KEY_DOWN_PIN; break #kd

            if self.dgRead(KEY_PRESS_PIN): a = 'press'; b=KEY_PRESS_PIN; break #jp
            
            if self.dgRead(KEY1_PIN): a = '1'; b=KEY1_PIN; break #k1
            
            if self.dgRead(KEY2_PIN): a = '2'; b=KEY2_PIN; break #k2
            
            if self.dgRead(KEY3_PIN): a = '3'; b=KEY3_PIN; break #k3

            sleep(0.01) # prevent really fast ticks

        if debounce:
            downcycles = 0
            while self.dgRead(b):
                downcycles += 1
                if downcycles >= 100:
                    self.keysBeingHeld.append(a)
                    return a # it's being held down for a reason
                
                sleep(0.005)

        return a

    def checkIfKey(self, key=False):
        """check if there is a key being pressed"""

        if key != False:
            return self.dgRead(self.pinout[key])

        a = h.checkSocketINput()
        b = None
        if a:
            return True

        if key == False:
            if self.dgRead(KEY_UP_PIN): b=KEY_UP_PIN; return True

            if self.dgRead(KEY_LEFT_PIN): b=KEY_LEFT_PIN; return True
            
            if self.dgRead(KEY_RIGHT_PIN): b=KEY_RIGHT_PIN; return True
            
            if self.dgRead(KEY_DOWN_PIN): b=KEY_DOWN_PIN; return True

            if self.dgRead(KEY_PRESS_PIN): b=KEY_PRESS_PIN; return True
            
            if self.dgRead(KEY1_PIN): b=KEY1_PIN; return True
            
            if self.dgRead(KEY2_PIN): b=KEY2_PIN; return True
            
            if self.dgRead(KEY3_PIN): b=KEY3_PIN; return True

        return False

    def getKey(self, debounce=False):
        """return current key pressed"""

        a = h.checkSocketINput()
        if a:
            return a

        keyPressed = False
        if self.dgRead(KEY_UP_PIN): keyPressed = 'up'
        if self.dgRead(KEY_LEFT_PIN): keyPressed = 'left'
        if self.dgRead(KEY_RIGHT_PIN): keyPressed = 'right'
        if self.dgRead(KEY_DOWN_PIN): keyPressed = 'down'
        if self.dgRead(KEY_PRESS_PIN): keyPressed = 'press'
        if self.dgRead(KEY1_PIN): keyPressed = '1'
        if self.dgRead(KEY2_PIN): keyPressed = '2'
        if self.dgRead(KEY3_PIN): keyPressed = '3'

        if debounce and keyPressed:
            downcycles = 0
            while self.dgRead(self.pinout[keyPressed]):
                downcycles += 1
                if downcycles >= 100:
                    self.keysBeingHeld.append(a)
                    return a # it's being held down for a reason
                
                sleep(0.005)

        return keyPressed
        
    def showImage(self, directory):
        self.fullClear(self.draw)
        bmp = Image.open(directory)

        invbmp = ImageOps.invert(bmp.convert('L'))

        self.image.paste(invbmp, (0,0))
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
