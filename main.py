#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
absolute shitshow of code
gpio code snippets are from waveshare docs
rest are mine
"""
import os
import time
from PIL import Image, ImageDraw, ImageFont
from core.utils import config
from core.plugin import *
#import json
#import threading
#import socket

pillowDebug = False # very not reliable, also laggy
enableWebServer = True

devOptions = False # enable dev options


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

    # setup display driver
    menus = pwnhyveMenuLoader()

    selectedMenu = menus.modules[customizable.screenType]["module"]

    driverLoader = pwnhyveScreenLoader(config["display"]["driver"])

    if driverLoader.driver == None:
        driverLoader = pwnhyveScreenLoader("headless")

    dispDriver = driverLoader.driver
        

    print("[DISPLAY] initalizing display driver...", end="")

    disp = driverLoader.driver.DisplayDriver(selectedMenu)
    GPIO, image, draw = disp.GPIO, disp.image, disp.draw

    print("initalized.\n")
    # end of display setup

    # load plugins
    print('[PLUGINS] initializing plugins and menus...', end="")
    plugPath = config["plugins"]["pluginsPath"]

    plugins = pwnhyvePluginLoader(folder=plugPath.replace("./", ""))

    plugins.moduleList += ["/"+x for x in os.listdir(plugPath) if os.path.isdir(plugPath+x) and not x.startswith("_")]
    currentDirectory = ""

    print("initalized.")
    # end of plugin load

    print("[MENU] READY. HACK THE PLANET!")

    pnd = plugins.moduleList
    while 1:

        # interface for batteries n stuff
        #draw.text((6,0), "CPU:000", font=vars.microFont)
        #draw.text((16,0), "M:WL0", font=vars.microFont)
        #draw.text((24,0), "AP:SOLO0", font=vars.microFont)
        # TODO: make battery icons # finished


        selection = 0
        disp.fullClear(draw)

        # button stuff
        #pnd = plugins.moduleList + [x for x in os.listdir("./plugins") if os.path.isdir("./plugins/"+x)]
        while True:
            key = disp.gui.menu(pnd, disableBack=currentDirectory=="")

            if key == None:
                a = currentDirectory.split("/")
                currentDirectory = '/'.join(a[:len(a)-1])
                
                #if currentDirectory == "": # backed all the way
                dire = (plugPath.replace("./", "")+currentDirectory).replace("//", "/") # what the fuck am i doin


                plugins = pwnhyvePluginLoader(folder=dire)
                pnd = plugins.moduleList + ["/"+x for x in os.listdir(dire) if os.path.isdir("./"+dire) and not x.startswith("_") and ".py" not in x]

                #print("LDIR: {}".format(currentDirectory))
                continue
            
            pt = (plugPath+currentDirectory).replace("//", "/")
            if key in ['/'+x for x in os.listdir(pt) if os.path.isdir(os.path.join(pt,x))]:

                # example directory structure

                # |- plugins
                #    |- test
                #    |  \ a.py
                #    |- test2
                #    |  \ b.py
                #    | c.py
                    
                currentDirectory += key
                print("[MENU] loading "+currentDirectory)
                disp.fullClear(draw)
                disp.draw.text((round(128/3), round(64/4)), "loading...", font=ImageFont.truetype('core/fonts/tahoma.ttf', 11))
                disp.screenShow()


                dire = (plugPath.replace("./", "")+currentDirectory+"/").replace("//", "/") # what the fuck am i doin
                
                plugins = pwnhyvePluginLoader(folder=dire) # "test"
                pnd = plugins.moduleList + ["/"+x for x in os.listdir(dire) if os.path.isdir("./"+dire) and not x.startswith("_") and ".py" not in x]

                print('[MENU] finished loading')

                break
            else: # raw plugin
                print("[MENU] running plugin \"{}\"".format(currentDirectory+"/"+key))
                print("[MENU] DISCLAIMER: unless this is an official pwnhyve plugin, any errors that come up after this message are NOT ASSOCIATED WITH PWNHYVE. CONTACT THE PLUGIN'S DEVELOPER TO FIX IT.")
                
                print("\n" + "/\\"*30)

                startPluginTime = time.time()
                plugins.run(
                    plugins.getOriginModule(key),
                    key,
                    draw, disp, image, GPIO,
                    )
                
                print("/\\"*30)

                print("\n[MENU] ran plugin \"{}\" - took {} seconds".format(currentDirectory+"/"+key, round(time.time()-startPluginTime, 3)))
                break
