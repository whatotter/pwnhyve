from PIL import Image, ImageDraw, ImageFont, ImageOps

class screen:
    def getItems(args:list):
        plugins, yCoord, xCoord, currentSelection, selection = args
    
        listToPrint = [] # clean list to print

        # TODO: figure out something cleaner than this
        try:
            b4 = list(plugins)[currentSelection - 1]
        except IndexError: b4=list(plugins)[0]
        try:
            after = list(plugins)[currentSelection + 1]
        except IndexError: after=list(plugins)[0]

        listToPrint = [b4, selection, after]
        #
        #   b4 > pwnagotchi
        #   selection > reboot 
        #   after > shutdown
        #
        #

        return listToPrint

    def display(args:list):

        draw, disp, image, GPIO, listToPrint, plugins, yCoord, xCoord, currentSelection, selection, icons = args

        yCoord = 1

        flipperFontN = ImageFont.truetype('core/fonts/pixelop/PixelOperatorMono.ttf', 16)
        flipperFontB = ImageFont.truetype('core/fonts/pixelop/PixelOperatorMono-Bold.ttf', 16)
        flipperSelection = Image.open('./core/fonts/selection.bmp')
    
        for text in list(listToPrint): # do draw
            bigMinimizedText = ''.join([str(x) for x in text][:12]) # usually for big
            smallMinimizedText = ''.join([str(x) for x in text][:14]) # usually for small

            xCoord = 24

            if text == "": yCoord += 22; return

            icoX, icoY = 4, yCoord + 2

            try:
                try:
                    ico1 = icons[text]
                except: ico1 = None
                #                 ^ v smartest person alive rn
                if ico1 == None: ico1 = "./core/icons/missing.bmp"

                ico = Image.open(ico1).resize((16,16))
            except Exception as e:
                raise

            if text == selection:
                #boxcoords = [(2, 24), (128 - 4, 18 + yCoord)]
                #draw.rectangle(boxcoords, fill=1, outline=0)

                image.paste(flipperSelection, (0,22))

                createSelection(draw, bigMinimizedText, xCoord, yCoord, selected=0, font=flipperFontB) # draw over it 
                image.paste(ico, (icoX, icoY)) # do icon again cuz it glitches
            else:
                createSelection(draw, smallMinimizedText, xCoord, yCoord, selected=0, font=flipperFontN) # draw over it 
                image.paste(ico, (icoX, icoY))

            yCoord += 22

def createSelection(display, text, xCoord, yCoord, selected=0, **kwargs):
    coords = (xCoord, yCoord)
    display.text(coords, text, fill=selected, **kwargs)
    return coords

def functions():
    return {
        "screen.getItems": "",
        "screen.display": ""
    }