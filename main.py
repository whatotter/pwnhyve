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
from core.utils import *
from core.plugin import *
from core.pil_simplify import tinyPillow
import core.bgworker as bgworker


if __name__ == "__main__":

    initializeLogfile()
    
    #region run usb gadget
    uWarn("[USB] initializing usb gadget...")
    os.system("/bin/pwnhyveUSB")

    print("")
    #endregion

    #region setup display driver
    print("")
    screenType = config["menu"]["screenType"]
    
    uWarn("[Display] DisplayDriver target = {}".format(config["display"]["driver"]))
    uWarn("[Display] Attempting to load..")

    menus = pwnhyveMenuLoader()
    selectedMenu = menus.modules[screenType]["module"]
    driverLoader = pwnhyveScreenLoader(config["display"]["driver"])

    if driverLoader.driver == None:
        driverLoader = pwnhyveScreenLoader("headless")

    dispDriver = driverLoader.driver

    disp = driverLoader.driver.DisplayDriver(selectedMenu)
    image, draw = disp.image, disp.draw
    tinypil = tinyPillow(draw, disp, image)

    uSuccess("[Display] ...loaded.\n")
    #endregion end of display setup

    #region load plugins
    uWarn('[Plugins] initializing plugins and menus...')
    basePluginsPath = config["plugins"]["pluginsPath"]

    plugins = pwnhyvePluginLoader(folder=basePluginsPath.replace("./", ""))

    uSuccess("...initalized.\n")
    #endregion end of plugin load

    #region load background threads

    WorkerThreads = [
        bgworker.ThreadedWorker(bgworker.USBNotifyWorker(), args=(tinypil,)),
        bgworker.ThreadedWorker(bgworker.WebUIWorker(), args=(tinypil,))
    ]

    for worker in WorkerThreads:
        worker.startWorker()

    #endregion

    print("")
    uSuccess("READY. HACK THE PLANET!")
    print("")

    pluginsAndDirectories = plugins.moduleList + getFolders(basePluginsPath)
    finishedLoading = False
    extraLoadingText = ""
    currentDirectory = ""
    while True:

        disp.fullClear(draw)

        # button stuff
        fontSize = round(disp.height / 8)
        folders = getFolders(basePluginsPath)
        while True:
            for folder in folders: # set default folder icon
                plugins.icons[folder] = "./core/icons/folder.bmp"
                
            # ask user what they want (this is the menu, plugins and dirs)
            userChoice = disp.gui.menu(
                pluginsAndDirectories, 
                disableBack=currentDirectory=="", 
                icons=plugins.icons
                )

            if userChoice == None: # user entered back, so go back 1 directory
                foldersSplit = currentDirectory.split("/") # "one/two/three" -> [one, two, three]
                currentDirectory = '/'.join(
                    foldersSplit[:len(foldersSplit)-1] # pop last ([one, two])
                    ) # join back together ("one/two")
                
                if currentDirectory == "": # at main menu
                    for module, modulePtr in plugins.loadedPluginModules.copy().items(): # unload modules to save memory
                        del sys.modules[module]
                        del plugins.loadedPluginModules[module]
                        del modulePtr

                        try:
                            modulePtr.__dir__()
                        except Exception as e:
                            print("[UNLOADER] unloaded plugin \"{}\": {}".format(module, e))

                # calculate our new directory
                newFullDirectory = robustJoin(
                    basePluginsPath,
                    currentDirectory
                    )

                # load plugins in that new directory
                plugins = pwnhyvePluginLoader(
                    folder=newFullDirectory
                    )
                
                # merge folders and plugins tg
                pluginsAndDirectories = plugins.moduleList + getFolders(newFullDirectory)

                continue
            
            # if the users choice is a folder in the directory we're currently in,
            if userChoice in getFolders( robustJoin(basePluginsPath, currentDirectory), base=""):
                # load that folder

                currentDirectory = robustJoin(currentDirectory, userChoice) # join the directory we want with the path we have

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
                    
                # do the loading stuff
                loadingThread = threading.Thread(target=threadedLoading, args=(disp,), daemon=True)
                loadingThread.start()
                print("[MENU] loading "+currentDirectory)
                extraLoadingText = "Loading {}".format(currentDirectory)

                # calculate our full directory (pwd type)
                newFullDirectory = robustJoin(
                    basePluginsPath,
                    currentDirectory
                    )

                # load plugins in that directory
                plugins = pwnhyvePluginLoader(
                    folder=newFullDirectory
                    ) # "test"
                
                # merge loaded modules and folders
                pluginsAndDirectories = plugins.moduleList + getFolders(newFullDirectory)

                # stop loading
                finishedLoading = True
                loadingThread.join()
                print('[MENU] finished loading')

                continue
            
            else: # user selected a plugin module, so run the plugin module
                print("[MENU] running plugin \"{}\"".format(currentDirectory+"/"+userChoice))
                print("[MENU] DISCLAIMER: unless this is an official pwnhyve plugin, any errors that come up after this message are NOT ASSOCIATED WITH PWNHYVE. CONTACT THE PLUGIN'S DEVELOPER TO FIX IT.")
                
                print("\n" + "/\\"*30)

                startPluginTime = time.time()
                plugins.run(
                    plugins.getOriginModule(userChoice),
                    userChoice,
                    tinypil
                    )
                
                print("/\\"*30)

                print("\n[MENU] ran plugin \"{}\" - took {} seconds".format(currentDirectory+"/"+userChoice, round(time.time()-startPluginTime, 3)))
                continue
