#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
TODO: clean this
"""

import os
import threading

# CD to script path
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

import sys
import time
from PIL import ImageFont
from core.utils import config
from core.plugin import *
from core.pil_simplify import tinyPillow
import core.bgworker as bgworker


if __name__ == "__main__":
    
    #region run usb gadget
    print("[USB] initializing usb gadget...")
    os.system("/bin/pwnhyveUSB")
    #endregion

    #region setup display driver
    screenType = config["menu"]["screenType"]
    
    menus = pwnhyveMenuLoader()
    selectedMenu = menus.modules[screenType]["module"]
    driverLoader = pwnhyveScreenLoader(config["display"]["driver"])

    if driverLoader.driver == None:
        driverLoader = pwnhyveScreenLoader("headless")

    dispDriver = driverLoader.driver
        

    print("[DISPLAY] initalizing display driver...", end="")

    disp = driverLoader.driver.DisplayDriver(selectedMenu)
    image, draw = disp.image, disp.draw
    tinypil = tinyPillow(draw, disp, image)

    print("initalized.\n")
    #endregion end of display setup

    #region load plugins
    print('[PLUGINS] initializing plugins and menus...', end="")
    plugPath = config["plugins"]["pluginsPath"]

    plugins = pwnhyvePluginLoader(folder=plugPath.replace("./", ""))

    plugins.moduleList += ["/"+x for x in os.listdir(plugPath) if os.path.isdir(plugPath+x) and not x.startswith("_")]
    currentDirectory = ""

    print("initalized.")
    #endregion end of plugin load

    #region load background threads

    usbThread = bgworker.ThreadedWorker(bgworker.USBNotifyWorker(), args=(tinypil,))
    usbThread.startWorker()

    #endregion

    print("[MENU] READY. HACK THE PLANET!")

    pluginsAndDirectories = plugins.moduleList
    previousModuleLoaded = None
    finishedLoading = False
    extraLoadingText = ""
    while 1:

        selection = 0
        disp.fullClear(draw)

        # button stuff
        fontSize = round(disp.height / 8)
        folders = ["/"+x for x in os.listdir(plugPath) if os.path.isdir("./"+plugPath) and not x.startswith("_") and ".py" not in x]
        while True:
            for folder in folders:
                plugins.icons[folder] = "./core/icons/folder.bmp"
                
            key = disp.gui.menu(
                pluginsAndDirectories, 
                disableBack=currentDirectory=="", 
                icons=plugins.icons
                )

            if key == None: # user entered back, so go back 1 directory
                a = currentDirectory.split("/")
                currentDirectory = '/'.join(a[:len(a)-1])
                
                if currentDirectory == "": # at main menu
                    for module, modulePtr in plugins.loadedPluginModules.copy().items(): # unload modules to save memory
                        del sys.modules[module]
                        del plugins.loadedPluginModules[module]
                        del modulePtr

                        try:
                            modulePtr.__dir__()
                        except Exception as e:
                            print("[UNLOADER] unloaded plugin \"{}\": {}".format(module, e))


                dire = (plugPath.replace("./", "")+currentDirectory).replace("//", "/") # what the fuck am i doin


                plugins = pwnhyvePluginLoader(folder=dire)
                pluginsAndDirectories = plugins.moduleList + ["/"+x for x in os.listdir(dire) if os.path.isdir("./"+dire) and not x.startswith("_") and ".py" not in x]

                #print("LDIR: {}".format(currentDirectory))
                continue
            
            # user selected a directory, so open the directory and load any plugins in it
            pluginPath = (plugPath+currentDirectory).replace("//", "/")
            if key in ['/'+pluginPathFolders for pluginPathFolders in os.listdir(pluginPath) if os.path.isdir(os.path.join(pluginPath, pluginPathFolders))]:

                # example directory structure

                # |- plugins
                #    |- test
                #    |  \ a.py
                #    |- test2
                #    |  \ b.py
                #    | c.py

                def threadedLoading(disp):
                    global finishedLoading
                    global extraLoadingText

                    loadings = [
                        "|", "/", "---", "\\", "|", "/", "---", "\\"
                    ]
                    loadingIndex = 0

                    while not finishedLoading:
                        if loadingIndex == len(loadings):
                            loadingIndex = 0

                        disp.fullClear(draw)
                        disp.draw.text((round(disp.width/2), round(disp.height/2)), loadings[loadingIndex], 
                                       font=ImageFont.truetype('core/fonts/roboto.ttf', 24), anchor="mm")
                        disp.draw.text((2, 2), extraLoadingText, 
                                       font=ImageFont.truetype('core/fonts/roboto.ttf', 12))
                        disp.screenShow()

                        loadingIndex += 1

                        time.sleep(0.25)

                    finishedLoading = False
                    extraLoadingText = ""
                    

                loadingThread = threading.Thread(target=threadedLoading, args=(disp,), daemon=True)
                loadingThread.start()
                    
                currentDirectory += key
                print("[MENU] loading "+currentDirectory)

                extraLoadingText = "Loading {}".format(currentDirectory)

                dire = (plugPath.replace("./", "")+currentDirectory+"/").replace("//", "/") # what the fuck am i doin
                
                plugins = pwnhyvePluginLoader(folder=dire) # "test"
                pluginsAndDirectories = plugins.moduleList + ["/"+x for x in os.listdir(dire) if os.path.isdir("./"+dire+"/"+x) and not x.startswith("_") and ".py" not in x]

                finishedLoading = True
                loadingThread.join()

                print('[MENU] finished loading')

                break
            
            else: # user selected a plugin module, so run the plugin module
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
