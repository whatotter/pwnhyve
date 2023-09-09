from PIL import Image, ImageFont, ImageOps
from time import sleep
from core.utils import getChunk
import string
from core.plugin import load
from json import loads
from io import BytesIO
import base64

#GPIO define
RST_PIN        = 25
CS_PIN         = 8
DC_PIN         = 24

KEY_UP_PIN     = 6 
KEY_DOWN_PIN   = 19
KEY_LEFT_PIN   = 5
KEY_RIGHT_PIN  = 26
KEY_PRESS_PIN  = 13

KEY1_PIN       = 21
KEY2_PIN       = 20
KEY3_PIN       = 16

programCoords = {}

class customizable:
    cleanScroll = True
    onlyPrefix = False
    selectionBackgroundWidth = 200

    def onIdle(display):
        pass

class usbRunPercentage:
    def __init__(self, draw, disp, image,
            consoleFont=ImageFont.truetype('core/fonts/roboto.ttf', 10),
            percentageFont=ImageFont.truetype('core/fonts/roboto.ttf', 12),
            flipped=False
        ):
        self.percentage = 0
        self.text = "..."
        self.close = False
        self.draw = draw
        self.disp = disp
        self.image = image

        self.cFont = consoleFont
        self.pFont = percentageFont
        self.flipped = flipped

    def start(self, divisor:int=13):
        percentageOld = None
        textOld = None
        tempText = []

        percentageX, percentageY = 94,24
        while 1:
            #print(self.text) # dee bug
            if open("./core/temp/threadQuit", "r").read().strip() == "1": self.close = True; open("./core/temp/threadQuit", "w").write("0")
            if self.close: return # request to close


            # to prevent drawing more lines than display res, remove first line of console if the len of a newline split list is equal to 5
            if len(self.text.split("\n")) > 5:
                textList = self.text.split("\n") # split into list
                while len(textList) > 5:
                    textList.pop(0) # pop first index

                self.text = '\n'.join(textList) # join it back together with newlines

            tempText.clear()
            for line in self.text.split("\n"): # make sure text doesnt go over divider
                if len(line) > divisor: # will go over divider
                    #lineList = [str(x) for x in line] # turn into list
                    lineWordList = line.split(" ")
                    lines = []
                    tempLine = ""

                    #while len(lineList) != divisor: # while len isnt divisor
                        #lineList.pop(len(lineList) - 1) # remove last char

                    while len(lineWordList) != 0: # while our words that are in a list isnt empty
                        #print(lineWordList) # debug
                        for x in lineWordList.copy(): # copy to prevent errors
                            if len(tempLine) + len(x) > divisor: # if the len of the things are over divisor, start removing
                                if len(x) > divisor: # if the entire word is over divisor
                                    #print("word over divisor")
                                    xLst = [str(y) for y in x] # turn it into a list
                                    while len(xLst) != divisor - 2: # while its not divisor
                                        xLst.pop() # pop last
                                    xLst.append("..") # to show it's been cut
                                    x2 = ''.join(xLst) # turn it back into str

                                    lines.append(x2) # append cut word into lines
                                    lineWordList.remove(x) # remove full word
                                    tempLine = "" # clear temp line
                                    break # break off

                                lines.append(tempLine)
                                tempLine = ""
                                break

                            tempLine += x + " " # just add our words n stuff

                            lineWordList.remove(x) # prevent going over already processed word

                    # just for multiline pretty
                    """
                    lines[0] = "/" + lines[0]
                    for x in range(1, len(lines) - 1):
                        lines[x] = '|'+lines[x]
                    lines[-1] = '\\'+lines[-1]
                    """

                    #lineList.append("..") # add elipses to show it's been cut
                    #line = ''.join(lineList) # re-merge list

                    line = '\n'.join(lines) # re-merge list

                tempText.append(line) # append to list to join later
            
            self.text = '\n'.join(tempText) # join lines from list

            """
            if self.percentage == percentageOld:
                if textOld == self.text:
                    continue # if nothing has changed, continue to prevent drawing too much # this does not work
            
            textOld = self.text # set old vars
            percentageOld = self.percentage          
            """

            if self.percentage < 100: # to have 90% and 100% in the middle
                percentageX = 94
            else:
                percentageX = 96

            fullClear(self.draw)

            self.draw.rectangle([(86, 0), (88, 64)], fill=0, outline=255) # divider
            
            self.draw.text((percentageX, percentageY), "{}%".format(self.percentage), fill=0, outline=255, font=self.pFont) # percentage

            self.draw.text((4, 4), self.text, fill=0, outline=255, font=self.cFont) # console
            
            screenShow(self.disp, self.image, flipped=self.flipped, stream=True)

    def exit(self):
        self.close = True

    def addText(self, stri:str):
        self.text += stri+"\n"

    def clearText(self):
        self.text = ""

    def setPercentage(self, percent:int):
        self.percentage = percent

class screenConsole:
    def __init__(self, draw, disp, image,
            consoleFont=ImageFont.truetype('core/fonts/roboto.ttf', 10),
            flipped=False, autoUpdate=True
        ):
        self.text = "..."
        self.close = False
        self.draw = draw
        self.disp = disp
        self.autoUpdate = autoUpdate
        self.image = image
        self.updateBool = False

        self.cFont = consoleFont
        self.flipped = flipped
        self.stopWriting = False

    def update(self):
        self.updateBool = True

    def start(self, divisor:int=25):
        textOld = None
        tempText = []

        while 1:
            if open("./core/temp/threadQuit", "r").read().strip() == "1": self.close = True; open("./core/temp/threadQuit", "w").write("0")

            if self.autoUpdate == False:
                while self.updateBool != True:
                    pass
                self.updateBool = False
            #print(self.text) # dee bug
            if self.close:
                fullClear(self.draw)
                screenShow(self.disp, self.image, flipped=self.flipped, stream=True)
                return # request to close
            
            if self.stopWriting: sleep(0.5); continue


            # to prevent drawing more lines than display res, remove first line of console if the len of a newline split list is equal to 5
            if len(self.text.split("\n")) > 5: # the 5 here is max lines
                textList = self.text.split("\n") # split into list
                while len(textList) > 12: # the 12 here is max letters
                    textList.pop(0) # pop first index

                self.text = '\n'.join(textList) # join it back together with newlines

            tempText.clear()
            for line in self.text.split("\n"): # make sure text doesnt go over divider
                if len(line) > divisor: # will go over divider
                    #lineList = [str(x) for x in line] # turn into list
                    lineWordList = line.split(" ")
                    lines = []
                    tempLine = ""

                    #while len(lineList) != divisor: # while len isnt divisor
                        #lineList.pop(len(lineList) - 1) # remove last char

                    while len(lineWordList) != 0: # while our words that are in a list isnt empty
                        #print(lineWordList) # debug
                        for x in lineWordList.copy(): # copy to prevent errors
                            if len(tempLine) + len(x) > divisor: # if the len of the things are over divisor, start removing
                                if len(x) > divisor: # if the entire word is over divisor
                                    #print("word over divisor")
                                    xLst = [str(y) for y in x] # turn it into a list
                                    while len(xLst) != divisor - 2: # while its not divisor
                                        xLst.pop() # pop last
                                    xLst.append("..") # to show it's been cut
                                    x2 = ''.join(xLst) # turn it back into str

                                    lines.append(x2) # append cut word into lines
                                    lineWordList.remove(x) # remove full word
                                    tempLine = "" # clear temp line
                                    break # break off

                                lines.append(tempLine)
                                tempLine = ""
                                break

                            tempLine += x + " " # just add our words n stuff

                            lineWordList.remove(x) # prevent going over already processed word

                    # just for multiline pretty
                    """
                    lines[0] = "/" + lines[0]
                    for x in range(1, len(lines) - 1):
                        lines[x] = '|'+lines[x]
                    lines[-1] = '\\'+lines[-1]
                    """

                    #lineList.append("..") # add elipses to show it's been cut
                    #line = ''.join(lineList) # re-merge list

                    line = '\n'.join(lines) # re-merge list

                tempText.append(line) # append to list to join later
            
            self.text = '\n'.join(tempText) # join lines from list

            """
            if self.percentage == percentageOld:
                if textOld == self.text:
                    continue # if nothing has changed, continue to prevent drawing too much # this does not work
            
            textOld = self.text # set old vars
            percentageOld = self.percentage          
            """

            fullClear(self.draw)

            self.draw.text((4, 4), self.text, fill=0, outline=255, font=self.cFont) # console

            screenShow(self.disp, self.image, flipped=self.flipped, stream=True)

    def exit(self):
        self.close = True

    def addText(self, stri:str):
        self.text += stri+"\n"

    def clearText(self):
        self.text = ""

def checkSocketINput():
    gpio = None
    with open("/tmp/socketGPIO", "r") as f:
        gpio = f.read()
    
    open("/tmp/socketGPIO", "w").write("") # leave blank (worst way to do this probably)

    if gpio == "":
        return False
    else:
        if gpio in ["up", "left", "right", "down", "1", "2", "3", "press"]:
            buttons = {
            "up": 6 ,
            "down": 19,
            "left": 5,
            "right": 26,
            "press": 13,
            "1": 21,
            "2": 20,
            "3": 16,
            }
            return int(buttons[gpio])
            
def waitForKey(GPIO, debounce=False):
    """
    wait for key press and return the key pressed

    debounce waits for the key to be released
    """

    a = None

    while 1: # wait for key press
        sockGPIO = checkSocketINput()
        if not sockGPIO:
            pass
        else:
            a = sockGPIO
            break

        if not GPIO.input(KEY_UP_PIN): a = KEY_UP_PIN; break

        if not GPIO.input(KEY_LEFT_PIN): a = KEY_LEFT_PIN; break
        
        if not GPIO.input(KEY_RIGHT_PIN): a = KEY_RIGHT_PIN; break
        
        if not GPIO.input(KEY_DOWN_PIN): a = KEY_DOWN_PIN; break

        if not GPIO.input(KEY_PRESS_PIN): a = KEY_PRESS_PIN; break
        
        if not GPIO.input(KEY1_PIN): a = KEY1_PIN; break
        
        if not GPIO.input(KEY2_PIN): a = KEY2_PIN; break
        
        if not GPIO.input(KEY3_PIN): a = KEY3_PIN; break

        sleep(0.05) # prevent really fast ticks

    if debounce:
        while checkIfKey(GPIO):
            pass
        sleep(0.01)

    return a

def checkIfKey(GPIO):
    """check if there is a key being pressed"""

    a = checkSocketINput()
    if a:
        return True

    if not GPIO.input(KEY_UP_PIN): return True

    if not GPIO.input(KEY_LEFT_PIN): return True
        
    if not GPIO.input(KEY_RIGHT_PIN): return True
        
    if not GPIO.input(KEY_DOWN_PIN): return True

    if not GPIO.input(KEY_PRESS_PIN): return True
        
    if not GPIO.input(KEY1_PIN): return True
        
    if not GPIO.input(KEY2_PIN): return True
        
    if not GPIO.input(KEY3_PIN): return True

    return False

def getKey(GPIO):
    """get key without waiting; return current key pressed"""

    a = checkSocketINput()
    if a:
        return a

    if not GPIO.input(KEY_UP_PIN): return KEY_UP_PIN

    if not GPIO.input(KEY_LEFT_PIN): return KEY_LEFT_PIN
        
    if not GPIO.input(KEY_RIGHT_PIN): return KEY_RIGHT_PIN
        
    if not GPIO.input(KEY_DOWN_PIN): return KEY_DOWN_PIN

    if not GPIO.input(KEY_PRESS_PIN): return KEY_PRESS_PIN
        
    if not GPIO.input(KEY1_PIN): return KEY1_PIN
        
    if not GPIO.input(KEY2_PIN): return KEY2_PIN
        
    if not GPIO.input(KEY3_PIN): return KEY3_PIN

    return False

def showImage(disp, directory):
    img = Image.new('1', (disp.width, disp.height), 255)  # 255: clear the frame
    bmp = Image.open(directory)
    img.paste(bmp, (0,5))
    # Himage2=Himage2.rotate(180) 	
    disp.ShowImage(disp.getbuffer(img))

def createSelection(display, text, xCoord, yCoord, selected=0, **kwargs):
    coords = (xCoord, yCoord)
    display.text(coords, text, fill=selected, **kwargs)
    return coords

def fullClear(draw):
    draw.rectangle((0, 0, 200, 100), fill=1)
    return True

def screenShow(disp, image, flipped=False, stream=False):

    if flipped:
        a = ImageOps.flip(image)
        disp.ShowImage(disp.getbuffer(a.transpose(Image.FLIP_LEFT_RIGHT)))
    else:
        disp.ShowImage(disp.getbuffer(image))

    if stream:

        buffered = BytesIO()
        
        image.save(buffered, format="JPEG")

        img_str = base64.b64encode(buffered.getvalue())

        with open("/tmp/base64Data", "w") as f:
            f.write(img_str.decode('ascii'))
            f.flush()

    return disp.getbuffer(image)

def enterText(draw, disp, image, GPIO, kbRows=["qwertyuiopasdfghjklzxcvbnm", "qwertyuiopasdfghjklzxcvbnm".upper(), "1234567890", "!@#$%^&*()_-+={}\\;',./"], font=ImageFont.truetype('core/fonts/tahoma.ttf', 11), flipped=False, secret=False):
    """
    super wip
    
    draw, disp, image, GPIO are all required

    kbRows: the rows/set of characters to let the user choose from - default is alphanumeric characters and symbols

    font: the default font to use for the letters, etc.

    flipped: if the keyboard should be flipped (used for when the user isn't using the display in normal orentiation)

    secret: if the text being entered should be classified - example, a password
    """
    chosenKey = "q"
    compiledStri = ""
    keyI = 0
    stringsI = 0
    chars = [x for x in kbRows[stringsI]]

    while True:

        striShown = compiledStri

        if len(striShown) > 16:
            v = [str(x) for x in striShown]
            while len(v) != 16:
                v.pop() 

        fullClear(draw)

        draw.rectangle([(0, 14), (128, 16)], fill=0, outline=255)

        if not secret:
            draw.text((2,2), compiledStri, fill=0, outline=255, font=font)
        else:
            draw.text((2,2), ''.join(["*" for _ in compiledStri]), fill=0, outline=255, font=font)

        textX, textY = 8, 20

        for x in chars:
            if textX >= 116:
                textX = 8
                textY += 12

            if x != chosenKey:
                draw.text((textX, textY), x, fill=0, outline=255, font=font)
            else:
                draw.rectangle([(textX-2, textY-1), (textX+8, textY+12)], fill=0, outline=255)
                draw.text((textX, textY), x, fill=1, outline=255, font=font)

            textX += 10

        # show compiled image
        screenShow(disp, image, flipped=flipped, stream=True)


        ##

        key = waitForKey(GPIO, debounce=True)

        if key == KEY_DOWN_PIN: # moving on the x and y plane
            stringsI += 1 if stringsI != len(kbRows)-1 else 0
            chars = kbRows[stringsI]

            if keyI > len(chars):
                keyI = len(chars)

        elif key == KEY_UP_PIN:
            stringsI -= 1 if stringsI != 0 else 0
            chars = kbRows[stringsI]

            if keyI > len(chars):
                keyI = len(chars)

        elif key == KEY_RIGHT_PIN: # moving on the y plane
            keyI += 1 if keyI != len(chars) -1  else 0

        elif key == KEY_LEFT_PIN: # moving on the y plane
            keyI -= 1 if keyI != 0 else 0

        elif key == KEY_PRESS_PIN:
            compiledStri += chosenKey

        elif key == KEY3_PIN:
            return compiledStri
        elif key == KEY2_PIN:
            compiledStri += "" #space
        elif key == KEY1_PIN:
            compiledStri = compiledStri[:-1]

        try:
            chosenKey = chars[keyI]
        except IndexError:
            keyI = 0
            chosenKey = chars[keyI]

def menu(draw, disp, image, choices, GPIO,
          gpioPins={'KEY_UP_PIN': 6,'KEY_DOWN_PIN': 19,'KEY_LEFT_PIN': 5,'KEY_RIGHT_PIN': 26,'KEY_PRESS_PIN': 13,'KEY1_PIN': 21,'KEY2_PIN': 20,'KEY3_PIN': 16,},
            flipped=False, menuType=loads(open("./config.json", "r").read())["screenType"], menus=load(folder="menus"), caption=None, disableBack=False):
    xCoord = 5
    yCoord = 5
    currentSelection = 0 # index of programs list
    maxLNprint = 5
    cleanScrollNum = 0
    currentSelOld = 0

    if len(choices) == 0:
        raise KeyError("no choices provided")
    if "" in choices:
        choices.remove("") # any whitespace

    while 1:
        yCoordBefore = yCoord
        selection = list(choices)[currentSelection]

        fullClear(draw)

        if currentSelection >= maxLNprint:
            if currentSelection != currentSelOld:
                cleanScrollNum += 1
        else:
            if currentSelection != currentSelOld:
                cleanScrollNum -= 1

        currentSelOld = currentSelection

        if caption == None:
            pass
        else:
            draw.rectangle([(0, 0), (255, 13)], fill=1, outline=255)
            draw.text([1,1], caption, font=ImageFont.truetype('core/fonts/tahoma.ttf', 11))
            yCoord += 14

        if menuType in menus:
            b = menus[menuType]

            listToPrint = b[2].screen.getItems([choices, yCoord, xCoord, currentSelection, selection])

            b[2].screen.display([draw, disp, image, GPIO, list(listToPrint), choices, yCoord, xCoord, currentSelection, selection, {}])


        yCoord = yCoordBefore # set our y coord

        screenShow(disp, image, flipped=flipped, stream=True)

        # button stuff

        while True:
            key = waitForKey(GPIO, debounce=True)

            print(key)

            if key == False: continue

            if key == gpioPins['KEY_DOWN_PIN']: # button is released
                if not flipped:
                    if currentSelection != (len(choices) - 1):
                        currentSelection += 1
                else:
                    if currentSelection != 0:
                        currentSelection -= 1
                        
                break
                #print("down")

            if key == gpioPins['KEY_UP_PIN']: # button is released
                if flipped:
                    if currentSelection != (len(choices) - 1):
                        currentSelection += 1
                else:
                    if currentSelection != 0:
                        currentSelection -= 1

                break
                #print("Up")

            if key == gpioPins['KEY_PRESS_PIN']: # button is released
                return choices[currentSelection]
                #print("center")

            if key == 20: # button is released
                flipped = not flipped
                break
                #print("center")

            if not disableBack:
                if key == gpioPins['KEY_LEFT_PIN']: return None