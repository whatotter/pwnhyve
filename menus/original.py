from PIL import Image, ImageDraw, ImageFont, ImageOps
from core.plugin import BasePwnhyvePlugin

class vars:
    maxLNprint = 5
    cleanScrollNum = 0
    currentSelOld = 0

class Screen(BasePwnhyvePlugin):
    def getItems(self, plugins, currentSelection):

        listToPrint = plugins[currentSelection:currentSelection+5]

        return listToPrint


    def display(self, draw, disp, image, GPIO, moduleList, currentSelection, icons):

        listToPrint = self.getItems(moduleList, currentSelection)
        selection = moduleList[currentSelection]

        xCoord = 2
        yCoord = 2

        font = ImageFont.truetype('core/fonts/roboto.ttf', 11)

        for text in list(listToPrint): # do draw
            if selection != text: # if our selection isnt the text iter gave us
                #createSelection(draw, text, xCoord, yCoord, selected=0, font=font) # draw it normally
                draw.text((xCoord, yCoord), text.replace("_", ""), fill=0, outline=255, font=font) # draw black text over rectangle
            else: # it is our selection
                draw.rectangle([(0, yCoord), (255, 13 + yCoord)], fill=0, outline=255) # draw colored rectangle first
                draw.text((xCoord, yCoord), text.replace("_", ""), fill=1, outline=255, font=font) # draw black text over rectangle

                    
            yCoord += 14

def createSelection(display, text, xCoord, yCoord, selected=0, **kwargs):
    coords = (xCoord, yCoord)
    display.text(coords, text, fill=selected, **kwargs)
    return coords

def functions():
    return {
        "screen.getItems": "",
        "screen.display": ""
    }