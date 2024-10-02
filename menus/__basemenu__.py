import threading
from PIL import Image, ImageDraw, ImageFont, ImageOps
from time import sleep    

# this is accessed as .gui
class BasePwnhyveScreen():
    def __init__(self, draw:ImageDraw, disp, image:Image):

        self.disp = disp
        self.draw = draw
        self.image = image

        return None
    
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

                if key == 'u':
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

                elif key == 'd':
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

                elif key == 'r':
                    sl += 1
                    if sl > len(self.whole) + len(self.deci):
                        sl = len(self.whole) + len(self.deci)
                
                elif key == 'l':
                    sl -= 1
                    if 0 >= sl:
                        sl = 0

                elif key == 'p':
                    return self.ttF()
    
    class slider:
        def __init__(self, tpil, caption:str,
                      min_:int=0, start:int=50, max_:int=100, _step=1) -> None:
            draw,disp,image = tpil.__getDDI__()

            self.caption = caption
            self.min = min_
            self.max = max_
            self.value = start
            self._step = _step

            assert start >= min_ and max_ >= start

            self.draw = draw
            self.disp = disp
            self.image = image

            self._bigFont = ImageFont.truetype('core/fonts/roboto.ttf', 12)
            self.captFont = ImageFont.truetype('core/fonts/haxrcorp-4089.ttf', 12)

            self.alive = True
            pass

        def start(self):

            while True:
                self.disp.fullClear(self.draw)

                pointerX, pointerY = 12+self.value, 20
                self.draw.rectangle([(12, 23), (116, 24)])
                self.draw.rectangle([(pointerX, pointerY), (pointerX+4, pointerY+8)], fill='WHITE')

                self.draw.text([64, 16], str(self.value), font=self._bigFont, anchor="ms") #value

                if self.caption != None:
                    self.draw.text([64, 40], self.caption, font=self._bigFont, anchor="ms") # caption

                self.disp.screenShow()

                # end of drawing, wait for key

                key = self.disp.waitForKey(debounce=True)
                if key == 'r':
                    self.value += self._step
                    if self.value > self.max:
                        self.value = self.max

                elif key == 'l':
                    self.value -= self._step
                    if self.min > self.value:
                        self.value = self.min
                
                elif key == 'u':
                    self.value += self._step * 10
                    if self.value > self.max:
                        self.value = self.max

                elif key == 'd':
                    self.value -= self._step * 10
                    if self.min > self.value:
                        self.value = self.min

                elif key == 'p':
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

            self.text = ""
            self.close = False
            self.draw = draw
            self.disp = disp
            self.autoUpdate = autoUpdate
            self.image = image
            self.updateBool = False

            self.cFont = ImageFont.truetype('core/fonts/haxrcorp-4089.ttf', round(self.disp.height / 8))
            self.flipped = flipped

            self.stopWriting = False

            self.oldText = ""
            self.started = False

            threading.Thread(target=self.start, daemon=True).start()

        def update(self):
            self.updateBool = True

        def forceUpdate(self):
            self.updateBool = True
            sleep(0.1)

        def start(self, divisor:int=32, maxRows=6):
            textOld = None
            tempText = []

            if self.started: print("[+] screenConsole thread was called after being already being started"); return

            self.started = True

            while 1:
                if open("./core/temp/threadQuit", "r").read().strip() == "1": self.close = True; open("./core/temp/threadQuit", "w").write("0")

                if self.autoUpdate == False:
                    while self.updateBool != True:
                        pass
                    self.updateBool = False
                #print(self.text) # dee bug
                if self.close:
                    self.disp.fullClear(self.draw)
                    self.disp.screenShow(self.disp, self.image, flipped=self.flipped, stream=True)
                    return # request to close
                
                if self.stopWriting: sleep(0.5); continue


                # to prevent drawing more lines than display res, remove first line of console if the len of a newline split list is equal to 5
                if len(self.text.split("\n")) > maxRows: # the maxRows here is max lines
                    textList = self.text.split("\n") # split into list
                    while len(textList)-1 > maxRows: # the 12 here is max rows
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

                if self.text != self.oldText:
                    self.disp.fullClear(self.draw)
                    self.draw.text((2, 1), self.text, fill='WHITE', font=self.cFont, spacing=1) # console
                    self.disp.screenShow(flipped=self.flipped, stream=True)
                
                self.oldText = self.text

        def exit(self):
            self.close = True
            sleep(0.1)

        def close(self):
            self.exit()
        
        def quit(self):
            self.exit()

        def addText(self, stri:str):
            self.text += stri+"\n"

        def clearText(self):
            self.text = ""

    def getItems(self, plugins, currentSelection, rows=5):

        listToPrint = plugins[currentSelection:currentSelection+rows]

        return listToPrint
    
    def enterText(self, kbRows=["qwertyuiopasdfghjklzxcvbnm", "qwertyuiopasdfghjklzxcvbnm".upper(), "1234567890", "!@#$%^&*()_-+={}\\;',./"],
                   flipped=False, secret=False, prefix=None, suffix=None):
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

        rowIndex = 0
        characterIndex = 0

        font = ImageFont.truetype('core/fonts/haxrcorp-4089.ttf', 16)

        while True:

            striShown = prefix + compiledStri + suffix

            if len(striShown) > 16:
                v = [str(x) for x in striShown]
                while len(v) != 16:
                    v.pop() 

            self.disp.fullClear(self.draw) # clear

            self.draw.rectangle([(0, 14), (128, 16)], fill='WHITE', outline=255) # draw the line spliting the text and the keyboard

            if not secret:
                self.draw.text((2,2), compiledStri, fill='WHITE', outline=255, font=font)
            else:
                self.draw.text((2,2), ''.join(["*" for _ in compiledStri]), fill='WHITE', outline=255, font=font)


            ### draws the kb
                
            maxPixelX = 116
            textX, textY = 8, 20 # starting coordinate of the first letter

            for x in kbRows[rowIndex]: # for every character in our row..
                if textX >= maxPixelX: # if we already maxed out the display length...
                    # start a new line
                    maxPixelX -= 4 # reduce our max pixel X since we're doing halfgrid
                    textX = 8 + 4 # \r
                    textY += 12 # \n

                if x != chosenKey: # if this character we're writing isn't chosen..
                    self.draw.text((textX, textY), x, fill='WHITE', outline=255, font=font) # write it normally

                else: # if it is chosen...
                    self.draw.rectangle([(textX-2, textY-1), (textX+8, textY+12)], fill='BLACK', outline=255) # write it with inverted colors..
                    self.draw.text((textX, textY), x, fill='WHITE', outline=255, font=font) # .. and with a box around it 

                textX += 10 # move right for our next character

            # show compiled image
            self.disp.screenShow(self.disp, self.image, flipped=flipped, stream=True)


            ##

            key = self.disp.waitForKey(debounce=True)

            if key == 'd': # moving on the x and y plane

                """
                stringsI += 1 if stringsI != len(kbRows)-1 else 0
                chars = kbRows[stringsI]

                if keyI > len(chars):
                    keyI = len(chars)
                """

                if rowIndex != len(kbRows):
                    rowIndex += 1

                if characterIndex > len(kbRows[rowIndex]):
                    characterIndex = len(kbRows[rowIndex])

            elif key == 'u':

                if rowIndex != 0:
                    rowIndex -= 1

                if characterIndex > len(kbRows[rowIndex]):
                    characterIndex = len(kbRows[rowIndex])

                """
                stringsI -= 1 if stringsI != 0 else 0
                chars = kbRows[stringsI]

                if keyI > len(chars):
                    keyI = len(chars)
                """

            elif key == 'r': # moving on the y plane
                characterIndex += 1 if characterIndex != len(kbRows[rowIndex]) -1  else 0

            elif key == 'l': # moving on the y plane
                characterIndex -= 1 if characterIndex != 0 else 0

            elif key == 'p':
                compiledStri += chosenKey

            elif key == '3':
                return prefix + compiledStri + suffix
            elif key == '2':
                compiledStri += " " #space
            elif key == '1':
                compiledStri = compiledStri[:-1]

            # calculate our chosen key
                
            try:
                chosenKey = kbRows[rowIndex][characterIndex]
            except IndexError:
                characterIndex = 0
                chosenKey = kbRows[rowIndex][characterIndex]

    def menu(self, choices, disableBack=False):
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