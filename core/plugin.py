"""
plugin loading system
"""
import os
import importlib
  
plugins = {}

def load(folder="plugins"):
    r = {}

    for item in os.listdir(f"./{folder}"):
        if item == "plugin.py": continue
        if ".py" in item:
            
            item = item.replace('.py','')

            plugins[item] = importlib.import_module(f'{folder}.{item}')

            try:
                r[item] = (f'{item}.py', plugins[item].functions(), plugins[item])
            except AttributeError: # plugin script didnt have a functions() module
                print("{}.py doesn't have a \"functions()\" definition, contact plugin developer to add one; skipping for now...".format(item))
                continue
        
    return (plugins, r)

def run(target, arg, plugin):

    if plugin == None:
        err = 0
        for function in plugins:
            if target.replace(".py", "") in str(function):
                func = getattr(plugins[function], function, None)

                if func:
                    func(arg)
                    return True
                else:
                    err += 1

                if err == len(plugins):
                    raise AttributeError("function doesnt exist")
        

    else:
        err = 0
        try:
            func = getattr(plugin, target)
        except AttributeError:
            err += 1
        else:
            if not arg:
                func()
                return
            else:
                func(arg)
                return

        if err == len(plugins):
            raise AttributeError("function doesnt exist")