import os
import time
from typing import Union
from PIL import Image, ImageDraw, ImageFont
from time import sleep
from core.pil_simplify import tinyPillow
from textwrap import wrap

# this is accessed as .gui
class BasePwnhyveScreen():
    
    def __init__(self, draw:ImageDraw, disp, image:Image):

        self.disp = disp
        self.draw = draw
        self.image = image

        self.tpil = tinyPillow(draw, disp, image, gui=self)

        return None
    
    def carouselMenu(self, *args, **kwargs) -> carouselMenu:
        """
        a simple carousel menu
        ** beware this is nonblocking, you must manage redraws and key inputs yourself **
        
        Example:
            >>> menu = tpil.gui.carouselMenu()
            >>> menu.draw("main console text", "caption")
            >>> if tpil.waitForKey() == "right":
            >>>     # user scrolled right...
            >>> ...
        """

        return carouselMenu(self.tpil)

    def keyLegend(self, *args, **kwargs) -> keyLegend:
        """
        create a key legend at the bottom of the screen (takes 10 pixels)
        ** BEWARE THIS IS NOT AUTOMATICALLY REDRAWN, YOU MUST REDRAW IT YOURSELF USING `this.draw()` **

        Args:
            legend: a dictionary of keys, and what they do
                    e.g. {"left": "back", "press": "ok", "right": "next"}
                    icons will be automagically filled out
        """

        return keyLegend(self.tpil, *args, **kwargs)

    def setFloat(self, *args, **kwargs) -> float:
        """
        set individual values in a number, e.g. like sdrpp's frequency changer
        typically used for exactly that, setting radio frequencies

        Args:
            caption (str): caption to tell the user (what this is for)
            _min (float): minimum value the user can pick
            start (str): starting value; must be a string because python doesn't like 300.000 and turns it into 300.0
            _max (float): maximum value the user can pick
            wholePlaces (int): amount of whole number places there is
            decimalPlaces (int): amount of decimal places there is 

        Returns:
            float: the result the user picked
        """

        ab = setFloat(self.tpil, *args, **kwargs)
        return ab.start()

    def slider(self, *args, **kwargs) -> Union[float,int]:
        """
        a simple integer slider

        Args:
            caption (str): caption to show the user (e.g. what the user is picking)
            minimum (int or float): minimum the slider can go to
            start (int or float): where the slider starts (must be between minimum and maximum) (e.g. 50)
            maximum (int or float): maximum the slider can go to
            step (int or float): steps the slider goes, when the user goes left and right (right being +)
            bigstep (int or float): steps the slider goes when the uses up and down (up being +)
            ndigits (int): number of digits to round to, if the value is a float

        Returns:
            float or int: the value the user chose
        """

        ab = slider(self.tpil, *args, **kwargs)
        return ab.draw() # why it's in two bits, no clue

    def usbRunPercentage(self, **kwargs) -> usbRunPercentage:
        """
        issue a console with a 80/20 split, where 20% of the screen is taken up by \
        a percentage

        this is kinda depreciated, i don't like using it
        """
        return usbRunPercentage(self.tpil, **kwargs)

    def screenConsole(self, **kwargs) -> screenConsole:
        """
        issue a terminal-like ui to the user - only text allowed
        """

        return screenConsole(self.tpil, **kwargs)

    def toast(self, text:str, xy1:list, xy2:list, timeout:int=-1, textYOffset:int=0):
        """
        toast the user with a notification, and go away when the user clicks a key

        @text: text of the notification
        @xy1: top-left XY coord in list format [X,Y], for the body
        @xy2: bottom-right XY coord in list format [X,Y], for the body
        @timeout: timeout before hiding toast box - defaults to -1 (user intervention)
        @textYOffset: text offset from top of the body (e.g. margin-top)

        """
        originalImage = self.image.tobytes('raw', '1')
        #originalImage = self.image.tobitmap()
        # since we're overlaying on an image that we want to restore after \
        # a bit, we save the image before we do anything with it to load \
        # it back after

        # draw toast box
        self.draw.rounded_rectangle(([xy1[0]-1, xy1[1]-1], [xy2[0]+1, xy2[1]+1]), fill=1, radius=3)
        self.draw.rounded_rectangle((xy1, xy2), radius=3)

        self.tpil.text([xy1[0]+4, xy1[1]+2+textYOffset], text, font=ImageFont.truetype('core/fonts/Tiny5-Regular.ttf', 8))

        self.tpil.show(clear=False)

        # wait for user to read, or something
        if 0 > timeout:
            self.tpil.waitForKey() # let user continue when they want
        else:
            time.sleep(timeout) # wait for toast to go away

        # load back the image we saved earlier
        imageFB = Image.frombytes('1', (self.image.width, self.image.height), originalImage, 'raw', '1')
        self.image.paste(imageFB, (0,0))

        # show it
        self.tpil.show(clear=False)

    def getItems(self, plugins, currentSelection, rows=5):

        listToPrint = plugins[currentSelection:currentSelection+rows]

        return listToPrint
    
    def enterText(self, kbRows=[["1234567890-=~", "qwertyuiop[]", "asdfghjkl;'", "zxcvbnm,./", " %"], ["!@#$%^&*()_+~", "QWERTYUIOP{}", "ASDFGHJKL:\"", "ZXCVBNM<>?", " "]],
                   secret=False, prefix=None, suffix=None):
        """
        allows the user to enter text and returns the string

        @kbRows: the rows/set of characters to let the user choose from - default is alphanumeric characters and symbols
        @font: the default font to use for the letters, etc.
        @secret: if the text being entered should be classified - example, a password
        @prefix: string to prefix user's text with - for example, a date
        @suffix: string to suffix user's text with - for example, a file extension
        """

        prefix = "" if prefix is None else prefix
        suffix = "" if suffix is None else suffix

        chosenKey = "q"
        compiledStri = ""

        characterIndex = 0
        keyRowIndex = 0
        keyRowBlobIndex = 0

        spaceBar = "[_________]"
        enter = "[<]"

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

            self.tpil.clear() # clear

            self.tpil.rect((0, 12), (128, 12)) # draw the line spliting the text and the keyboard

            if modifier:
                self.tpil.text((110,56), "ALT", font=tinyFont)

            if not secret:
                self.tpil.text((2,0), striShown, font=font)
            else:
                self.tpil.text((2,0), ''.join(["*" for _ in striShown]), font=font)

            textLength = font.getlength(striShown)+2
            self.tpil.rect((textLength, 2), (textLength, 10))


            ### draws the kb
                
            maxPixelX = 116
            textX, textY = 4, 14 # starting coordinate of the first letter
            textXOffset = 4
            kbRow = kbRows[keyRowBlobIndex]

            for keyRow in kbRow: # iterate over key rows (imagine the 3 key rows on your usual keyboard)
                div = round(maxPixelX / len(keyRow))
                for char in keyRow: # for every character in our row..

                    if keyRowBlobIndex == 0: # text, not symbols
                        if char == "~": char = "<="
                        elif char == "%": 
                            char = enter
                        elif char == " ": 
                            char = spaceBar
                            div = font.getlength(char)+2

                    if char != chosenKey: # if this character we're writing isn't chosen..
                        self.tpil.text((textX, textY), char, font=font) # write it normally

                    else: # if it is chosen...
                        self.tpil.rect(
                            (textX-2, textY), 
                            (textX + font.getlength(char), textY+10), 
                            color='WHITE'
                            ) # draw box
                        
                        self.tpil.text((textX, textY), char, font=font, color="BLACK") # draw text after box 

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
            self.tpil.show()

            key = self.tpil.waitForKey(debounce=True)

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
                elif chosenKey[0] == "[" and chosenKey[-1] == "]" and chosenKey[1] == "_":
                    compiledStri += " "
                elif chosenKey == enter:
                    return prefix + compiledStri + suffix
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
            if chosenKey == "%": chosenKey = enter

    def menu(self, choices, disableBack=False, 
             highlight=[], # won't be used here
             index=None, # won't be used here either
             ) -> str:
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
        """
        redraw the menu

        Args:
            text (str): text to draw
            caption (str): text to draw at the bottom of the screen
        """
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
                                '\n'.join(wrap(self.text, replace_whitespace=False, drop_whitespace=False, width=round(self.disp.width/2))), 
                                font=self.cFont, spacing=1) # console
                
                self.tpil.show()
                self.updateBool = False
            
            self.oldText = self.text

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

        if len(self.text.split("\n")) > 4:
            self.text = '\n'.join(self.text.split("\n")[4:])

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

        if len(self.text.split("\n")) > 7:
            a = self.text.split("\n")
            a.pop(0)
            
            self.text = '\n'.join(a)

        self.update()

    def clearText(self):
        self.text = ""
        self.update()