from PIL import Image, ImageFont
from time import sleep

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
            
def waitForKey(GPIO):
    while 1: # wait for key press
        if not GPIO.input(KEY_UP_PIN): break
    
        if not GPIO.input(KEY_LEFT_PIN): break
            
        if not GPIO.input(KEY_RIGHT_PIN): break
            
        if not GPIO.input(KEY_DOWN_PIN): break

        if not GPIO.input(KEY_PRESS_PIN): break
            
        if not GPIO.input(KEY1_PIN): break
            
        if not GPIO.input(KEY2_PIN): break
            
        if not GPIO.input(KEY3_PIN): break

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

def menu(draw, disp, image, choices, GPIO, gpioPins,
 cleanScroll=True, onlyPrefix=False, selectionBackgroundWidth=200, font=None, flipped=False):
    xCoord = 5
    yCoord = 5
    currentSelection = 0 # index of programs list
    selectedPrefix = ">"
    maxLNprint = 5
    cleanScrollNum = 0
    scrollChunks = []
    currentSelOld = 0
    while 1:
        yCoordBefore = yCoord
        selection = list(choices)[0]

        fullClear(draw)

        if currentSelection >= maxLNprint:
            if currentSelection != currentSelOld:
                cleanScrollNum += 1
        else:
            if currentSelection != currentSelOld:
                cleanScrollNum -= 1

        currentSelOld = currentSelection

        if not cleanScroll:
            for chunk in scrollChunks:
                if selection in chunk:
                    listToPrint = chunk
        else:
            a = list(choices)
            listToPrint = []

            for _ in range(currentSelection):
                if cleanScrollNum != 0:
                    a.pop(0)

            for i in a:
                listToPrint = a[:5]

        for text in list(listToPrint): # do draw
            if selection != text:
                returnedCoords = createSelection(draw, text, xCoord, yCoord, selected=0, font=font)
                programCoords[text] = returnedCoords
            else:
                if not onlyPrefix:
                    draw.rectangle([(0, yCoord), (selectionBackgroundWidth, 13 + yCoord)], fill=0, outline=255)
                    draw.text((xCoord, yCoord), text, fill=1, outline=255, font=font)
                    programCoords[text] = (xCoord, yCoord)
                else:
                    #createSelection(draw, selection, xCoord, yCoord, selected=1, font=font) # clear it
                    draw.text((xCoord, yCoord), selectedPrefix+text, fill=0, outline=255, font=font)
                    programCoords[text] = (xCoord, yCoord)
                    
            yCoord += 14

        yCoord = yCoordBefore

        # button stuff

        if GPIO.input(gpioPins['KEY_DOWN_PIN']): # button is released
            pass # button not pressed
        else: # button is pressed:
            if currentSelection != (len(choices) - 1):
                currentSelection += 1
            #print("down")

        if GPIO.input(gpioPins['KEY_UP_PIN']): # button is released
            pass # not press
        else: # button is pressed:
            if currentSelection != 0:
                currentSelection -= 1
            #print("Up")

        if GPIO.input(gpioPins['KEY_PRESS_PIN']): # button is released
            pass # not press
        else: # button is pressed:
            return choices[currentSelection]
            #print("center")

        if not GPIO.input(gpioPins['KEY_LEFT_PIN']): return None

        if flipped:
            img1 = image.transpose(Image.FLIP_TOP_BOTTOM) # easy read
            disp.ShowImage(disp.getbuffer(img1.transpose(Image.FLIP_LEFT_RIGHT)))
        else:
            disp.ShowImage(disp.getbuffer(image))