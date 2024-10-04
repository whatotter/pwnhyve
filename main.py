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
from core.pil_simplify import tinyPillow

class customizable:
    disableKeys = False # disable keys from socket

class vars:
    xCoord = 5
    yCoord = 5
    currentSelection = 0 
    flipped = False
    icons = {}

    font = ImageFont.truetype('core/fonts/roboto.ttf', 11)
    flipperFontN = ImageFont.truetype('core/fonts/pixelop/PixelOperatorMono.ttf', 16)
    flipperFontB = ImageFont.truetype('core/fonts/pixelop/PixelOperatorMono-Bold.ttf', 16)
    flipperSelection = Image.open('./core/fonts/selection.bmp')
    microFont = ImageFont.truetype('core/fonts/pixelop/PixelOperatorMono8.ttf', 5)



if __name__ == "__main__":

    customizable.screenType = config["menu"]["screenType"]

    # setup display driver
    menus = pwnhyveMenuLoader()

    selectedMenu = menus.modules[customizable.screenType]["module"]

    driverLoader = pwnhyveScreenLoader(config["display"]["driver"])

    if driverLoader.driver == None:
        driverLoader = pwnhyveScreenLoader("headless")

    dispDriver = driverLoader.driver
        

    print("[DISPLAY] initalizing display driver...", end="")

    disp = driverLoader.driver.DisplayDriver(selectedMenu)
    image, draw = disp.image, disp.draw
    tinypil = tinyPillow(draw, disp, image)

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

        selection = 0
        disp.fullClear(draw)

        # button stuff
        #pnd = plugins.moduleList + [x for x in os.listdir("./plugins") if os.path.isdir("./plugins/"+x)]
        fontSize = round(disp.height / 8)
        while True:
            key = disp.gui.menu(pnd, disableBack=currentDirectory=="", icons=plugins.icons)

            if key == None:
                # go back one folder in the directory path

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
                disp.draw.text((round(disp.width/3), round(disp.height/4)), "loading...", font=ImageFont.truetype('core/fonts/tahoma.ttf', fontSize))
                disp.screenShow()


                dire = (plugPath.replace("./", "")+currentDirectory+"/").replace("//", "/") # what the fuck am i doin
                
                plugins = pwnhyvePluginLoader(folder=dire) # "test"
                pnd = plugins.moduleList + ["/"+x for x in os.listdir(dire) if os.path.isdir("./"+dire+"/"+x) and not x.startswith("_") and ".py" not in x]

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
                    tinypil
                    )
                
                print("/\\"*30)

                print("\n[MENU] ran plugin \"{}\" - took {} seconds".format(currentDirectory+"/"+key, round(time.time()-startPluginTime, 3)))
                break
