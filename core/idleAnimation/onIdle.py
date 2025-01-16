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
    display.rectangle((0, 0, 300,300), fill=1)
    return True

class Plugin(BasePwnhyvePlugin):
    def setIdle(tpil):

        print("now idle")

        #fullClear(canvas)
        #canvas.text((10, 10), "a mimir", fill=0, outline=255, font=vars.font)

        currFrame = 1
        frames = {}

        framesAmnt = len(os.listdir("./core/idleAnimation"))

        for x in range(1, framesAmnt):
            bmp = Image.open('./core/idleAnimation/frame{}.bmp'.format(x))
            if tpil.disp.height == tpil.disp.width: # when 1:1 ratio
                h = round(tpil.disp.height/2)
            else:
                h = tpil.disp.height

            frames[x] = bmp.resize((tpil.disp.width, h))


        while 1: # wait for key press
            if tpil.checkIfKey(): return

            if currFrame == framesAmnt: currFrame = 1

            tpil.pasteImage(frames[currFrame])

            currFrame += 1

            time.sleep(vars.nyanCatDelay)
                
        return
