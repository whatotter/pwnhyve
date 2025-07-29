"""
plugin loading system
"""
import os
import importlib
from core.utils import *
from threading import Thread
from core.__basemenu__ import BasePwnhyveScreen
  
moduleDict = {}

class BasePwnhyvePlugin:
    def __init__(self):
        self.icon = None
        return None
    
class BasePwnhyveScreen(BasePwnhyveScreen):
    pass
    
class pwnhyveScreenLoader():
    """
    loads selected screen driver from ./core/screens

    folder: folder to load drivers from, defaults to "core/screens"
    """
    def __init__(self, driver, folder="core/displayDrivers",):
        r = {}

        self.driver = None
        for item in os.listdir(f"./{folder}"):
            if ".py" in item and driver in item:

                #uWarn("[ScreenLoader] Attempting to load display driver \"{}\"".format(item))
                
                item = item.replace('.py','')
                iport = f'{folder.replace("/", ".")}.{item}'
                moduleDict[item] = importlib.import_module(iport)

                self.driver = moduleDict[item]
                #uSuccess("[ScreenLoader] Loaded")
                return
            
        uAlert("[ScreenLoader] couldn't find the display driver, none loaded - this WILL cause issues")
            


class pwnhyveMenuLoader():
    """
    loads custom screens from ./addons/menus folder.
    seperate from "pwnhyvePluginLoader" for compatibility and less confusion, even though they're 99% the same

    folder: folder to load GUIs from, defaults to "addons/menus"
    """
    def __init__(self, folder="addons/menus",):
        r = {}

        for item in os.listdir(f"./{folder}"):
            if ".py" in item:
                
                item = item.replace('.py','')

                moduleDict[item] = importlib.import_module(f'{folder.replace("/", ".")}.{item}')

                z = moduleDict[item]
                r[item] = {"module": z}
            
        self.modules = r

class pwnhyvePluginLoader():
    """
    pwnhyve's plugin loader, using a single class instead of a functions function (yuck!)

    folder: folder to load plugins from, defaults to "plugins"
    enableThreading: enables threading when you call a plugin's function, to prevent errors on the main thread, which would completely brick the pi's display
    """
    def __init__(self, folder:str="plugins", enableThreading:bool=True):
        r = {}
        allIcons = {}
        self.loadedPluginModules = {} # variable to reference modules loaded by this class only, not every module loaded

        if folder.startswith("./"):
            folder = folder[2:] # remove the "./"

        if not folder.endswith("/"):
            folder += "/" # this is stupid, but needed

        for item in os.listdir(f"./{folder}"):
            if ".py" in item:
                
                item = item.replace('.py','')
                if len(item) == 0:
                    continue

                importfolder = folder.replace("/", ".")

                pythonImport = "{}{}".format(importfolder, item).replace("..", ".")


                uWarn("[PluginLoader] loading plugin \"{}\"".format(pythonImport))
                moduleDict[item] = importlib.import_module(pythonImport)
                self.loadedPluginModules[pythonImport] = moduleDict[item]

                objects = [x for x in dir(moduleDict[item]) if x.startswith("PWN") or x == "Plugin"]

                for x in objects:
                    #z = moduleDict[item].Plugin()
                    z = getattr(moduleDict[item], x) # plugin class

                    try:
                        icons = getattr(z, '_icons')
                    except:
                        icons = {}

                    r[item+"::"+x] = {"functions": [y for y in dir(z) if not y.startswith("_")], "module": z, "icons": icons}
                    allIcons.update(icons)

                    uWarn("[PluginLoader] loading class \"{}\"".format(item+"::"+x))
            
        self.th = enableThreading

        self.modules = r
        self.moduleList = []
        self.icons = allIcons

        for k,v in self.modules.items():
            self.moduleList += v["functions"]

    def run(self, plugin:object, target:str, *args, **kwargs):
        """
        run a command using it's class and function name, alongside args

        plugin: class/object the function is in, for example "MyClass"
        target: the function in that object to call, for example "MyFunction"
        *args: passed to the called function
        **kwargs: passed to the called function

        returns the function passed, for example the actual object of "MyFunction"
        """
        func = getattr(plugin, target)
        if self.th:
            thread = Thread(target=func, args=args, kwargs=kwargs, daemon=True)
                
            thread.start()
            thread.join()

        else:
            func(*args, **kwargs)
        
        return func
    
    def getOriginModule(self, function):
        """
        gets the class/object that a function came from, for calling, used in conjunction with self.run()

        function: function to find

        returns False if not found, returns the object otherwise
        """

        for k,v in self.modules.items():
            if function in list(v["functions"]):
                return v["module"]
        return False
    
    def mergeWithFolder(self, folder, overlap=False):
        """
        merge current object with new folder, sometimes used if there's an update

        folder: folder to read from and update
        overlap: if to overlap already loaded functions - for example: if 'abcd' already exists, add another 'abcd' if it's found again

        returns the pwnhyvePluginLoader object for that function
        """

        # actually merge the folder
        a = pwnhyvePluginLoader(folder=folder)
        self.modules.update(a.modules)

        # redo modulelist
        self.moduleList = []
        for k,v in self.modules.items():
            if overlap:
                self.moduleList += v["functions"]
            else:
                for x in v["functions"]:
                    if x not in self.moduleList:
                        self.moduleList.append(x) # isn't in modulelist
                    else:
                        ... # is already in modulelist

        return a # return new, added folder