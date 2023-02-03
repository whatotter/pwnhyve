#from core.badusb.badusb import BadUSB, DuckyScriptInterpreter
# refuses to import ANYTHING and says "no module named 'core'" and i cant figure it out
# if someone figures this out PLEASE tell me
# until then i will put the entire script in here

# TEMPORARILY FIXED
# but anything temporary can be permaneant if you try hard enough

from core.badusb.badusb import BadUSB, DuckyScriptInterpreter
from plugins.wifi import pwnagotchiHTML

from flask import Flask, Response, send_file, request
import socket
import threading
import subprocess
import base64
import json
from hashlib import sha256
from time import sleep

try:
    import psutil
except ImportError:
    windows = True
import os

app = Flask(__name__)
#cwd = os.getcwd()
cwd = "./core/controlPanel"
loggedIn = []
loggedPWD = sha256(json.loads(open(f"{cwd}/config.json").read())["password"].encode('ascii')).hexdigest()

class system:
    def get_cpu_temp():
        if windows: return 0
        psutil.sensors_temperatures()["cpu_thermal"][0].current

    def get_gpu_temp():
        if windows: return 0
        psutil.sensors_temperatures()["gpu_thermal"][0].current

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

    deauthPOOL = ""
    deauthCONSOLE = ""
    deauthJSON = None
    unixSock = None

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
                "deauth": system.deauthPOOL
            },

            "system": {
                "cpuPercent": psutil.cpu_percent(1.5) if not windows else 0,
                "ramPercent": psutil.virtual_memory()[2] if not windows else 0,
                "cpuTemp": round(psutil.sensors_temperatures()["cpu_thermal"][0].current) if not windows else 0,
                "gpuTemp": round(psutil.sensors_temperatures()["gpu_thermal"][0].current) if not windows else 0,
            },

            "usbScripts": os.listdir(f"{cwd}/../../plugins/payloads/"),

            "deauth": system.deauthJSON
        }
    )

@app.route("/api/badusb/scripts")
def usbInfo():
    return {"data": "ok",
            "scripts": os.listdir(f"{cwd}/../../plugins/payloads/")}

@app.route("/api/badusb/run", methods=['GET','POST'])
def usbRun():
    sn = request.get_json(force=True)["script"]

    class dsiEx():
        percentage = 0
        printed = ""

    if not windows:
        system.dsi = DuckyScriptInterpreter(BadUSB()).run(f"{cwd}/../../plugins/payloads/{sn}")
    else:
        system.dsi = dsiEx()

        for x in range(0,101):
            system.dsi.percentage = x
            system.dsi.printed += "abc\n"
            sleep(0.1)

        print("ok")

    print(sn)

    return "0"

@app.route("/api/badusb/dumpInfo")
def usbInfoDump():
    return {"data": "ok",
        "scripts": os.listdir(f"{cwd}/../../plugins/payloads/"),
        "percentageDone": system.dsi.percentage if system.dsi != None else "0",
        "console": system.dsi.printed
        }

@app.route("/api/badusb/clearPercentage")
def usbClearPercentage():
    system.dsi = None
    return {"data": "ok"}

@app.route("/api/clearPools")
def clearPools():
    system.wifiPOOL, system.arpPOOL, system.deauthPOOL = "", "", ""
    
    return {"data": "ok"}

@app.route("/api/commands/pwnagotchiStart")
def pwnStart():
    threading.Thread(target=pwnagotchiHTML, daemon=True).start()

    unixSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    unixSock.connect(("127.0.0.1", 62117))

    def unixSockThread(sock):
        while True:
            try:
                abc = sock.recv(65536).decode('utf-8')
            except ConnectionAbortedError:
                print("exited gracefully")
                return

            try:
                jsond = json.loads(abc)

                system.deauthCONSOLE = jsond["console"]
                system.deauthJSON = abc
                
            except:
                system.deauthPOOL += abc + "\n"


    system.unixSock = unixSock
    threading.Thread(target=unixSockThread, args=(unixSock,), daemon=True).start()

    return {"data": "ok"}

@app.route("/api/commands/pwnagotchiStop")
def pwnStop():

    system.unixSock.close()

    toExitSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    toExitSock.connect(("127.0.0.1", 62118))

    toExitSock.sendall("exit".encode("utf-8"))

    toExitSock.close()

    return {"data": "ok"}


@app.route("/api/commands/nmap")
def nmapRun():
    windows=True

    sn = request.get_json(force=True)["args"]

    if windows:
        cmd = ("cmd.exe /C nmap {} && echo #finish".format(sn)).split(" ")
    else:
        cmd = ("bash nmap {} && echo #finish".format(sn)).split(" ")

    temp = True
    isBreak = False
    a = 0

    p = subprocess.Popen(cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT)


    while temp:
        if isBreak: break
        a = 0
        for line in iter(p.stdout.readline, b''):
            if len(line.rstrip().decode('ascii')) != 0: yield line.decode('ascii')

            a += 1

            if len(line.rstrip().decode('ascii')) == 0:
                temp = not temp
                isBreak=True
                break

            if "#finish" in str(line.rstrip()):
                temp = not temp
                isBreak=True
                break

            if isBreak: break
        if a == 0:
            break # if no more new lines

    yield '01234'

    return



if __name__ == '__main__':

    #getLogger('werkzeug').disabled = True
    #flask.cli.show_server_banner = lambda *args: None

    app.run(port=80, host="0.0.0.0")