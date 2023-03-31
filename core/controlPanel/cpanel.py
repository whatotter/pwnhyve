#from core.badusb.badusb import BadUSB, DuckyScriptInterpreter
# refuses to import ANYTHING and says "no module named 'core'" and i cant figure it out
# if someone figures this out PLEASE tell me
# until then i will put the entire script in here

# TEMPORARILY FIXED
# but anything temporary can be permaneant if you try hard enough

#from core.badusb.badusb import BadUSB, DuckyScriptInterpreter
import os, sys
sys.path.insert(1, os.path.join(sys.path[0], 'core/controlPanel'))

import plugin as plgmanager

from flask import Flask, Response, send_file, request
import socket
import threading
import subprocess
import base64
import json
from hashlib import sha256
from time import sleep
import logging

try:
    import psutil
    windows = False
except ImportError:
    windows = True
import os

app = Flask(__name__)
#cwd = os.getcwd()
cwd = "./core/controlPanel"
loggedIn = []
loggedPWD = sha256(json.loads(open(f"{cwd}/config.json").read())["password"].encode('ascii')).hexdigest() # gyat

class system:
    def get_cpu_temp():
        if windows: return 0
        psutil.sensors_temperatures()["cpu_thermal"][0].current

    def shellExec(cmd, wait=False, basicSecurity=True):
        if basicSecurity:
            if ";" in cmd:
                cmd = cmd.split(";")[0]

            if "&" in cmd:
                cmd = cmd.split("&")[0]

        try:
            thread = threading.Thread(target=os.system, args=(cmd,), daemon=True)

            thread.start()

            if wait:
                thread.join()
            else:
                pass

            return True
        except:
            raise

    rceSock = None
    percentage = 0
    dsi = None

    sockCon = "" # deez nuts
    unixSock = None
    sockOutput = None
    closeSock = None


    pluginStop = False

@app.route("/")
def index():
    if request.remote_addr in loggedIn:
        return open(f"{cwd}/assets/index.html", "r").read()
    else:
        return open(f"{cwd}/assets/login.html", "r").read()

@app.route("/mobile")
def mobileIndex():
    return open(f"{cwd}/assets/mobile.html", "r").read()


@app.route("/main.css")
def css_sheet():
    return send_file(f"assets/css/main.css", mimetype='text/css')

@app.route("/mobile.css")
def mobileCSSSheet():
    return send_file(f"assets/css/mobile.css", mimetype='text/css')

@app.route("/toaster.css")
def toastercss():
    return send_file(f"assets/css/toastr.css", mimetype='text/css')

@app.route("/pureknob.js")
def pureknob():
    return send_file(f"assets/javascript/pureknob.js", mimetype='text/javascript')

@app.route("/toaster.js")
def toaster():
    return send_file(f"assets/javascript/toastr.js", mimetype='text/javascript')

@app.route("/main.js")
def mainjs():
    return send_file(f"assets/javascript/main.js", mimetype='text/javascript')


# icons

@app.route("/cloud.png")
def cloudICO():
    return send_file(f"assets/png/terminal.png", mimetype="image/png")

@app.route("/graph.png")
def graphICO():
    return send_file(f"assets/png/graph.png", mimetype="image/png")

@app.route("/main.png")
def mainICO():
    return send_file(f"assets/png/main.png", mimetype="image/png")

@app.route("/nowifi.png")
def deauthICO():
    return send_file(f"assets/png/deauth.png", mimetype="image/png")

@app.route("/nmap.png")
def nmapICO():
    return send_file(f"assets/png/nmap.png", mimetype="image/png")

@app.route("/usb.png")
def usbICO():
    return send_file(f"assets/png/usb.png", mimetype="image/png")

@app.route("/wifi.png")
def wifiICO():
    return send_file(f"assets/png/wifi.png", mimetype="image/png")

@app.route("/shutdown.png")
def shutdownpng():
    return send_file(f"assets/png/shutdown.png", mimetype="image/png")

@app.route("/restart.png")
def restartpng():
    return send_file(f"assets/png/restart.png", mimetype="image/png")

# api
@app.route("/api/login", methods=['GET','POST'])
def loginPost():
    password = request.get_json(force=True)["password"]

    b64pwd = base64.b64decode(password.encode('ascii'))
    sha256pwd = sha256(b64pwd).hexdigest()

    if sha256pwd == loggedPWD:
        loggedIn.append(request.remote_addr)
        print("{} logged in".format(request.remote_addr))
        return "1"
    else:
        return "0"

@app.route("/api/dumpInfo")
def postinfo():
    if request.remote_addr not in loggedIn:
        return ({"data": "no"})
    return ({
            "data": "ok",

            "pools": {
                "console": system.sockCon
            },

            "system": {
                "cpuPercent": psutil.cpu_percent(1.5) if not windows else 0,
                "ramPercent": psutil.virtual_memory()[2] if not windows else 0,
                "cpuTemp": round(psutil.sensors_temperatures()["cpu_thermal"][0].current) if not windows else 0,
            },

            "usbScripts": os.listdir(f"{cwd}/../../plugins/payloads/"),
        }
    )

@app.route("/api/plugins/show")
def pluginsShow():
    return {"plugins": vars.plugins, "icons": vars.icons}

@app.route("/api/plugins/console")
def pluginsConsole():
    return system.sockCon

@app.route("/api/plugins/input", methods=["GET", "POST"])
def pluginsInput():
    a = request.get_json(force=True)

    print(a)

    system.sockOutput = a["input"]

    print(system.sockOutput)
    
    return "1"

@app.route("/api/plugins/stop", methods=["GET", "POST"])
def pluginsStop():
    system.pluginStop = True

    while system.pluginStop:
        pass

    return "1"

@app.route("/api/plugins/run", methods=["GET", "POST"])
def pluginsRun():
    jsoN = request.get_json(force=True)

    system.sockCon = ""

    unixSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    closeSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    closeSock.bind(("127.0.0.1", 62118))
    unixSock.bind(("127.0.0.1", 62117))

    unixSock.listen(1)
    closeSock.listen(1)

    def unixSockThread(sock):
        """communication between this script and the plugin - moves all data from plugin to a variable so flask can send to user"""

        sock.settimeout(1)
        conn, addr = sock.accept()
        conn.settimeout(1)

        print("[!] got plugin connection")


        while True:
            try:
                abc = conn.recv(65536).decode('utf-8')

                if not abc or len(abc) == 0:
                    break

                abc += "\n"
            except ConnectionAbortedError:
                print("exited gracefully")
                system.sockCon += "\nPlugin abruptly disconnected - check for an error?\n"
                system.pluginStop = True
                break
            except TimeoutError:
                continue

            print(abc)

            if abc.strip() != "userIntervention":
                if abc.strip() == "exit":
                    print("exited data sock")
                    system.sockCon += "\nPlugin exited.\n"
                    system.pluginStop = True
                    quit()
                try:
                    system.sockCon += abc
                except:
                    pass # idk
            else:
                system.sockCon += ">>> "

                while system.sockOutput == None:
                    pass

                print(system.sockOutput)

                conn.sendall(system.sockOutput.encode("utf-8"))

                system.sockCon += system.sockOutput + "\n"

                system.sockOutput = None

        system.unixSock = None

    def closeSockThread(sock):
        """
        sends a (basically) SIGKILL command to the plugin to stop running

        when closeSock = True, this socket sends "exit" to plugin thread
        plugin thread stops everything, returns "ok" and quits
        if plugin abruptly quits and doesn't send "ok", catches it

        plugin must close unix sock/data sock first, and send "ok" before exitsocket.close()
        """
        conn, addr = sock.accept()

        print("[!] got plugin connection")

        while True:
            if system.pluginStop:
                try:
                    conn.sendall("exit".encode("utf-8"))
                except (BrokenPipeError, ConnectionAbortedError):
                    print("caught abrupt quit")
                    break
            try:
                if conn.recv(512).decode("utf-8") == "ok":
                    break
            except:
                print("caught abrupt quit")
                break
        
        system.pluginStop = False
        system.closeSock = None


    if system.unixSock != None:
        return "A plugin is already running."
    else:
        system.unixSock = unixSock
        system.closeSock = closeSock

        threading.Thread(target=unixSockThread, args=(unixSock,), daemon=True).start()
        threading.Thread(target=closeSockThread, args=(closeSock,), daemon=True).start()

    # once threads start, start plugin


    key = jsoN["plugin"]

    for p in vars.bigPlugins[1]: # for plugin in plugins list
        for executable in vars.bigPlugins[1][p][1]: # for every executable in the 
            if executable == key:
                plg = vars.bigPlugins[1][p][2] # chosen plugin

                print("running")
                threading.Thread(target=plgmanager.run, args=(key, [("127.0.0.1", 62117), ("127.0.0.1", 62118)], plg), daemon=True).start() # run it
                return "1"
    




class vars:
    plugins = {}
    icons = {}
    folders = []
    bigPlugins = None

def run(host, port):

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    #flask.cli.show_server_banner = lambda *args: None

    plugins = plgmanager.load(folder="webplugins") # load

    vars.bigPlugins = plugins

    for p in plugins[1]: # for plugin in plugins list
        if len(plugins[1][p][1]) == 0: continue # sanity check
        for executable in plugins[1][p][1]: # for every executable in the plugin's executable list
            if executable == "icons": continue
            vars.plugins[executable] = {} # create dict
            vars.icons[executable] = {} # create dict

            try:
                vars.icons[executable] = plugins[1][p][1]["icons"][executable].strip() # define icon
            except: #KeyError:
                vars.icons[executable] = None

            try:
                vars.plugins["{}".format(executable, plugins[1][p][0])]["help"] = (plugins[1][p][1][executable].strip(), plugins[1][p][0]) # define help

            except (KeyError, AttributeError): # command's help not in configurationfile
                vars.plugins[executable]["help"] = "I AM A FOLDER"
                vars.folders.append(executable)
                for item in plugins[1][p][1][executable]: # what the fuck
                    try:
                        a = plugins[1][p][1][executable][item]
                    except:
                        raise KeyError("{}'s command {} doesn't have a help key pair in it's configuration".format(plugins[1][p][0], executable))

                    try:
                        vars.icons[item] = plugins[1][p][1]["icons"][item].strip() # define icon
                    except: #KeyError:
                        vars.icons[item] = None

                    vars.plugins[executable][item] = a
                    #vars.plugins[executable]["help"] = a # define help

                    #print(vars.plugins[executable])
                    #print(vars.plugins)

    print("now running web server")

    app.run(port=port, host=host)