"""
THIS WILL ALWAYS RUN WHEN IDLE

you can also edit the nyan cat frames to show what you wanna show, just edit the bitmap files in ./core/nyanCatIdle
"""

from PIL import ImageFont, Image
import time
from core.SH1106.screen import waitForKey, checkIfKey

class vars:
    font = ImageFont.truetype('core/fonts/Font.ttf', 18)

    nyanCat = True # enable meow meow meow meow meow meow 
    nyanCatDelay = 0.0025 # delay inbetween showing new frame
    displayResX, displayResY = 128, 64 # your display resolution to display nyan cat correctly

def fullClear(display):
    display.rectangle((0, 0, 200, 100), fill=1)
    return True

def setIdle(args:list):

    canvas, display, image, GPIO = args[0], args[1], args[2], args[3]

    print("now idle")

    fullClear(canvas)

    #canvas.text((10, 10), "a mimir", fill=0, outline=255, font=vars.font)

    if not vars.nyanCat:
        display.ShowImage(display.getbuffer(image))

        waitForKey(GPIO)
    else:
        display.ShowImage(display.getbuffer(image))

        currFrame = 1

        image = Image.new('1', (display.width, display.height), 255)  # 255: clear the frame

        frames = {}

        for x in range(1, 12):
            bmp = Image.open('./core/nyanCatIdle/frame{}.bmp'.format(x))
            frames[x] = bmp.resize((vars.displayResX, vars.displayResY))


        while 1: # wait for key press
            if checkIfKey(GPIO): break

            if currFrame == 12: currFrame = 1

            image = Image.new('1', (display.width, display.height), 255)  # 255: clear the frame       
            image.paste(frames[currFrame])
            display.ShowImage(display.getbuffer(image))

            currFrame += 1

            time.sleep(vars.nyanCatDelay)

    return

def functions():
    return {"setIdle": "set Artremis as idle, and run its idle definition", "icons": {"setIdle": "./core/icons/zzz.bmp"}}