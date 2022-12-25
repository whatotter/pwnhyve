#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
absolute shitshow of code
gpio code snippets are from waveshare docs
rest are mine
"""
from PIL import Image, ImageDraw, ImageFont
from core.SH1106.screen import createSelection, fullClear, waitForKey
from core.utils import getChunk, uError, uStatus, fakeGPIO, uSuccess
from core.plugin import *
from time import sleep

pillowDebug = False # very not reliable, also laggy
enableWebServer = True

try:
    import core.SH1106.SH1106m as SH1106
    import RPi.GPIO as GPIO
except ImportError:
    uError("unable to import SH1106 or RPI.GPIO libary")
    if not pillowDebug:
        if enableWebServer:
            uStatus("starting webserver")

            from flask import Flask, Response, send_file, request
            import core.controlPanel.cpanel as cpanel

            uSuccess("imported webserver")

            cpanel.app.run(host="0.0.0.0", port=80)

        quit()
    else:
        uStatus("pillow debug enabled, showing all images to a pillow window")
        import matplotlib.pyplot as plt



class customizable:
    cleanScroll = True # true = everything scrolls, false = once you reach the bottom everything is redrawn
    # ^ reccomended on

    onlyPrefix = False # true = instead of inverted colors when item is selected, put set prefix to show its selected, false = invert colors of selected item
    # ^ reccomended off

    selectionBackgroundWidth = 200 # width of inverted colors, change if you have bigger display or dont like it
    # ^ reccomended at 200

    idleCycles = 240 * 3 # cycles before reporting idle; # 120 idle cycles is 30 seconds, 240 cycles is 60s (not exact)
    # ^ reccomended at 240 * 3

    selectedPrefix = ">" # if you dont want to fill the background with color, change this to what you want it as and enable "onlyPrefix"
    # ^ doesnt matter what you set it as but the default was ">"


class vars:
    xCoord = 5
    yCoord = 5
    currentSelection = 0 # index of programs list
    maxLNprint = 5
    cleanScrollNum = 0
    scrollChunks = []
    currentSelOld = 0
    passedIdleCycles = 0
    plugins = {}
    isActive = False
    flipped = False

    font = ImageFont.truetype('core/fonts/roboto.ttf', 11)

if __name__ == "__main__":

    # 240x240 display with hardware SPI:

    if not pillowDebug:
        disp = SH1106.SH1106()
        disp.Init()
        disp.clear()

        GPIO.setmode(GPIO.BCM)

        gpio = { # gpio pins are the buttons, like joystick, side buttons, etc.
            'KEY_UP_PIN': 6,
            'KEY_DOWN_PIN': 19,
            'KEY_LEFT_PIN': 5,
            'KEY_RIGHT_PIN': 26,
            'KEY_PRESS_PIN': 13,
            'KEY1_PIN': 21,
            'KEY2_PIN': 20,
            'KEY3_PIN': 16,
        }

        for gpioPin in gpio: # init gpio
            GPIO.setup(gpio[gpioPin],GPIO.IN,pull_up_down=GPIO.PUD_UP)
    else:
        class disp: # idk
            width = 128
            height = 64

            def ShowImage(buf):
                print(buf)
            def getbuffer(buf):
                plt.pause(0.0000000001)
                plt.imshow(image)
                sleep(0.025) # approx time for display to display image

        gpio = { # gpio pins are the buttons, like joystick, side buttons, etc.
            'KEY_UP_PIN': 'UP',
            'KEY_DOWN_PIN': 'DOWN',
            'KEY_LEFT_PIN': 'LEFT',
            'KEY_RIGHT_PIN': 'RIGHT',
            'KEY_PRESS_PIN': '.',
            'KEY1_PIN': 'q',
            'KEY2_PIN': 'a',
            'KEY3_PIN': 'z',
        }

        GPIO = fakeGPIO(gpio)

    image = Image.new('1', (disp.width, disp.height), "WHITE") # init display
    draw = ImageDraw.Draw(image) # dsiayp
    programCoords = {} # auisdhgwe89-drgyn 354-97n8g7tg6v0o89dt7gh6b0bfbt5o98fdftr0b8gi0cdfjstuxrogl7ht5rhu9gtgturjstinufdrg5nuhuotilxfcdfrugh

    plugins = load(folder="plugins") # load

    for p in plugins[1]: # for plugin in plugins list
        if len(plugins[1][p][1]) == 0: continue # sanity check
        for executable in plugins[1][p][1]: # for every executable in the plugin's executable list
            vars.plugins["{}".format(executable)] = {} # create dict

            try:
                vars.plugins["{}".format(executable, plugins[1][p][0])]["help"] = (plugins[1][p][1][executable].strip(), plugins[1][p][0]) # define help
            except KeyError: # command's help not in configurationfile
                raise KeyError("{}'s command {} doesn't have a help key pair in it's configuration".format(plugins[1][p][0], executable))
            vars.plugins["{}".format(executable, plugins[1][p][0])]["module"] = None # set module as None to show it's not ours


    vars.plugins["reload"] = {}
    vars.plugins["reload"]["help"] = ("reload plugins","0") # define help

    vars.plugins["exitScript"] = {}
    vars.plugins["exitScript"]["help"] = ("fully quit script","0") # define help2

    # create scroll chunks
    if not customizable.cleanScroll: vars.scrollChunks = getChunk(list(vars.plugins), vars.maxLNprint)

    while 1:
        vars.isActive = False
        yCoordBefore = vars.yCoord
        fullClear(draw)
        if pillowDebug:
            os.system("cls") # clear term

        try: # check if selection is out of range
            selection = list(vars.plugins)[vars.currentSelection]
        except IndexError: # if it is
            vars.currentSelection = vars.currentSelection - 1 # failsafe
            selection = list(vars.plugins)[vars.currentSelection - 1] # go back 1 (TODO: maybe remove)

        if vars.currentSelection >= vars.maxLNprint: # if current selection index is equal or more than max line print
            if vars.currentSelection != vars.currentSelOld: # and if current selection isnt the same as old index
                vars.cleanScrollNum += 1 # increase scroll
        else: # if it's smaller
            if vars.currentSelection != vars.currentSelOld: # and it isnt the same as old index
                vars.cleanScrollNum -= 1 # decrease scroll

        vars.currentSelOld = vars.currentSelection # set our old value after we checked

        if not customizable.cleanScroll: # if we arent clean scroll
            # slightly ram saving
            for chunk in vars.scrollChunks:
                if selection in chunk: # if our selected string is in the chunk (string = "abcd", chunks = [["banana", >>>"abcd"<<<, "efg"], ["apple", "green", "xyz"]])
                    listToPrint = chunk
        else:
            a = list(vars.plugins) # turn our plugins dict into a list
            listToPrint = [] # clean list to print

            for _ in range(vars.currentSelection): # iter over current selection (i dont understand this)
                if vars.cleanScrollNum != 0:
                    a.pop(0)

            for i in a: # iter over our plugin
                listToPrint = a[:5] # add 5 items every time

        for text in list(listToPrint): # do draw
            if selection != text: # if our selection isnt the text iter gave us
                returnedCoords = createSelection(draw, text, vars.xCoord, vars.yCoord, selected=0, font=vars.font) # draw it normally
                programCoords[text] = returnedCoords # set the coords for later
            else: # it is our selection
                if not customizable.onlyPrefix: # if we arent using only prefix
                    draw.rectangle([(0, vars.yCoord), (customizable.selectionBackgroundWidth, 13 + vars.yCoord)], fill=0, outline=255) # draw colored rectangle first
                    draw.text((vars.xCoord, vars.yCoord), text, fill=1, outline=255, font=vars.font) # draw black text over rectangle
                else:
                    createSelection(draw, selection, vars.xCoord, vars.yCoord, selected=1, font=vars.font) # clear it
                    createSelection(draw, customizable.selectedPrefix+selection, vars.xCoord, vars.yCoord, selected=0, font=vars.font) # draw over it

                programCoords[text] = (vars.xCoord, vars.yCoord) # add coord
                    
            vars.yCoord += 14

        vars.yCoord = yCoordBefore # set our y coord

        # button stuff

        if GPIO.input(gpio['KEY_DOWN_PIN']): # button is released
            pass
        else: # button is pressed:
            vars.isActive = True

            if vars.flipped:
                if vars.currentSelection == 0:
                    vars.currentSelection = len(vars.plugins)
                    continue
                vars.currentSelection -= 1
            else:
                if vars.currentSelection == (len(vars.plugins)):
                    vars.currentSelection = 0
                    continue
                vars.currentSelection += 1

        if GPIO.input(gpio['KEY_UP_PIN']): # button is released
            pass # not press
        else: # button is pressed:
            vars.isActive = True

            if not vars.flipped:
                if vars.currentSelection == 0:
                    vars.currentSelection = len(vars.plugins)
                    continue
                vars.currentSelection -= 1
            else:
                if vars.currentSelection == (len(vars.plugins)):
                    vars.currentSelection = 0
                    continue
                vars.currentSelection += 1

        if not GPIO.input(gpio['KEY_PRESS_PIN']) or not GPIO.input(gpio['KEY_RIGHT_PIN']): # button is pressed
            vars.isActive = True # set our idle thing
            key = list(vars.plugins)[vars.currentSelection] # set key value

            if key == "reload":
                reloaded = load(folder="plugins") # load
                vars.plugins = {} # clear since reload

                print("[info] plugin reload")

                for p in reloaded[1]: # for plugin in reloaded list
                    if len(reloaded[1][p][1]) == 0: continue # sanity check
                    for executable in reloaded[1][p][1]: # for every executable in the plugin's executable list
                        print("[plugin] added {}".format(executable))
                        vars.plugins["{}".format(executable)] = {} # create dict

                        try:
                            vars.plugins["{}".format(executable, reloaded[1][p][0])]["help"] = (reloaded[1][p][1][executable].strip(), reloaded[1][p][0]) # define help
                        except KeyError: # command's help not in configurationfile
                            raise KeyError("{}'s command {} doesn't have a help key pair in it's configuration".format(reloaded[1][p][0], executable))
                        vars.plugins["{}".format(executable, reloaded[1][p][0])]["module"] = None # set module as None to show it's not ours

                vars.plugins["reload"] = {}
                vars.plugins["reload"]["help"] = ("reload plugins","0") # define help

                fullClear(draw) # clear display

                disp.ShowImage(disp.getbuffer(image)) #draw

                continue

            elif key == "exitScript":
                quit()

            for p in plugins[1]: # for plugin in plugins list
                for executable in plugins[1][p][1]: # for every executable in the 
                    if executable == key:
                        plg = plugins[1][p][2] # chosen plugin
                        run(key, [draw, disp, image, GPIO], plg) # run it
        else: # button is NOT pressed:
            pass

        if GPIO.input(gpio['KEY2_PIN']): # button is released
            pass
        else: # button is pressed:
            vars.flipped = not vars.flipped # flip display

        if GPIO.input(gpio['KEY3_PIN']): # button is released
            pass
        else: # button is pressed:
            fullClear(draw)

            cur = list(vars.plugins)[vars.currentSelection]
            printed = False

            draw.rectangle([(0, 0), (200, 16)], fill=0, outline=255)
            draw.text((3, 1), "help for \"{}\"".format(cur), fill=1, outline=255, font=vars.font)


            help = vars.plugins[cur]['help'][0] # get all help from modules

            if len(help) > 21:
                a = []
                c = [str(x) for x in help]

                while True:
                    if len(c) > 21: d = 21
                    else: d = len(c)

                    if d == 0: break

                    a.append(''.join(c[:d]).strip())

                    for i in c[:d]:
                        c.remove(i)

                help = '|'.join(a)

            if "|" in help:
                print("| in help")
                a = help.split("|")
                b = 18
                for i in a:
                    draw.text((5, b), i, fill=0, outline=255, font=vars.font)
                    print('added {}'.format(i))
                    b += 11
            else:
                print("| not in help")
                draw.text((5, 18), help, fill=0, outline=255, font=vars.font)
            printed = True

            if not printed:
                draw.text((10, 25), "no help is available for this plugin", fill=1, outline=255, font=vars.font)

            # show compiled image
            if vars.flipped:
                disp.ShowImage(disp.getbuffer(image.transpose(Image.FLIP_LEFT_RIGHT)))
            else:
                disp.ShowImage(disp.getbuffer(image))

            waitForKey(GPIO)

        if not vars.isActive:
            if customizable.idleCycles <= vars.passedIdleCycles:
                try:
                    for p in plugins[1]: # for plugin in plugins list
                        for executable in plugins[1][p][1]: # for every executable in the 
                            if executable == "setIdle":
                                plg = plugins[1][p][2] # chosen plugin
                                run("setIdle", [draw, disp, image, GPIO], plg)       
                    vars.passedIdleCycles = 0
                except Exception as e:
                    print("failed to go idle: {}".format(str(e)))
                    pass
            vars.passedIdleCycles += 1



        # show compiled image
        if vars.flipped:
            img1 = image.transpose(Image.FLIP_TOP_BOTTOM) # easy read
            disp.ShowImage(disp.getbuffer(img1.transpose(Image.FLIP_LEFT_RIGHT)))
        else:
            if not pillowDebug:
                disp.ShowImage(disp.getbuffer(image))
            else:
                disp.getbuffer(image)
                #image.show()
                #plt.pause(0.01)
                #plt.imshow(image)
                #sleep(0.25) # approx time for display to display image
                #plt.show()