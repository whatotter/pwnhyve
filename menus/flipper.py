from PIL import Image, ImageDraw, ImageFont, ImageOps
from core.plugin import BasePwnhyveScreen
from time import sleep


class Screen(BasePwnhyveScreen):
    def getItems(self, plugins, currentSelection):
    
        listToPrint = plugins[currentSelection:currentSelection+5]

        return listToPrint

    def menu(self, choices,
            gpioPins={'KEY_UP_PIN': 6,'KEY_DOWN_PIN': 19,'KEY_LEFT_PIN': 5,'KEY_RIGHT_PIN': 26,'KEY_PRESS_PIN': 13,'KEY1_PIN': 21,'KEY2_PIN': 20,'KEY3_PIN': 16,},
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
                self.draw.text([8,1], caption, font=ImageFont.truetype('core/fonts/tahoma.ttf', 11))
                yCoord += 14

            self.display(choices, currentSelection, icons)

            yCoord = yCoordBefore # set our y coord

            self.disp.screenShow(flipped=flipped, stream=True)

            # button stuff

            while True:
                key = self.disp.waitForKey(debounce=True)

                if key == False: continue

                if key == 'd': # button is released
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

                if key == 'u': # button is released
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

                if key == 'p': # button is released
                    if choices[currentSelection] == "..": return None
                    return choices[currentSelection]
                    #print("center")

                if key == '2': # button is released
                    flipped = not flipped
                    break
                    #print("center")

                if not disableBack:
                    if key == 'l': return None

    def display(self, moduleList, currentSelection, icons):

        listToPrint = self.getItems(moduleList, currentSelection)
        selection = moduleList[currentSelection]

        yCoord = 2

        unselectedFont = ImageFont.truetype('core/fonts/haxrcorp-4089.ttf', 16)
        selectedFont   = ImageFont.truetype('core/fonts/haxrcorp-4089.ttf', 16)
        flipperSelection = Image.open('./core/fonts/selection.bmp')

        for text in list(listToPrint): # do draw
            rIcoX, rIcoY = 2, 0

            icofile = icons.get(text, "./core/icons/missing.bmp")
            rico = Image.open(icofile).convert('1')

            if selection != text: # if our selection isnt the text iter gave us
                self.draw.text((18, yCoord), text.replace("_", " "), fill=0, outline=255, font=unselectedFont) # draw black text over rectangle
                
                ico = rico.resize((12,12))
            else: # it is our selection
                self.draw.rounded_rectangle([(-4, yCoord-2), (120, 12 + yCoord)], fill=0, outline=255, radius=3) # draw colored rectangle first
                self.draw.text((18, yCoord), text.replace("_", " "), fill=1, outline=255, font=selectedFont) # draw black text over rectangle
                
                ico = ImageOps.invert(rico).resize((12,12))

            self.image.paste(ico, (rIcoX, rIcoY+yCoord))

            yCoord += 13

        yCoord = 3

        while 60 >= yCoord:
            self.draw.rectangle(((124, yCoord), (124, yCoord)), fill=0)
            yCoord += 3

        selBoxY = (round(64 / len(moduleList)) * currentSelection)
        selBoxHeight = round(64 / len(moduleList))
        selBox = self.draw.rectangle(((123, selBoxY), (125, selBoxY+selBoxHeight)), fill=0)

def createSelection(display, text, xCoord, yCoord, selected=0, **kwargs):
    coords = (xCoord, yCoord)
    display.text(coords, text, fill=selected, **kwargs)
    return coords
