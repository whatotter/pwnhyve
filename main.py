#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
absolute shitshow of code
gpio code snippets are from waveshare docs
rest are mine
"""
from PIL import Image, ImageDraw, ImageFont
from core.SH1106.screen import *
from core.utils import getChunk, uError, uStatus, uSuccess
from core.plugin import *
import json
import threading
import socket

pillowDebug = False # very not reliable, also laggy
enableWebServer = True

devOptions = False # enable dev options

"""
TODO: 
make a modded
"""

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
    # (mostly) everything is overridden by the config.json
    # !!!!!!!!!!!!!!!!!!!!!! DO NOT EDIT !!!!!!!!!!!!!!!!!!! because of ^

    cleanScroll = True # true = everything scrolls, false = once you reach the bottom everything is redrawn
    # ^ reccomended on

    onlyPrefix = False # true = instead of inverted colors when item is selected, put set prefix to show its selected, false = invert colors of selected item
    # ^ reccomended off

    selectionBackgroundWidth = 200 # width of inverted colors, change if you have bigger display or dont like it
    # ^ reccomended at 200

    idleCycles = 2400000 * 60 # cycles before reporting idle; # 120 idle cycles is 30 seconds, 240 cycles is 60s (not exact)
    # ^ reccomended at 240 * 3

    selectedPrefix = ">" # if you dont want to fill the background with color, change this to what you want it as and enable "onlyPrefix"
    # ^ doesnt matter what you set it as but the default was ">"

    screenType = "original" # menu type
    # ^ prefrence

    disableIdle = False # disable idle
    # ^ prefrence, but reduces cpu usage, which in turn increases lifespan on battery

    disableKeys = False # disable keys from socket
    # ^ can be disabled just in case, disables all socket info


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
    icons = {}
    folders= []
    prevSelection = None
    menus = {}

    streamSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    font = ImageFont.truetype('core/fonts/roboto.ttf', 11)
    flipperFontN = ImageFont.truetype('core/fonts/pixelop/PixelOperatorMono.ttf', 16)
    flipperFontB = ImageFont.truetype('core/fonts/pixelop/PixelOperatorMono-Bold.ttf', 16)
    flipperSelection = Image.open('./core/fonts/selection.bmp')
    microFont = ImageFont.truetype('core/fonts/pixelop/PixelOperatorMono8.ttf', 5)

def stream():
    """
    replay all pillow images to socket
    """

    vars.streamSock.bind(("0.0.0.0", 11198))
    vars.streamSock.listen(1)
    vars.streamSock.settimeout(None)

    open("/tmp/socketGPIO", "w").write("")
    open("/tmp/base64Data", "w").write("")

    while True:
        vars.streamSock.settimeout(None)

        conn, addr = vars.streamSock.accept()

        conn.settimeout(0.05)
        vars.streamSock.settimeout(0.05)

        while True:
            if os.path.exists("/tmp/base64Data"):
                with open("/tmp/base64Data", "r") as f:
                    try:
                        conn.sendall(f.read().encode('utf-8'))
                    except:
                        break

            try:
                data = conn.recv(512).decode('utf-8') # 100ms delay
            except:
                continue

            if data:
                if not customizable.disableKeys:
                    with open("/tmp/socketGPIO", "w") as f:
                        f.write(data)
                        f.flush()
            else:
                continue

        vars.streamSock.settimeout(None)



if __name__ == "__main__":

    # villain setuo
    #Thread(target=opsys, args=("cd ./core/villain && sudo python3 villain.py &",), daemon=True).start()
    #print("[!] started villain; use fg to bring it to console")

    # 240x240 display with hardware SPI:

    with open("config.json", "r") as f:
        a = json.loads(f.read())

        customizable.cleanScroll = a["cleanScroll"]
        customizable.onlyPrefix = a["onlyPrefix"]
        customizable.selectionBackgroundWidth = a["selectionBackgroundWidth"]
        customizable.idleCycles = a["idleCycles"]
        customizable.selectedPrefix = a["selectedPrefix"]
        customizable.disableIdle = a["disableIdle"]

        customizable.screenType = a["screenType"]

        if a["enableStream"]:
            threading.Thread(target=stream, daemon=True).start()

        # types of screens
        # "original": the original display i made
        # "flipper": the display based off a flipper zero
        # "minimalistic": the display based off the classic deauth watch - also really minimalistic, personal favorite

        if customizable.screenType == "flipper": yCoord = 1

        if a["enableWebServer"]:
            uStatus("starting webserver")

            #from flask import Flask, Response, send_file, request
            import core.controlPanel.cpanel as cpanel

            uSuccess("imported webserver")

            #cpanel.app.run(host="0.0.0.0", port=80)

            Thread(target=cpanel.run, args=("0.0.0.0",7979,), daemon=True).start()

        disp = SH1106.SH1106()
        disp.Init()
        disp.clear()

        GPIO.setmode(GPIO.BCM)

        GPIO.sockStream = vars.streamSock

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

    image = Image.new('1', (disp.width, disp.height), "WHITE") # init display
    draw = ImageDraw.Draw(image) # dsiayp

    plugins = load(folder="plugins") # load

    # THIS SHIT IS FUCKED UP
    for p in plugins: # for plugin in plugins list
        if len(plugins[p][1]) == 0: continue # sanity check
        for executable in plugins[p][1]: # for every executable in the plugin's executable list
            if executable == "icons": continue
            vars.plugins[executable] = {} # create dict
            vars.icons[executable] = {} # create dict

            try:
                vars.icons[executable] = plugins[p][1]["icons"][executable].strip() # define icon
            except: #KeyError:
                vars.icons[executable] = None

            try:
                vars.plugins["{}".format(executable, plugins[p][0])]["help"] = (plugins[p][1][executable].strip(), plugins[p][0]) # define help

            except (KeyError, AttributeError): # command's help not in configurationfile
                vars.plugins[executable]["help"] = "I AM A FOLDER" # reminds me of that "I AM A SURGON" thing
                vars.folders.append(executable)
                for item in plugins[p][1][executable]: # what the fuck
                    try:
                        a = plugins[p][1][executable][item]
                    except:
                        raise KeyError("{}'s command {} doesn't have a help key pair in it's configuration".format(plugins[p][0], executable))

                    try:
                        vars.icons[item] = plugins[p][1]["icons"][item].strip() # define icon
                    except: #KeyError:
                        vars.icons[item] = None

                    vars.plugins[executable][item] = a
                    #vars.plugins[executable]["help"] = a # define help

                    #print(vars.plugins[executable])
                    #print(vars.plugins)

    #print(plugins)

    menus = load(folder="menus") # load for menus


    if devOptions:
        vars.plugins["reload"] = {}
        vars.plugins["reload"]["help"] = ("reload plugins","0") # define help

        vars.plugins["exitScript"] = {}
        vars.plugins["exitScript"]["help"] = ("fully quit script","0") # define help2

    # create scroll chunks
    if not customizable.cleanScroll: vars.scrollChunks = getChunk(list(vars.plugins), vars.maxLNprint)
    vars.prevSelection = 9e9

    while 1:
        vars.isActive = False
        yCoordBefore = vars.yCoord

        # interface for batteries n stuff
        #draw.text((6,0), "CPU:000", font=vars.microFont)
        #draw.text((16,0), "M:WL0", font=vars.microFont)
        #draw.text((24,0), "AP:SOLO0", font=vars.microFont)
        # TODO: make battery icons # finished


        try: # check if selection is out of range
            selection = list(vars.plugins)[vars.currentSelection]
        except IndexError: # if it is
            vars.currentSelection = vars.currentSelection - 1 # failsafe
            selection = list(vars.plugins)[vars.currentSelection - 1] # go back 1 (TODO: maybe remove)

        """        
        if vars.currentSelection >= vars.maxLNprint: # if current selection index is equal or more than max line print
            if vars.currentSelection != vars.currentSelOld: # and if current selection isnt the same as old index
                vars.cleanScrollNum += 1 # increase scroll
        else: # if it's smaller
            if vars.currentSelection != vars.currentSelOld: # and it isnt the same as old index
                vars.cleanScrollNum -= 1 # decrease scroll

        # TODO: make the screen not update if selection hasn't changed
        #if vars.currentSelection == vars.currentSelOld:
            #continue # no updates needed, will be faster

        vars.currentSelOld = vars.currentSelection # set our old value after we checked
        """

        fullClear(draw)

        if customizable.screenType in menus:
            b = menus[customizable.screenType]

            listToPrint = b[2].screen.getItems([vars.plugins, vars.yCoord, vars.xCoord, vars.currentSelection, selection])

            b[2].screen.display([draw, disp, image, GPIO, list(listToPrint), plugins, vars.yCoord, vars.xCoord, vars.currentSelection, selection, vars.icons])

            screenShow(disp, image, flipped=vars.flipped, stream=True)
        

        vars.yCoord = yCoordBefore # set our y coord

        # button stuff

        vars.prevSelection = vars.currentSelection

        while True:
            key = menu(draw, disp, image, list(vars.plugins), GPIO, disableBack=True)

            #print(key)

            print(vars.folders)

            if key in vars.folders:
                #print("AB" * 30)
                # URGENT TODO: FIX THIS
                    
                    
                plgList = vars.plugins[key]
                if "help" in plgList:
                    plgList.pop("help")
                
                print(list(plgList))

                a = menu(draw, disp, image, list(plgList), GPIO, menuType=customizable.screenType)

                #key = list(plgList)[vars.currentSelection]

                for executable in plgList: # for every executable in the
                    #print("KURWAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
                    #print(executable)

                    #choice = plugins[1][p][1][executable]
                    #print(choice)

                    print("--------------------------------")
                    print(plgList)
                    print("--------------------------------")

                    if executable == a:
                        plg = None

                        for x in plugins:
                            for y in plugins[x]:
                                print("{} in {}".format(a, list(plugins[x][1])))
                                for z in list(plugins[x][1]):
                                    if type(plugins[x][1][z]) == dict:
                                        print(plugins[x][1][z])
                                        if z == "icons": continue
                                        if a in list(plugins[x][1][z]):
                                            print("boom")
                                            plg = plugins[x][2]
                                
                        if plg == None:
                            plg = plugins[p][2] # chosen plugin

                        assert plg != None

                        print("--------")
                        print(plg)
                        print("--------")
                        #TODO: make it run in a different thread so it doesnt error main thread

                        open("./core/temp/threadQuit", "w").write("0")
                        z = run(a, [draw, disp, image, GPIO], plg) # run it
                        open("./core/temp/threadQuit", "w").write("1")

                        break
                    else:
                        pass
                        #print("abf") # i love spelling

                break
            else:
                for p in plugins: # for plugin in plugins list
                    for executable in plugins[p][1]: # for every executable in the 
                        if executable == key:
                            plg = plugins[p][2] # chosen plugin
                            run(key, [draw, disp, image, GPIO], plg) # run it

                break