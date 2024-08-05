"""
THIS WILL ALWAYS RUN WHEN IDLE

you can also edit the nyan cat frames to show what you wanna show, just edit the bitmap files in ./core/idleAnimations
"""

import os
from core.plugin import BasePwnhyvePlugin
from PIL import ImageFont, Image
import time

class vars:
    font = ImageFont.truetype('core/fonts/Font.ttf', 18)

    nyanCat = True # enable meow meow meow meow meow meow 
    nyanCatDelay = 0.05 # delay inbetween showing new frame
    displayResX, displayResY = 128, 64 # your display resolution to display nyan cat correctly

def fullClear(display):
    display.rectangle((0, 0, 200, 100), fill=1)
    return True

class Plugin(BasePwnhyvePlugin):
    def setIdle(canvas, display, image, GPIO):

        print("now idle")

        #fullClear(canvas)
        #canvas.text((10, 10), "a mimir", fill=0, outline=255, font=vars.font)

        if not vars.nyanCat:
            display.showImage(image)
            display.waitForKey(GPIO)
        else:
            currFrame = 1
            frames = {}

            framesAmnt = len(os.listdir("./core/idleAnimation"))

            for x in range(1, framesAmnt):
                bmp = Image.open('./core/idleAnimation/frame{}.bmp'.format(x))
                frames[x] = bmp.resize((vars.displayResX, vars.displayResY))


            while 1: # wait for key press
                if display.checkIfKey(GPIO): return

                if currFrame == framesAmnt: currFrame = 1

                display.showImage2(frames[currFrame])

                currFrame += 1

                time.sleep(vars.nyanCatDelay)
                
        return
