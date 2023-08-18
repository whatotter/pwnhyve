from PIL import ImageFont
from core.SH1106.screen import *
import time

class example1:
    """
    an example class
    """
    def print_this(string):
        """
        an example definition in an example class
        """
        print(string)

    config = { 
        # you can have this in an external file, aslong as main file gets it in dictionary format
        # this is for your command help n stuff
        "hello": "123456789abcdefghijkl",

        "icons": {
            "hello": "./core/icons/zzz.bmp"
        }
    }

    font = ImageFont.truetype('core/fonts/Font.ttf', 18)

def fullClear(display):
    display.rectangle((0, 0, 200, 100), fill=1)
    return True

def hello(args:list):
    """
    an example command
    """

    canvas, display, image = args[0], args[1], args[2]

    example1.print_this("hello world")

    fullClear(canvas)

    canvas.text((10, 10), "hello world", fill=0, outline=255, font=example1.font)

    screenShow(display, image, flipped=False, stream=True)

    time.sleep(3)

    return

def ask(string):
    """
    an example of an unexecutable function
    """

    return input(string)

def functions():
    """
    put your executable functions here and your configuration
    """
    return example1.config