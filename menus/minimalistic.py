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

        xCoord = 0

        for text in list(listToPrint): # do draw
            if selection != text: # if our selection isnt the text iter gave us
                createSelection(draw, "  " + text.replace("_", ""), xCoord, yCoord, selected=0, font=ImageFont.truetype('core/fonts/tahoma.ttf', 11)) # draw it normally
            else: # it is our selection
                createSelection(draw, "| " + selection.replace("_", ""), xCoord, yCoord, selected=0, font=ImageFont.truetype('core/fonts/tahoma.ttf', 11)) # draw over it
                    
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