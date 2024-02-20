#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
absolute shitshow of code
gpio code snippets are from waveshare docs
rest are mine
"""
import os
from PIL import Image, ImageDraw, ImageFont
from core.SH1106.screen import *
from core.utils import getChunk, uError, uStatus, uSuccess, config
from core.plugin import *
#import json
#import threading
#import socket

pillowDebug = False # very not reliable, also laggy
enableWebServer = True

devOptions = False # enable dev options

try:
    import core.SH1106.SH1106m as SH1106
    import RPi.GPIO as GPIO
except ImportError:
    uError("unable to import SH1106 or RPI.GPIO libary")
    quit() 

class customizable:
    # (mostly) everything is overridden by the config.json
    # !!!!!!!!!!!!!!!!!!!!!! DO NOT EDIT !!!!!!!!!!!!!!!!!!! because of ^

    disableKeys = False # disable keys from socket
    # ^ can be disabled just in case, disables all socket info


class vars:
    xCoord = 5
    yCoord = 5
    currentSelection = 0 # index of programs list
    flipped = False
    icons = {}

    font = ImageFont.truetype('core/fonts/roboto.ttf', 11)
    flipperFontN = ImageFont.truetype('core/fonts/pixelop/PixelOperatorMono.ttf', 16)
    flipperFontB = ImageFont.truetype('core/fonts/pixelop/PixelOperatorMono-Bold.ttf', 16)
    flipperSelection = Image.open('./core/fonts/selection.bmp')
    microFont = ImageFont.truetype('core/fonts/pixelop/PixelOperatorMono8.ttf', 5)



if __name__ == "__main__":

    # villain setuo
    #Thread(target=opsys, args=("cd ./core/villain && sudo python3 villain.py &",), daemon=True).start()
    #print("[!] started villain; use fg to bring it to console")

    # 240x240 display with hardware SPI:

    #customizable.cleanScroll = a["cleanScroll"]
    #customizable.onlyPrefix = a["onlyPrefix"]
    #customizable.selectionBackgroundWidth = a["selectionBackgroundWidth"]
    #customizable.idleCycles = a["idleCycles"]
    #customizable.selectedPrefix = a["selectedPrefix"]
    #customizable.disableIdle = a["disableIdle"]

    customizable.screenType = config["menu"]["screenType"]

    # types of screens
    # "original": the original display i made
    # "flipper": the display based off a flipper zero
    # "minimalistic": the display based off the classic deauth watch - also really minimalistic, personal favorite

    """
    if a["enableWebServer"]:
        uStatus("starting webserver")

        #from flask import Flask, Response, send_file, request
        import core.controlPanel.cpanel as cpanel

        uSuccess("imported webserver")

        #cpanel.app.run(host="0.0.0.0", port=80)

        Thread(target=cpanel.run, args=("0.0.0.0",7979,), daemon=True).start()
    """

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

    image = Image.new('1', (disp.width, disp.height), "WHITE") # init display
    draw = ImageDraw.Draw(image) # dsiayp

    # load plugins
    plugPath = config["plugins"]["pluginsPath"]
    plugins = pwnhyvePluginLoader(folder=plugPath.replace("./", ""))
    plugins.moduleList += ["/"+x for x in os.listdir(plugPath) if os.path.isdir(plugPath+x) and not x.startswith("_")]
    currentDirectory = ""

    menus = pwnhyveDisplayLoader()

    currentDirectory = ""

    while 1:

        # interface for batteries n stuff
        #draw.text((6,0), "CPU:000", font=vars.microFont)
        #draw.text((16,0), "M:WL0", font=vars.microFont)
        #draw.text((24,0), "AP:SOLO0", font=vars.microFont)
        # TODO: make battery icons # finished


        try: # check if selection is out of range
            selection = plugins.moduleList[vars.currentSelection]
        except IndexError: # if it is
            vars.currentSelection -= 1 # failsafe
            selection = plugins.moduleList[vars.currentSelection - 1] # go back 1 (TODO: maybe remove)

        fullClear(draw)

        if customizable.screenType in list(menus.modules):
            b = menus.modules[customizable.screenType]

            listToPrint = b["module"].getItems(plugins.moduleList, vars.currentSelection)
            b["module"].display(draw, disp, image, GPIO, list(listToPrint), plugins, vars.yCoord, vars.xCoord, vars.currentSelection, selection, vars.icons)

            screenShow(disp, image, flipped=vars.flipped)
        

        # button stuff
        #pnd = plugins.moduleList + [x for x in os.listdir("./plugins") if os.path.isdir("./plugins/"+x)]
        pnd = plugins.moduleList
        while True:
            print('---' * 6)
            print(pnd)
            key = menu(draw, disp, image, pnd, GPIO, disableBack=currentDirectory=="")
            print('---' * 6)

            print(key)

            if key == None:
                a = currentDirectory.split("/")
                currentDirectory = '/'.join(a[:len(a)-1])
                
                print("backed to "+currentDirectory)

                if currentDirectory == "": # backed all the way
                    dire = (plugPath.replace("./", "")+currentDirectory).replace("//", "/") # what the fuck am i doin

                    plugins = pwnhyvePluginLoader(folder=dire)
                    pnd = plugins.moduleList + ["/"+x for x in os.listdir(plugPath) if os.path.isdir(plugPath+x) and not x.startswith("_")]

                continue
            
            print(os.listdir(plugPath+currentDirectory))
            if key in ['/'+x for x in os.listdir(plugPath+currentDirectory) if os.path.isdir("./plugins/"+x)]:

                # example directory structure

                # |- plugins
                #    |- test
                #    |  \ a.py
                #    |- test2
                #    |  \ b.py
                #    | c.py
                    
                currentDirectory += key
                print("forwarded to "+currentDirectory)
                fullClear(draw)
                draw.text((round(128/2), round(64/4)), "loading...")
                screenShow(disp, image)


                dire = (plugPath.replace("./", "")+currentDirectory+"/").replace("//", "/") # what the fuck am i doin
                plugins = pwnhyvePluginLoader(folder=dire) # "test"
                pnd = plugins.moduleList + ["/"+x for x in os.listdir(plugPath) if os.path.isdir("./plugins/"+x) and not x.startswith("_")]
                print(pnd)

                print('finished loading')
                break
            else: # raw plugin
                plugins.run(
                    plugins.getOriginModule(key),
                    key,
                    draw, disp, image, GPIO,
                    )
                break
