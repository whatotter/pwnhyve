import math
import os
import threading
from PIL import Image, ImageDraw, ImageFont, ImageOps
from time import sleep
from core.pil_simplify import tinyPillow
from textwrap import wrap

# this is accessed as .gui
class BasePwnhyveScreen():
    def __init__(self, draw:ImageDraw, disp, image:Image):

        self.disp = disp
        self.draw = draw
        self.image = image

        return None
    
    class carouselMenu:
        def __init__(self, tpil:tinyPillow) -> None:
            self.tpil = tpil
            self.height = tpil.disp.height
            self.width = tpil.disp.width
            self.YCoord = self.height - round(self.height/6)
            self.fontSize = self.tpil.disp.recommendedFontSize
            self.font = ImageFont.truetype('core/fonts/monospace.ttf', self.fontSize)
            pass

        def draw(self, text, caption, wrapText=False):
            charWidth = round(self.width/4)

            self.tpil.clear()

            self.tpil.text((0,0),
                        '\n'.join(
                            wrap(text, width=charWidth)
                            ) if wrapText else text, 
                        font=self.font)

            y = self.YCoord
            self.tpil.rect((0, self.YCoord), (self.width, self.YCoord), color='WHITE') # draw line
            self.tpil.rect((0, self.YCoord+1), (self.width, self.height), color='BLACK') # draw footer

            y += 1

            self.tpil.loadImage("./core/icons/buttons/left.bmp", [2,y+2],
                                inverted=self.tpil.disp.invertedColor)
            
            self.tpil.loadImage("./core/icons/buttons/right.bmp", [self.width-10, y+2],
                                inverted=self.tpil.disp.invertedColor)
            
            self.tpil.text(
                (
                    round(self.width/2),
                    y
                ), caption, anchor="ma", fontSize=self.tpil.disp.recommendedFontSize
            )

            self.tpil.show()
        
    class keyLegend:
        def __init__(self, tpil:tinyPillow, legend:dict) -> None:
            """
            create a key legend at the bottom of the screen (takes 10 pixels)

            Parameters:
                legend: a dictionary of keys, and what they do
                      e.g. {"left": "back", "press": "ok", "right": "next"}
            """
            
            self.legend = legend
            self.tpil = tpil
            self.height = tpil.disp.height
            self.width = tpil.disp.width
            self.YCoord = self.height - round(self.height/6)

        def draw(self):
            y = self.YCoord # Y coord we're gonna be working with
            x = 0 # X coord we're gonna be working with

            self.tpil.rect((0, self.YCoord), (self.width, self.YCoord), color='WHITE') # draw line
            
            y += 1

            # draw each legend
            for key, legendText in self.legend.items():
                if key+".bmp" in os.listdir("./core/icons/buttons"):
                    self.tpil.loadImage("./core/icons/buttons/{}.bmp".format(key), [x,y+2],
                                        inverted=self.tpil.disp.invertedColor)
                    
                    x += 12 # move X by 12
                    self.tpil.text((x, y), legendText,
                                fontSize=self.tpil.disp.recommendedFontSize)
                    
                    x += (5 * len(legendText)) + 6
                    #x += 6*len(legendText) # X padding

    class setFloat:
        def __init__(self, tpil, caption:str,
                      _min:float=100.000, start:str="314.314", _max:float=500.000, wholePlaces=3, decimalPlaces=3) -> None:
            draw,disp,image = tpil.__getDDI__()
            
            self.caption = caption
            self.min = _min
            self.max = _max
            self.value = start
            self.floatval = float(start)

            self.draw = draw
            self.disp = disp
            self.image = image

            self.whole = [x for x in start.split(".")[0]]
            self.deci = [x for x in start.split(".")[1]]
            
            self.wholePlaces = wholePlaces
            self.decimalPlaces = decimalPlaces

            self._bigFont = ImageFont.truetype('core/fonts/roboto.ttf', 10)

            self.alive = True
            pass

        def downtriangle(self, x,y):
            self.draw.polygon([(x,y), (x+8, y), (x+4,y+6)])

        def uptriangle(self, x,y):
            self.draw.polygon([(x,y), (x+8, y), (x+4,y-6)])

        def ttF(self):
            return float(''.join(self.whole) + "." + ''.join(self.deci))

        def start(self):

            # fucking mess
            sl = 0
            selector = 0
            isWhole = True

            while True:
                self.disp.fullClear(self.draw)

                # 128/2= 64
                # 64/2 = 32

                diffr = 4
                rectWidth = 8

                self.draw.rectangle([(64, 31), (64, 32)])

                n = 0

                wholePlaceX = 68-diffr
                for x in range(self.wholePlaces):
                    self.draw.text(
                        [wholePlaceX-rectWidth, 24], 
                        text=self.whole[len(self.whole)-(1+x)] # reverse the list
                        )
                    
                    if len(self.whole)-(1+x) == sl:
                        self.draw.rectangle([(wholePlaceX-2-rectWidth, 23), (wholePlaceX, 36)])
                        self.downtriangle(wholePlaceX-rectWidth-1, 38)
                        self.uptriangle(wholePlaceX-rectWidth-1, 21)

                        selector = len(self.whole)-(1+x)
                        isWhole = True

                    wholePlaceX -= 10
                    assert 64 > wholePlaceX
                    n += 1

                deciPlaceX = 64+diffr
                
                for x in range(self.decimalPlaces):
                    self.draw.text([deciPlaceX, 24], text=self.deci[x])

                    if n == sl:
                        self.draw.rectangle([(deciPlaceX-2, 23), (deciPlaceX+rectWidth, 36)])
                        self.downtriangle(deciPlaceX-1, 38)
                        self.uptriangle(deciPlaceX-1, 21)

                        selector = x
                        isWhole = False

                    deciPlaceX += 10
                    assert 128 > deciPlaceX
                    n += 1

                if self.caption != None:
                    self.draw.text([64, 54], self.caption, font=self._bigFont, anchor="ms") # caption

                self.disp.screenShow()

                # end of drawing, wait for key

                key = self.disp.waitForKey(debounce=True)

                if key == 'up':
                    if isWhole:
                        if int(self.whole[selector]) >= 9:
                            continue

                        self.whole[selector] = str(int(self.whole[selector]) + 1)
                    else:
                        if int(self.deci[selector]) >= 9:
                            continue
                        
                        self.deci[selector] = str(int(self.deci[selector]) + 1)

                    if self.ttF() >= self.max:
                        self.whole = [x for x in str(self.max).split(".")[0]]

                elif key == 'down':
                    if isWhole:
                        if 0 >= int(self.whole[selector]):
                            continue

                        self.whole[selector] = str(int(self.whole[selector]) - 1)
                    else:
                        if 0 >= int(self.deci[selector]):
                            continue
                        
                        self.deci[selector] = str(int(self.deci[selector]) - 1)

                    if self.min >= self.ttF():
                        self.whole = [x for x in str(self.min).split(".")[0]]

                elif key == 'right':
                    sl += 1
                    if sl > len(self.whole) + len(self.deci):
                        sl = len(self.whole) + len(self.deci)
                
                elif key == 'left':
                    sl -= 1
                    if 0 >= sl:
                        sl = 0

                elif key == 'press':
                    return self.ttF()
    
    class slider:
        def __init__(self, tpil, caption:str,
                      minimum:int=0, start:int=-1, maximum:int=100,
                      step=1, ndigits=1, bigstep=10) -> None:
            draw,disp,image = tpil.__getDDI__()

            if start == -1:
                start = round(maximum/2)

            self.caption = caption
            self.min = minimum
            self.max = maximum
            self.value = start
            self._step = step

            assert start >= minimum and maximum >= start

            self._draw = draw
            self.disp = disp
            self.image = image
            self.ndigits = ndigits
            self.bigstep = bigstep

            self._bigFont = ImageFont.truetype('core/fonts/roboto.ttf', 12)
            self.captFont = ImageFont.truetype('core/fonts/monospace.ttf', 12)

            self.alive = True
            pass

        def draw(self):

            while True:
                self.value = round(self.value, self.ndigits)
                self.disp.fullClear(self._draw)

                # slider
                self._draw.rectangle([(0, 23), (128, 24)])

                # slider thumb
                pointerY = 20
                pointerX = self.value * (self.disp.width/self.max)
                self._draw.rectangle([(pointerX, pointerY), (pointerX+4, pointerY+8)])

                self._draw.text([64, 16], str(self.value), font=self._bigFont, anchor="ms") #value

                if self.caption != None:
                    self._draw.text([64, 42], self.caption, font=self._bigFont, anchor="ms") # caption

                self.disp.screenShow()

                # end of drawing, wait for key

                key = self.disp.waitForKey(debounce=True)
                if key == 'right':
                    self.value += self._step
                    if self.value > self.max:
                        self.value = self.max

                elif key == 'left':
                    self.value -= self._step
                    if self.min > self.value:
                        self.value = self.min
                
                elif key == 'up':
                    self.value += self.bigstep
                    if self.value > self.max:
                        self.value = self.max

                elif key == 'down':
                    self.value -= self.bigstep
                    if self.min > self.value:
                        self.value = self.min

                elif key == 'press':
                    return self.value

    class usbRunPercentage:
        def __init__(self, tpil,
                consoleFont=ImageFont.truetype('core/fonts/roboto.ttf', 10),
                percentageFont=ImageFont.truetype('core/fonts/roboto.ttf', 12),
                flipped=False
            ):
            draw,disp,image = tpil.__getDDI__()

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

                self.update()
                sleep(0.05)

        def update(self):
            percentageX, percentageY = 94,24

            if self.percentage < 100: # to have 90% and 100% in the middle
                percentageX = 94
            else:
                percentageX = 96
                
            self.disp.fullClear(self.draw)

            self.draw.rectangle([(86, 0), (88, 64)], fill=0, outline=255) # divider
            
            self.draw.text((percentageX, percentageY), "{}%".format(self.percentage), fill=0, outline=255, font=self.pFont) # percentage

            self.draw.text((4, 4), self.text, fill=0, outline=255, font=self.cFont) # console
            
            self.disp.screenShow(flipped=self.flipped, stream=True)

        def exit(self):
            self.close = True

        def addText(self, stri:str):
            if self.text == "...":
                self.text = ""

            self.text += stri+"\n"
            self.update()

        def clearText(self):
            self.text = ""
            self.update()

        def setPercentage(self, percent:int):
            self.percentage = percent
            print("set percentage to {}".format(percent))
            self.update()

    class screenConsole:
        def __init__(self, tpil,
                consoleFont=None,
                flipped=False, autoUpdate=True
            ):

            draw,disp,image = tpil.__getDDI__()

            self.tpil = tpil
            self.text = ""
            self.close = False
            self.draw = draw
            self.disp = disp
            self.autoUpdate = autoUpdate
            self.image = image
            self.updateBool = True

            self.cFont = ImageFont.truetype('core/fonts/monospace.ttf', round(self.disp.height / 4))
            self.flipped = flipped

            self.stopWriting = False

            self.oldText = ""
            self.started = False

            #threading.Thread(target=self.start, daemon=True).start()

        def checkWrap(self, string):
            letters = 0
            strings = []
            currentString = ""
            for letter in string:
                if 128 > self.cFont.getlength(currentString + letter) and letter != "\n":
                    currentString += letter
                else:
                    strings.append(currentString.strip())
                    currentString = letter

            strings.append(currentString)

            return '\n'.join(strings)


        def update(self):
            self.tpil.clear()
            
            self.tpil.text((0, 1),
                            self.checkWrap(self.text), 
                            font=self.cFont, spacing=1) # console
            
            self.tpil.show()

        def forceUpdate(self):
            self.update()

        def start(self, divisor:int=32, maxRows=6):
            textOld = None
            tempText = []

            if self.started: print("[+] screenConsole thread was called after being already being started"); return

            self.started = True

            while 1:
                #print(self.text) # dee bug
                if self.close:
                    self.disp.fullClear(self.draw)
                    self.disp.screenShow(self.disp, self.image, flipped=self.flipped, stream=True)
                    return # request to close
                
                if self.stopWriting: sleep(0.5); continue

                if self.text != self.oldText or self.updateBool:
                    self.tpil.clear()
                    
                    self.tpil.text((2, 1),
                                   '\n'.join(wrap(self.text, replace_whitespace=False, drop_whitespace=False, width=round(self.disp.width/4))), 
                                   font=self.cFont, spacing=1) # console
                    
                    self.tpil.show()
                    self.updateBool = False
                
                self.oldText = self.text

        def exit(self):
            self.close = True
            sleep(0.1)

        def close(self):
            self.exit()
        
        def quit(self):
            self.exit()

        def setText(self, stri:str):
            self.text = stri
            self.update()

        def addText(self, stri:str):
            self.text += stri+"\n"
            self.update()

        def clearText(self):
            self.text = ""
            self.update()

    def getItems(self, plugins, currentSelection, rows=5):

        listToPrint = plugins[currentSelection:currentSelection+rows]

        return listToPrint
    
    def enterText(self, tpil, kbRows=[["1234567890-=~", "qwertyuiop[]", "asdfghjkl;'", "zxcvbnm,./", " "], ["!@#$%^&*()_+~", "QWERTYUIOP{}", "ASDFGHJKL:\"", "ZXCVBNM<>?", " "]],
                   secret=False, prefix=None, suffix=None):
        """
        super wip

        kbRows: the rows/set of characters to let the user choose from - default is alphanumeric characters and symbols

        font: the default font to use for the letters, etc.

        flipped: if the keyboard should be flipped (used for when the user isn't using the display in normal orentiation)

        secret: if the text being entered should be classified - example, a password
        """

        prefix = "" if prefix is None else prefix
        suffix = "" if suffix is None else suffix

        chosenKey = "q"
        compiledStri = ""

        characterIndex = 0
        keyRowIndex = 0
        keyRowBlobIndex = 0

        spaceBar = "[____________]"

        font = ImageFont.truetype('core/fonts/monospace.ttf', 16)
        tinyFont = ImageFont.truetype('core/fonts/monospace.ttf', 11)
        modifier = False

        slice1 = 0
        slice2 = len(prefix + suffix)
        while True:

            preStri = (prefix + compiledStri + suffix)
            striShown = preStri[slice1:slice2]

            if font.getlength(striShown) >= 120 and not modifier:
                while font.getlength(striShown) >= 120:
                    slice1 += 1
                    striShown = preStri[slice1:slice2]

            tpil.clear() # clear

            tpil.rect((0, 12), (128, 12)) # draw the line spliting the text and the keyboard

            if modifier:
                tpil.text((110,56), "ALT", font=tinyFont)

            if not secret:
                tpil.text((2,0), striShown, font=font)
            else:
                tpil.text((2,0), ''.join(["*" for _ in striShown]), font=font)

            textLength = font.getlength(striShown)+2
            tpil.rect((textLength, 2), (textLength, 10))


            ### draws the kb
                
            maxPixelX = 116
            textX, textY = 4, 14 # starting coordinate of the first letter
            textXOffset = 4
            kbRow = kbRows[keyRowBlobIndex]

            for keyRow in kbRow: # iterate over key rows (imagine the 3 key rows on your usual keyboard)
                div = round(maxPixelX / len(keyRow))
                for char in keyRow: # for every character in our row..
                    if char == "~": char = "<="
                    if char == " ": char = spaceBar

                    if char != chosenKey: # if this character we're writing isn't chosen..
                        tpil.text((textX, textY), char, font=font) # write it normally

                    else: # if it is chosen...
                        tpil.rect(
                            (textX-2, textY), 
                            (textX + font.getlength(char), textY+10), 
                            color='WHITE'
                            ) # draw box
                        
                        tpil.text((textX, textY), char, font=font, color="BLACK") # draw text after box 

                    textX += div # move right for our next character

                nextKeyRowIndex = kbRow.index(keyRow) + 1
                try:
                    nextKeyRowLength = len(kbRow[nextKeyRowIndex])
                except:
                    nextKeyRowIndex = 0

                if len(keyRow) != nextKeyRowLength: # next row is gonna be a different size
                    textX = 4 + textXOffset # do magic

                maxPixelX -= textXOffset
                textXOffset += 4
                textY += 10


            # show compiled image
            tpil.show()

            key = tpil.waitForKey(debounce=True)

            if key == 'down': # moving on the x and y plane

                """
                stringsI += 1 if stringsI != len(kbRows)-1 else 0
                chars = kbRows[stringsI]

                if keyI > len(chars):
                    keyI = len(chars)
                """

                keyRowIndex += 1
                #characterIndex -= 1
                if keyRowIndex > len(kbRow)-1 : keyRowIndex = len(kbRow)-1

            elif key == 'up':

                keyRowIndex -= 1
                if 0 > keyRowIndex: keyRowIndex = 0

                """
                stringsI -= 1 if stringsI != 0 else 0
                chars = kbRows[stringsI]

                if keyI > len(chars):
                    keyI = len(chars)
                """

            elif key == 'right': # moving on the y plane
                if modifier:
                    slice1 += 1 if slice1 != len(preStri) else 0
                else:
                    characterIndex += 1 if characterIndex != len(kbRow[keyRowIndex]) -1 else 0

            elif key == 'left': # moving on the y plane
                if modifier:
                    ignoreOver = True
                    slice1 -= 1 if slice1 != 0 else 0
                    slice2 += 1 if slice1 != 0 else 0
                else:
                    characterIndex -= 1 if characterIndex != 0 else 0

            elif key == 'press':
                if chosenKey == "<=":
                    compiledStri = compiledStri[:-1]
                elif chosenKey[0] == "[" and chosenKey[-1] == "]":
                    compiledStri += " "
                else:
                    compiledStri += chosenKey

                modifier = False
                slice2 += 1

            elif key == '3':
                return prefix + compiledStri + suffix
            elif key == '2':
                if keyRowBlobIndex >= len(kbRows)-1:
                    keyRowBlobIndex = 0
                else:
                    keyRowBlobIndex += 1
            elif key == '1':
                modifier = not modifier

            # calculate our chosen key
                
            try:
                chosenKey = kbRow[keyRowIndex][characterIndex]

            except IndexError:
                characterIndex = len(kbRow[keyRowIndex])-1 # we went over
                chosenKey = kbRow[keyRowIndex][characterIndex]

            if chosenKey == "~": chosenKey = "<="
            if chosenKey == " ": chosenKey = spaceBar

    def menu(self, choices, disableBack=False, 
             highlight=[], # won't be used here
             index=None, # won't be used here either
             ):
        currentSelection = 0

        if len(choices) == 0:
            choices = ["empty"]
        if "" in choices:
            choices.remove("") # any whitespace

        if not disableBack:
            if ".." in choices:
                choices.remove("..")
            choices.insert(0, "..")
            
        listToPrint = self.getItems(choices, currentSelection)
        selection = choices[currentSelection]

        xCoord = 2
        yCoord = 2

        font = ImageFont.truetype('core/fonts/roboto.ttf', 11)

        for text in list(listToPrint): # do draw
            if selection != text: # if our selection isnt the text iter gave us
                #createSelection(draw, text, xCoord, yCoord, selected=0, font=font) # draw it normally
                self.draw.text((xCoord, yCoord), text.replace("_", " "), fill='BLACK', outline=255, font=font) # draw black text over rectangle
            else: # it is our selection
                self.draw.rectangle([(0, yCoord), (255, 13 + yCoord)], fill='BLACK', outline=255) # draw colored rectangle first
                self.draw.text((xCoord, yCoord), text.replace("_", " "), fill='WHITE', outline=255, font=font) # draw black text over rectangle

                    
            yCoord += 14

    def display(self, moduleList, currentSelection, icons):

        listToPrint = self.getItems(moduleList, currentSelection)
        selection = moduleList[currentSelection]


        xCoord = 2
        yCoord = 2

        font = ImageFont.truetype('core/fonts/roboto.ttf', 11)

        for text in list(listToPrint): # do draw
            if selection != text: # if our selection isnt the text iter gave us
                #createSelection(draw, text, xCoord, yCoord, selected=0, font=font) # draw it normally
                self.draw.text((xCoord, yCoord), text.replace("_", " "), fill='BLACK', outline=255, font=font) # draw black text over rectangle
            else: # it is our selection
                self.draw.rectangle([(0, yCoord), (255, 13 + yCoord)], fill='BLACK', outline=255) # draw colored rectangle first
                self.draw.text((xCoord, yCoord), text.replace("_", " "), fill='WHITE', outline=255, font=font) # draw black text over rectangle

                    
            yCoord += 14

    def resizeCoordinate2Res(self, coordinate, axis='x'):
        # for displays that aren't 128x64

        if axis.lower() == 'x':
            return round(coordinate*(self.disp.width) / 128)
        elif axis.lower() == 'y':
            return round(coordinate*(self.disp.height) / 64)
        else:
            raise ValueError("axis \"{}\" is not 'x' or 'y'".format(axis))
        
    def resizeCoords2Res(self, xy):
        # resize both x and y from a list
        return (
            self.resizeCoordinate2Res(xy[0]),
            self.resizeCoordinate2Res(xy[1])
        )
    
    def rzxyr(self, *args, **kwargs):
        # shorthand for resizeCoords2Res
        return self.resizeCoords2Res(*args, **kwargs)
    
    def rzc2r(self, *args, **kwargs):
        # shorthand for resizeCoordinate2Res
        return self.resizeCoordinate2Res(*args, **kwargs)