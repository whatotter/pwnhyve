from PIL import Image, ImageFont
from time import sleep
from core.utils import getChunk
import string

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

            if self.flipped:
                img1 = self.image.transpose(Image.FLIP_TOP_BOTTOM) # easy read
                self.disp.ShowImage(self.disp.getbuffer(img1.transpose(Image.FLIP_LEFT_RIGHT)))
            else:
                self.disp.ShowImage(self.disp.getbuffer(self.image))

    def exit(self):
        self.close = True

    def addText(self, stri:str):
        self.text += stri+"\n"

    def clearText(self):
        self.text = ""

    def setPercentage(self, percent:int):
        self.percentage = percent

class AsyncMenu:
    def __init__(self, draw, disp, image, GPIO, choices) -> None:
        self.choices = choices

        self.draw = draw
        self.disp = disp
        self.GPIO = GPIO
        self.image = image

        self.selection = None

        self.haltBool = False
        self.halted = False

        self.exited = False
        pass

    def toggleHalt(self):
        self.haltBool = not self.haltBool
        op = not self.halted
        while self.halted != op:
            pass
        return self.halted

    def exit(self):
        self.exited = True

    def menu(self, gpioPins={'KEY_UP_PIN': 6,'KEY_DOWN_PIN': 19,'KEY_LEFT_PIN': 5,'KEY_RIGHT_PIN': 26,'KEY_PRESS_PIN': 13,'KEY1_PIN': 21,'KEY2_PIN': 20,'KEY3_PIN': 16,},
    cleanScroll=True, flipped=False, flipperZeroMenu=True, flipperFontN = ImageFont.truetype('core/fonts/pixelop/PixelOperatorMono.ttf', 16), flipperFontB = ImageFont.truetype('core/fonts/pixelop/PixelOperatorMono-Bold.ttf', 16), font=None, onlyPrefix=False, selectionBackgroundWidth=200, enableIcons=False, iconsDict={}, timeoutCycles=None):
        xCoord = 5
        yCoord = 5
        currentSelection = 0 # index of programs list
        selectedPrefix = ">"
        maxLNprint = 5
        cleanScrollNum = 0
        scrollChunks = []
        currentSelOld = 0
        cycles = 0

        while 1:
            if self.exited: return

            #print(self.choices)
            #print(self.haltBool)
            #print(self.halted)
            #print(currentSelection)
            
            if len(self.choices) == 0:
                while len(self.choices) == 0:
                    pass

            if self.haltBool:
                self.halted = True
                while self.haltBool:
                    if self.exited: return
                    pass
                self.halted = False

            yCoordBefore = yCoord
            selection = list(self.choices)[currentSelection]
            print(selection)
            flipperSelection=Image.open('./core/fonts/selection.bmp')

            fullClear(self.draw)

            if currentSelection >= maxLNprint:
                if currentSelection != currentSelOld:
                    cleanScrollNum += 1
            else:
                if currentSelection != currentSelOld:
                    cleanScrollNum -= 1

            currentSelOld = currentSelection

            if not cleanScroll:
                scrollChunks = getChunk(list(self.choices), 5)
                for chunk in scrollChunks:
                    print(chunk)
                    if selection in ';'.join(chunk): # idek anymore
                        listToPrint = chunk
                        break
            else:
                a = list(self.choices)
                listToPrint = []

                for _ in range(currentSelection):
                    if cleanScrollNum != 0:
                        a.pop(0)

                for i in a:
                    listToPrint = a[:5]

            if flipperZeroMenu:
                yCoord = 1
                listToPrint = [] # clean list to print

                # TODO: figure out something cleaner than this
                try:
                    b4 = list(self.choices)[currentSelection - 1]
                except IndexError: b4=""
                if currentSelection - 1 == -1: b4 = ""
                try:
                    after = list(self.choices)[currentSelection + 1]
                except IndexError: after=""

                listToPrint = [b4, selection, after] 
                #
                #   b4 > pwnagotchi
                #   selection > reboot 
                #   after > shutdown
                #
                #

            for text in list(listToPrint): # do self.draw
                if not flipperZeroMenu:
                    if selection != text: # if our selection isnt the text iter gave us
                        returnedCoords = createSelection(self.draw, text, xCoord, yCoord, selected=0, font=font) # self.draw it normally
                        programCoords[text] = returnedCoords # set the coords for later
                    else: # it is our selection
                        if not onlyPrefix: # if we arent using only prefix
                            self.draw.rectangle([(0, yCoord), (selectionBackgroundWidth, 13 + yCoord)], fill=0, outline=255) # self.draw colored rectangle first
                            self.draw.text((xCoord, yCoord), text, fill=1, outline=255, font=font) # self.draw black text over rectangle
                        else:
                            createSelection(self.draw, selectedPrefix+selection, xCoord, yCoord, selected=0, font=font) # self.draw over it

                        programCoords[text] = (xCoord, yCoord) # add coord
                            
                    yCoord += 14
                else:
                    bigMinimizedText = ''.join([str(x) for x in text][:12]) # usually for big
                    smallMinimizedText = ''.join([str(x) for x in text][:14]) # usually for small

                    xCoord = 4
                    if enableIcons: xCoord += 22

                    if text == "": yCoord += 22; continue
                    icoX, icoY = 4, yCoord + 2

                    try:
                        print(iconsDict)
                        try:
                            ico1 = iconsDict[text]
                        except Exception as e: print(e); ico1 = None
                        #                 ^ v smartest person alive rn
                        if ico1 == None: ico1 = "./core/icons/missing.bmp"

                        ico = Image.open(ico1).resize((16,16))
                    except Exception as e:
                        raise

                    if text == selection:
                        #boxcoords = [(2, 24), (128 - 4, 18 + vars.yCoord)]
                        #self.draw.rectangle(boxcoords, fill=1, outline=0)

                        self.image.paste(flipperSelection, (0,22))

                        createSelection(self.draw, bigMinimizedText, xCoord, yCoord, selected=0, font=flipperFontB) # self.draw over it 
                        if enableIcons: self.image.paste(ico, (icoX, icoY))
                    else:
                        createSelection(self.draw, smallMinimizedText, xCoord, yCoord, selected=0, font=flipperFontN) # draw over it 
                        if enableIcons: self.image.paste(ico, (icoX, icoY))

                    yCoord += 22

            yCoord = yCoordBefore

            # button stuff

            if self.GPIO.input(gpioPins['KEY_DOWN_PIN']): # button is released
                pass # button not pressed
            else: # button is pressed:
                if currentSelection != (len(self.choices) - 1):
                    currentSelection += 1
                #print("down")

            if self.GPIO.input(gpioPins['KEY_UP_PIN']): # button is released
                pass # not press
            else: # button is pressed:
                if currentSelection != 0:
                    currentSelection -= 1
                #print("Up")

            if self.GPIO.input(gpioPins['KEY_PRESS_PIN']): # button is released
                pass # not press
            else: # button is pressed:
                #return self.choices[currentSelection]
                self.selection = self.choices[currentSelection]
                #print("center")

            if not self.GPIO.input(gpioPins['KEY_LEFT_PIN']): self.selection = False; return False

            if timeoutCycles != None:
                if cycles == timeoutCycles:
                    return None
                else:
                    cycles += 1

            if flipped:
                img1 = self.image.transpose(Image.FLIP_TOP_BOTTOM) # easy read
                self.disp.ShowImage(self.disp.getbuffer(img1.transpose(Image.FLIP_LEFT_RIGHT)))
            else:
                self.disp.ShowImage(self.disp.getbuffer(self.image))

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

    def update(self):
        self.updateBool = True

    def start(self, divisor:int=25):
        textOld = None
        tempText = []

        while 1:
            if self.autoUpdate == False:
                while self.updateBool != True:
                    pass
                self.updateBool = False
            #print(self.text) # dee bug
            if self.close: return # request to close


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

            if self.flipped:
                img1 = self.image.transpose(Image.FLIP_TOP_BOTTOM) # easy read
                self.disp.ShowImage(self.disp.getbuffer(img1.transpose(Image.FLIP_LEFT_RIGHT)))
            else:
                self.disp.ShowImage(self.disp.getbuffer(self.image))

    def exit(self):
        self.close = True

    def addText(self, stri:str):
        self.text += stri+"\n"

    def clearText(self):
        self.text = ""
            
def waitForKey(GPIO):
    while 1: # wait for key press
        if not GPIO.input(KEY_UP_PIN): return KEY_UP_PIN
    
        if not GPIO.input(KEY_LEFT_PIN): return KEY_LEFT_PIN
            
        if not GPIO.input(KEY_RIGHT_PIN): return KEY_RIGHT_PIN
            
        if not GPIO.input(KEY_DOWN_PIN): return KEY_DOWN_PIN

        if not GPIO.input(KEY_PRESS_PIN): return KEY_PRESS_PIN
            
        if not GPIO.input(KEY1_PIN): return KEY1_PIN
            
        if not GPIO.input(KEY2_PIN): return KEY2_PIN
            
        if not GPIO.input(KEY3_PIN): return KEY3_PIN

        sleep(0.05) # prevent really fast ticks

    return

def checkIfKey(GPIO):
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

def fullClear(display):
    display.rectangle((0, 0, 200, 100), fill=1)
    return True

def enterText(draw, disp, image, GPIO, top=string.digits+"-=", kb="qwertyuiop{}asdfghjkl;'zxcvbnm,./", font=ImageFont.truetype("./core/fonts/pixelop/PixelOperatorHB8.ttf", 8), flipped=False):
    """
    super wip
    """
    textX, textY = 12, 12
    kbCoords = [0, 24]

    chosenKey = "q"

    while True:

        fullClear(draw)

        compiledStri = ""

        draw.rectangle([(textX+4, textY+0), (200, 16)], fill=0, outline=255)
        draw.text((textX+3, textY+1), compiledStri, fill=1, outline=255, font=font)

        # keyboar

        keyCoords = {}

        for x in top:

            if chosenKey == x:
                draw.rectangle((tuple(kbCoords), (kbCoords[0]+14, kbCoords[1]+10)), fill=1, outline=255)
                draw.text([kbCoords[0] + 2, kbCoords[1]+2], x, fill=0, outline=255, font=font)
            else:
                draw.rectangle((tuple(kbCoords), (kbCoords[0]+14, kbCoords[1]+10)), fill=0, outline=255)
                draw.text([kbCoords[0] + 2, kbCoords[1]+2], x, fill=1, outline=255, font=font)

            keyCoords[x] = kbCoords

            kbCoords[0] += 10

        kbCoords[0] = 0
        kbCoords[1] += 10

        for x in kb:
            if chosenKey == x:
                draw.rectangle((tuple(kbCoords), (kbCoords[0]+14, kbCoords[1]+10)), fill=1, outline=255)
                draw.text([kbCoords[0] + 2, kbCoords[1]+2], x, fill=0, outline=255, font=font)
            else:
                draw.rectangle((tuple(kbCoords), (kbCoords[0]+14, kbCoords[1]+10)), fill=0, outline=255)
                draw.text([kbCoords[0] + 2, kbCoords[1]+2], x, fill=1, outline=255, font=font)

            keyCoords[x] = kbCoords

            kbCoords[0] += 10

            if kbCoords[0] > 110:
                kbCoords[0] = 5
                kbCoords[1] += 10

        """
        kbCoords[0] = 0
        kbCoords[1] += 14

        for x in kb:
            draw.rectangle((tuple(kbCoords), (kbCoords[0]+10, kbCoords[1]+12)), fill=0, outline=255)
            draw.text([kbCoords[0] + 2, kbCoords[1]], x, fill=1, outline=255, font=font)
            keyCoords[x] = kbCoords

            kbCoords[0] += 8
            if kbCoords[0] > 128:
                kbCoords[0] = 0
                kbCoords[1] += 14

            #kbCoords[1] = kbCoords[1] + 4

        """

        # show compiled image
        if flipped:
            img1 = image.transpose(Image.FLIP_TOP_BOTTOM) # easy read
            disp.ShowImage(disp.getbuffer(img1.transpose(Image.FLIP_LEFT_RIGHT)))
        else:
            disp.ShowImage(disp.getbuffer(image))

        while True:
            # 0 is x plane
            # 1 is y plane

            key = getKey(GPIO)

            if key == KEY_DOWN_PIN: # moving on the x and y plane
                currCoords = keyCoords[chosenKey]
                for key in keyCoords:
                    rangeMod = 8
                    if keyCoords[key][1] in range(currCoords[1] - rangeMod, currCoords[1] + rangeMod):
                        #if keyCoords[key][0] == currCoords[0] + 5:
                        chosenKey = key
                        break

            elif key == KEY_RIGHT_PIN: # moving on the y plane
                currCoords = keyCoords[chosenKey]
                for key in keyCoords:
                    if keyCoords[key][0] == currCoords[0] + 10:
                        chosenKey = key
                        break

            elif key == KEY_LEFT_PIN: # moving on the y plane
                currCoords = keyCoords[chosenKey]
                for key in keyCoords:
                    if keyCoords[key][1] == currCoords[1] - 10:
                        chosenKey = key
                        break

def menu(draw, disp, image, choices, GPIO, gpioPins={'KEY_UP_PIN': 6,'KEY_DOWN_PIN': 19,'KEY_LEFT_PIN': 5,'KEY_RIGHT_PIN': 26,'KEY_PRESS_PIN': 13,'KEY1_PIN': 21,'KEY2_PIN': 20,'KEY3_PIN': 16,},
 cleanScroll=True, flipped=False, flipperZeroMenu=True, flipperFontN = ImageFont.truetype('core/fonts/pixelop/PixelOperatorMono.ttf', 16), flipperFontB = ImageFont.truetype('core/fonts/pixelop/PixelOperatorMono-Bold.ttf', 16), font=None, onlyPrefix=False, selectionBackgroundWidth=200, enableIcons=False, iconsDict={}, timeoutCycles=None):
    xCoord = 5
    yCoord = 5
    currentSelection = 0 # index of programs list
    selectedPrefix = ">"
    maxLNprint = 5
    cleanScrollNum = 0
    scrollChunks = []
    currentSelOld = 0
    cycles = 0

    flipperSelection=Image.open('./core/fonts/selection.bmp')

    if len(choices) == 0:
        raise KeyError("no choices provided")

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

        if not cleanScroll:
            scrollChunks = getChunk(list(choices), 5)
            for chunk in scrollChunks:
                print(chunk)
                if selection in ';'.join(chunk): # idek anymore
                    listToPrint = chunk
                    break
        else:
            a = list(choices)
            listToPrint = []

            for _ in range(currentSelection):
                if cleanScrollNum != 0:
                    a.pop(0)

            for i in a:
                listToPrint = a[:5]

        if flipperZeroMenu:
            yCoord = 1
            listToPrint = [] # clean list to print

            # TODO: figure out something cleaner than this
            try:
                b4 = list(choices)[currentSelection - 1]
            except IndexError: b4=""
            if currentSelection - 1 == -1: b4 = ""
            try:
                after = list(choices)[currentSelection + 1]
            except IndexError: after=""

            listToPrint = [b4, selection, after] 
            #
            #   b4 > pwnagotchi
            #   selection > reboot 
            #   after > shutdown
            #
            #

        for text in list(listToPrint): # do draw
            if not flipperZeroMenu:
                if selection != text: # if our selection isnt the text iter gave us
                    returnedCoords = createSelection(draw, text, xCoord, yCoord, selected=0, font=font) # draw it normally
                    programCoords[text] = returnedCoords # set the coords for later
                else: # it is our selection
                    if not onlyPrefix: # if we arent using only prefix
                        draw.rectangle([(0, yCoord), (selectionBackgroundWidth, 13 + yCoord)], fill=0, outline=255) # draw colored rectangle first
                        draw.text((xCoord, yCoord), text, fill=1, outline=255, font=font) # draw black text over rectangle
                    else:
                        createSelection(draw, selectedPrefix+selection, xCoord, yCoord, selected=0, font=font) # draw over it

                    programCoords[text] = (xCoord, yCoord) # add coord
                        
                yCoord += 14
            else:
                bigMinimizedText = ''.join([str(x) for x in text][:12]) # usually for big
                smallMinimizedText = ''.join([str(x) for x in text][:14]) # usually for small

                xCoord = 4
                if enableIcons: xCoord += 22

                if text == "": yCoord += 22; continue
                icoX, icoY = 4, yCoord + 2

                try:
                    #print(iconsDict)
                    try:
                        ico1 = iconsDict[text]
                    except Exception as e: print(e); ico1 = None
                    #                 ^ v smartest person alive rn
                    if ico1 == None: ico1 = "./core/icons/missing.bmp"

                    ico = Image.open(ico1).resize((16,16))
                except Exception as e:
                    raise

                if text == selection:
                    #boxcoords = [(2, 24), (128 - 4, 18 + vars.yCoord)]
                    #draw.rectangle(boxcoords, fill=1, outline=0)

                    image.paste(flipperSelection, (0,22))

                    createSelection(draw, bigMinimizedText, xCoord, yCoord, selected=0, font=flipperFontB) # draw over it 
                    if enableIcons: image.paste(ico, (icoX, icoY))
                else:
                    createSelection(draw, smallMinimizedText, xCoord, yCoord, selected=0, font=flipperFontN) # draw over it 
                    if enableIcons: image.paste(ico, (icoX, icoY))

                yCoord += 22

        yCoord = yCoordBefore

        if flipped:
            img1 = image.transpose(Image.FLIP_TOP_BOTTOM) # easy read
            disp.ShowImage(disp.getbuffer(img1.transpose(Image.FLIP_LEFT_RIGHT)))
        else:
            disp.ShowImage(disp.getbuffer(image))

        # button stuff

        while True:
            key = getKey(GPIO)

            #print(key)

            if key == False: continue

            if key == gpioPins['KEY_DOWN_PIN']: # button is released
                if currentSelection != (len(choices) - 1):
                    currentSelection += 1
                break
                #print("down")

            if key == gpioPins['KEY_UP_PIN']: # button is released
                if currentSelection != 0:
                    currentSelection -= 1
                break
                #print("Up")

            if key == gpioPins['KEY_PRESS_PIN']: # button is released
                return choices[currentSelection]
                #print("center")

            if key == gpioPins['KEY_LEFT_PIN']: return None