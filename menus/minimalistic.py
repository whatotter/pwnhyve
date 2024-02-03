from PIL import Image, ImageDraw, ImageFont, ImageOps
from core.plugin import BasePwnhyvePlugin

class vars:
    maxLNprint = 5
    cleanScrollNum = 0
    currentSelOld = 0

class Screen(BasePwnhyvePlugin):
    def getItems(self, plugins, currentSelection):

        print(plugins)

        if currentSelection >= vars.maxLNprint: # if current selection index is equal or more than max line print
            if currentSelection != vars.currentSelOld: # and if current selection isnt the same as old index
                vars.cleanScrollNum += 1 # increase scroll
        else: # if it's smaller
            if currentSelection != vars.currentSelOld: # and it isnt the same as old index
                vars.cleanScrollNum -= 1 # decrease scroll

        vars.currentSelOld = currentSelection

        a = list(plugins) # turn our plugins dict into a list
        listToPrint = [] # clean list to print

        for _ in range(currentSelection): # iter over current selection (i dont understand this)
            if vars.cleanScrollNum != 0:
                a.pop(0)

        for i in a: # iter over our plugin
            listToPrint = a[:5] # add 5 items every time

        listToPrint = plugins[currentSelection:currentSelection+5]
        
        return listToPrint


    def display(self, draw, disp, image,
                 GPIO, listToPrint, plugins,
                   yCoord, xCoord, currentSelection,
                     selection, icons):

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