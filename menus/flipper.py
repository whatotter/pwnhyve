from PIL import Image, ImageDraw, ImageFont, ImageOps
from core.plugin import BasePwnhyvePlugin

class Screen(BasePwnhyvePlugin):
    def getItems(self, plugins, currentSelection):
    
        listToPrint = plugins[currentSelection:currentSelection+5]

        return listToPrint

    def display(self, draw, disp, image, GPIO, moduleList, currentSelection, icons):

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
                draw.text((18, yCoord), text.replace("_", ""), fill=0, outline=255, font=unselectedFont) # draw black text over rectangle
                
                ico = rico.resize((12,12))
            else: # it is our selection
                draw.rounded_rectangle([(-4, yCoord-2), (120, 12 + yCoord)], fill=0, outline=255, radius=3) # draw colored rectangle first
                draw.text((18, yCoord), text.replace("_", ""), fill=1, outline=255, font=selectedFont) # draw black text over rectangle
                
                ico = ImageOps.invert(rico).resize((12,12))

            image.paste(ico, (rIcoX, rIcoY+yCoord))

            yCoord += 13

        yCoord = 3

        while 60 >= yCoord:
            draw.rectangle(((124, yCoord), (124, yCoord)), fill=0)
            yCoord += 3

        selBoxY = (round(64 / len(moduleList)) * currentSelection)
        selBoxHeight = round(64 / len(moduleList))
        selBox = draw.rectangle(((123, selBoxY), (125, selBoxY+selBoxHeight)), fill=0)

def createSelection(display, text, xCoord, yCoord, selected=0, **kwargs):
    coords = (xCoord, yCoord)
    display.text(coords, text, fill=selected, **kwargs)
    return coords
