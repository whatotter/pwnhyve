"""
THIS WILL ALWAYS RUN WHEN IDLE

you can also edit the nyan cat frames to show what you wanna show, just edit the bitmap files in ./core/nyanCatIdle
"""

from PIL import ImageFont, Image
import time
from core.SH1106.screen import waitForKey, checkIfKey

#GPIO define
RST_PIN        = 25
CS_PIN         = 8
DC_PIN         = 24

KEY_UP_PIN     = 6 
KEY_DOWN_PIN   = 19
KEY_LEFT_PIN   = 5
KEY_RIGHT_PIN  = 26
KEY_PRESS_PIN  = 13

KEY1_PIN       = 21
KEY2_PIN       = 20
KEY3_PIN       = 16

class vars:
    font = ImageFont.truetype('core/fonts/Font.ttf', 18)

    nyanCat = True # enable meow meow meow meow meow meow 
    nyanCatDelay = 0.05 # delay inbetween showing new frame
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

        while 1: # wait for key press
            if checkIfKey(GPIO): break

            if currFrame == 12: currFrame = 1
            image = Image.new('1', (display.width, display.height), 255)  # 255: clear the frame
            bmp = Image.open('./core/nyanCatIdle/frame{}.bmp'.format(currFrame))
            image.paste(bmp.resize((vars.displayResX, vars.displayResY)), (0,5))
            display.ShowImage(display.getbuffer(image))
            currFrame += 1

            time.sleep(vars.nyanCatDelay)

    return

def functions():
    return {"setIdle": "set Artremis as idle, and run its idle definition"}