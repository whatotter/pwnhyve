import base64
import json
import os, subprocess
from flask import Flask, Response, send_from_directory, request
from flask_socketio import SocketIO
import pam as PAMAuth
from core.utils import *
from core.remotecontrol.util import *

app = Flask(__name__)
socketio = SocketIO(app) 

addons = []
sessions = {} # active user sessions
filesaveIDS = {
    # to prevent users from uploading to an arbitrary folder, let us pick the folder
    "payloads": "./addons/payloads",
    "plugins": "./addons/plugins"
}

ipc = IPC.WebUiLink("server") # this <-> plugins

def generateSession(token, u, p):
    global sessions

    sessions[token] = {
        "shell": ShellThread(u,p),
        "authenticated": True,
        "pbs": 0
    }

    return sessions[token]

#region flask stuff
@app.route("/")
def index():
    return open("./core/remotecontrol/site/control.html", "r").read()

@app.route("/pwa-manifest.json")
def pwa():
    #return open("./core/remotecontrol/manifest.json", "r").read()
    return Response(
        open("./core/remotecontrol/site/manifest.json", "r").read(), 
        status=200, headers={"Content-Type": "application/manifest+json"}
        )

@app.route("/active-plugins")
def plugins():
    files = []

    for file in worm("./addons/plugins"):
        if file[1] == "file": # [1] is the type
            if file[0].split("/")[-1].startswith("_") or "pycache" in file[0]:
                continue
            else:
                files.append(file[0])
            
    return Response(
        json.dumps(files), 
        status=200, headers={"Content-Type": "application/json"}
        )

@app.route("/available-payloads")
def payloads():
    files = {x: round(os.path.getsize("./addons/payloads/{}".format(x))/1000,2) for x in os.listdir("./addons/payloads")}
            
    return Response(
        json.dumps(files), 
        status=200, headers={"Content-Type": "application/json"}
        )

@app.route("/addons/<path:file>")
def webuiaddons(file):
    basedir = "/" + os.path.join(
            *os.path.dirname(__file__).split("/")[:-2]
            )

    try:
        #return open("./addons/webui/{}".format(file), "rb").read()
        return send_from_directory(os.path.join(basedir, "addons/webui"), file)
    except FileNotFoundError:
        return Response("404", status=404)

#catchall
@app.route("/<path:file>")
def files(file):
    try:
        #return open("./core/remotecontrol/site/{}".format(file), "rb").read()
        return send_from_directory("./site", file)
    except FileNotFoundError:
        return Response("404", status=404)
#endregion
    
#region socketio stuff
@socketio.on("connect")
def connection():
    uStatus("[WebUI] SIO client connected | token {}".format(request.sid))

@socketio.on("authenticate")
def auth(msg):
    username = msg.get("user", False)
    password = msg.get("pasw", False)

    if username and password:
        if PAMAuth.authenticate(username, password):
            uSuccess("[WebUI] SIO connection successfully authenticated")
            sessionItems = generateSession(request.sid, username, password)

            # return zero errors
            socketio.emit("authstatus", {"status": 0}, to=request.sid)

            # send available addons
            socketio.emit("addons", addons, to=request.sid)

            # wait for ssh term to load up and print stuff
            socketio.sleep(0.25)

            # send ssh buffer
            socketio.emit("sshbuf", {"buffer": sessionItems["shell"].buffer.decode('utf-8')}, to=request.sid)
        else:
            socketio.emit("authstatus", {"status": 2}, to=request.sid) # incorrect pass/user
    else:
        socketio.emit("authstatus", {"status": 1}, to=request.sid) # missing info

@socketio.on("disconnect")
def disconnect():
    token = request.sid

    uStatus("[WebUI] SIO connection closed")

    if token in sessions:
        shell = sessions[token]["shell"]
        shell.close()

        sessions[token] = {}

@socketio.on("ipc")
def ipcComm(msg):
    sessionToken = request.sid

    if sessionToken in sessions and sessions[sessionToken]["authenticated"] == True: # user is real
        data = {
            "data": msg["data"],
            "sid": sessionToken
        }

        ipc.send(data)

@socketio.on("location")
def locationUpdate(msg):
    sessionToken = request.sid

    if sessionToken in sessions and sessions[sessionToken]["authenticated"] == True: # user is real
        print(json.dumps(msg, indent=4))

@socketio.on("upload")
def file_upload(msg):
    sessionToken = request.sid

    if sessionToken in sessions and sessions[sessionToken]["authenticated"] == True: # user is real
        fileid = msg["id"]
        filename = msg["filename"]
        data = base64.b64decode(msg["data"])

        with open(os.path.join(filesaveIDS[fileid], filename), "wb") as f:
            f.write(data)
            f.flush()

        uSuccess('[WebUI] wrote to {}'.format(filename))

@socketio.on("reqsysinfo")
def sysinfo():
    sessionToken = request.sid

    if sessionToken in sessions and sessions[sessionToken]["authenticated"] == True: # user is real
        sysinfo = {
            "System Uptime": subprocess.getoutput("uptime").split("up")[0].strip(),
            "Kernel Version": subprocess.getoutput("uname -r"),
            "Interfaces": list(
                filter(
                    lambda x: True if x not in ["lo"] else False,
                    [x["ifname"] for x in json.loads(subprocess.getoutput("ip -j a"))]
                )
            ),
            "Connected to USB host": True if len(subprocess.getoutput("ls /dev/ | grep hidg")) > 0 else False,
            "Storage": subprocess.getoutput("df --output=avail --output=size -H \"/\" | tail -n 1").strip().replace("  ", " available from "),
            "Hostname": subprocess.getoutput("hostname")
        }

        socketio.emit("sysinfo", sysinfo, to=request.sid)

#region ssh control
@socketio.on("sshrx")
def ssh_write_byte(msg):
    # write to ssh terminal
    sessionToken = request.sid

    if sessionToken in sessions and sessions[sessionToken]["authenticated"] == True: # user is real
        shell = sessions[sessionToken]["shell"]
        shell.writeByte(msg["byte"].encode("utf-8"))

@socketio.on("sshreqtx")
def shellTransmitCallback():
    st = request.sid # st : session token

    if st in sessions and sessions[st]["authenticated"] == True: # user is real
        shell = sessions[st]["shell"]

        newBufferSize = len(shell.buffer)
        if newBufferSize > sessions[st]["pbs"]:
            newBufferText = shell.buffer[sessions[st]["pbs"]:newBufferSize]
            socketio.emit("sshtx", {"byte": newBufferText.decode('utf-8')}, to=request.sid)

            sessions[st]["pbs"] = newBufferSize
#endregion
#endregion 

def ipc2sio(sender, data):
    print("sender = {} data = {}".format(sender, data))
    socketio.emit("ipc", {"sender": sender, "data": data})

addons = loadAddons()
ipc.subscribe(ipc2sio)

if __name__ == "__main__":
    socketio.run(app, port=5000, host="0.0.0.0")