from PIL import Image, ImageDraw, ImageFont, ImageOps
from core.plugin import BasePwnhyveScreen
from time import sleep


class Screen(BasePwnhyveScreen):
    def getItems(self, plugins, currentSelection, amount=5):
    
        listToPrint = plugins[currentSelection:currentSelection+amount]

        return listToPrint

    def menu(self, choices,
            flipped=False, icons={"..": "./core/icons/back.bmp"}, caption=None, disableBack=False):
        xCoord = 5
        yCoord = 5
        currentSelection = 0 # index of programs list
        maxLNprint = 5
        cleanScrollNum = 0
        currentSelOld = 0

        if len(choices) == 0:
            choices = ["empty"]
        if "" in choices:
            choices.remove("") # any whitespace

        if not disableBack:
            if ".." in choices:
                choices.remove("..")
            choices.insert(0, "..")

        while 1:
            yCoordBefore = yCoord
            selection = list(choices)[currentSelection]

            self.disp.fullClear(self.draw)

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
                self.draw.rectangle([(0, 0), (255, 13)], fill=1, outline=255)
                self.draw.text(
                    self.resizeCoords2Res([8,1]), 
                    caption, 
                    font=ImageFont.truetype('core/fonts/tahoma.ttf', 11)
                    )
                
                yCoord += 14

            self.display(choices, currentSelection, icons)

            yCoord = yCoordBefore # set our y coord

            self.disp.screenShow(flipped=flipped, stream=True)

            # button stuff

            while True:
                key = self.disp.waitForKey()

                if key == False: continue

                if key == 'down': # button is released
                    if not flipped:
                        if currentSelection != (len(choices) - 1):
                            currentSelection += 1
                        else:
                            currentSelection = 0
                    else:
                        if currentSelection != 0:
                            currentSelection -= 1
                        else:
                            currentSelection = len(choices) - 1
                            
                    break
                    #print("down")

                if key == 'up': # button is released
                    if flipped:
                        if currentSelection != (len(choices) - 1):
                            currentSelection += 1
                        else:
                            currentSelection = 0
                    else:
                        if currentSelection != 0:
                            currentSelection -= 1
                        else:
                            currentSelection = len(choices) - 1

                    break
                    #print("Up")

                if key == 'press' or key == 'right': # button is released
                    if choices[currentSelection] == "..": return None
                    return choices[currentSelection]
                    #print("center")

                if key == '2': # button is released
                    flipped = not flipped
                    break
                    #print("center")

                if not disableBack:
                    if key == 'left': return None

    def display(self, moduleList, currentSelection, icons):

        listToPrint = self.getItems(moduleList, currentSelection, amount=10)
        
        selection = moduleList[currentSelection]

        yCoord = 2
        iconSize = self.disp.iconSize
        fontSize = self.disp.recommendedFontSize
        iconSizePadding = 4 if self.disp.height == 64 else 8

        white = 'WHITE' if not self.disp.invertedColor else 'BLACK'
        black = 'BLACK' if not self.disp.invertedColor else 'WHITE'

        unselectedFont = ImageFont.truetype('core/fonts/monospace.ttf', fontSize)
        selectedFont   = ImageFont.truetype('core/fonts/monospace.ttf', fontSize)
        flipperSelection = Image.open('./core/fonts/selection.bmp')


        for text in list(listToPrint): # do draw
            rIcoX, rIcoY = 2 + (2 if self.disp.width == 128 else 0), 1

            icofile = icons.get(text, "./core/icons/missing.bmp")
            rico = Image.open(icofile)

            if self.disp.invertedColor:
                rico = ImageOps.invert(rico.convert('L'))

            if selection != text: # if our selection isnt the text iter gave us
                self.draw.text(
                    (iconSizePadding+iconSize+self.rzc2r(4), yCoord),
                      text.replace("_", " "), fill=white, outline=white, 
                      font=unselectedFont) # draw black text over rectangle
                
            else: # it is our selection
                self.draw.rounded_rectangle([self.rzxyr((0, yCoord-2)), self.rzxyr((120, 13 + yCoord))], fill=1, outline=white, radius=3) # draw colored rectangle first
                self.draw.text((iconSizePadding+iconSize+self.rzc2r(4), yCoord), text.replace("_", " "), fill=white, outline=white, font=selectedFont) # draw black text over rectangle
            

            ico = rico.resize((iconSize,iconSize))
            self.image.paste(ico, (rIcoX, rIcoY+yCoord))

            yCoord += (iconSize) + 6

        yCoord = 3

        while self.disp.height >= yCoord:
            self.draw.rectangle((
                self.rzxyr((124, yCoord)), self.rzxyr((124, yCoord))),
                fill=white)
            yCoord += 3

        selBoxY = (round(self.disp.height / len(moduleList)) * currentSelection)
        selBoxHeight = round(self.disp.height / len(moduleList))
        selBox = self.draw.rectangle(((self.rzc2r(123), selBoxY), (self.rzc2r(125), selBoxY+selBoxHeight)), fill=white, outline=white)

def createSelection(display, text, xCoord, yCoord, selected=0, **kwargs):
    coords = (xCoord, yCoord)
    display.text(coords, text, fill=selected, **kwargs)
    return coords
