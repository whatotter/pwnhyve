# simplifies pillow's draw
from PIL import Image, ImageDraw, ImageFont, ImageOps

class tinyPillow:
    def __init__(self, draw:ImageDraw.Draw, disp, image):
        self.draw = draw
        self.disp = disp
        self.image = image
        self.gui = disp.gui
        self.pinout = self.disp.pinout

        self.instantDraw = False
        self.font = ImageFont.truetype('core/fonts/monospace.ttf', 12)

        return
    
    def __manageInvColor__(self, color):
        """
        check if display is monochrome and inverted colors (i'm looking at you sh1106)
        """

        if not self.disp.hasColor and self.disp.invertedColor: # 1bit display, and inverted colors
            if color.lower() == "white":
                return "BLACK"
            elif color.lower() == "black":
                return 'WHITE'
            else: # not black or white
                return 'BLACK' # return black (which will come out as white on inverted displays)
        else: # not 1bit display or inverted color
            return color # return normal color
    
    def text(self, coords:list, text:str, color='WHITE', font=None, fontSize=None, **kwargs):
        """draw text"""

        wfont = self.font
        if font != None:
            wfont = font
        if fontSize != None:
            wfont = ImageFont.truetype('core/fonts/monospace.ttf', fontSize)

        color = self.__manageInvColor__(color)

        return self.draw.text(coords, str(text),
                        font=wfont,
                        fill=color,
                        **kwargs
                        )
    
    def rect(self, topleft:list, bottomright:list, color='WHITE'):
        """draw a rectangle/square"""
        color = self.__manageInvColor__(color)
        
        return self.draw.rectangle((tuple(topleft), tuple(bottomright)),
                        fill=color
                        )
    def clear(self):
        return self.disp.fullClear(self.draw)

    def waitForKey(self, *args, **kwargs):
        """
        wait for key press and return the key pressed

        returns the key pressed
        """
        return self.disp.waitForKey(*args, **kwargs)

    def checkIfKey(self, *args, **kwargs):
        """
        check if a key is pressed - note this is DEPRECIATED, use getKey() instead
        this is synonomous to getKey() for now, for backwards compat.
        """
        return self.disp.getKey(*args, **kwargs)

    def getKey(self, *args, **kwargs):
        """return the current key pressed"""

        return self.disp.getKey(*args, **kwargs)

    def waitWhileChkKey(self, *args, **kwargs):
        """
        check if a key is pressed with an alotted timeout

        Arguments:
            time: timeout time in seconds
        """
        return self.disp.waitWhileChkKey(*args, **kwargs)
    
    def loadImage(self, bitmapPath:str, coords:list=[0,0], inverted:bool=False):
        """
        paste an image at XY coords
        """

        bmp = Image.open(bitmapPath)

        if inverted:
            bmp = ImageOps.invert(bmp.convert('L'))

        self.image.paste(bmp, coords)

    def pasteImage(self, imageObject:Image, coords:list=[0,0]):
        """
        paste an image at XY coords
        """

        self.image.paste(imageObject, coords)

    def show(self, clear=True):
        """
        show compiled image to display
        """
        self.disp.screenShow()
        if clear: self.clear()

        

    def __getDDI__(self):
        """return (d)raw (d)isplay (i)mage for backwards compat. or custom drawings"""
        return self.draw, self.disp, self.image
    
    def resizeCoordinate2Res(self, coordinate, axis='x'):
        """
        resize a single coordinate to turn a 128x64 coordinate to a different resolution

        this is botched
        """
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