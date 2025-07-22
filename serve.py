import base64
import json
import os
import subprocess
import threading
from flask import Flask, Response, send_from_directory, request
from flask_socketio import SocketIO
import paramiko
import pam as PAMAuth

app = Flask(__name__)
socketio = SocketIO(app, async_mode='gevent')
sessions = {}
filesaveIDS = {
    # to prevent users from uploading to an arbitrary folder, let us pick the folder
    "payloads": "./payloads",
    "plugins": "./plugins"
}

class ShellThread():
    def __init__(self, username, password) -> None:
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect("127.0.0.1", username=username, password=password)

        self.chnl = self.ssh.invoke_shell()

        self.stdin = self.chnl.makefile('wb')
        self.stdout = self.chnl.makefile("r")

        self.buffer = b""

        self.byteCallback = None

        threading.Thread(target=self.read, daemon=True).start()

    def writeByte(self, byte:bytes):
        self.stdin.write(byte)
        #self.stdin.flush()

    def read(self):
        print('[paramiko] [+] reading thread active')
        while True:
            byte = self.stdout.read(1)

            if self.byteCallback != None:
                self.byteCallback(byte)

            self.buffer += byte

            if len(self.buffer.split(b"\n")) >= 1000:
                self.buffer = b'\n'.join( self.buffer.split(b"\n")[1000:] )

    def close(self):
        self.chnl.close()
        self.ssh.close()

def generateSession(token, u, p):
    global sessions

    sessions[token] = {
        "shell": ShellThread(u,p),
        "authenticated": True,
        "pbs": 0
    }

    return sessions[token]

def worm(folder):
    for file in os.listdir(folder): # for every file in the folder
        joined = os.path.join(folder, file) # for later use

        if os.path.isdir(joined): # if it's a directory
            yield (joined, "folder") # yield that we've found a directory

            for actualFile in worm(joined): # call this function on the directory
                yield actualFile # and yield back everything it finds

        if os.path.isfile(joined): # if it's a file
            yield (joined, "file") # yield we found a file

@app.route("/")
def index():
    return open("./core/remotecontrol/control.html", "r").read()

@app.route("/pwa-manifest.json")
def pwa():
    #return open("./core/remotecontrol/manifest.json", "r").read()
    return Response(
        open("./core/remotecontrol/manifest.json", "r").read(), 
        status=200, headers={"Content-Type": "application/manifest+json"}
        )

@app.route("/active-plugins")
def plugins():
    files = []

    for file in worm("./plugins"):
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
    files = {x: round(os.path.getsize("./payloads/{}".format(x))/1000,2) for x in os.listdir("./payloads")}
            
    return Response(
        json.dumps(files), 
        status=200, headers={"Content-Type": "application/json"}
        )

#catchall
@app.route("/<path:file>")
def files(file):
    try:
        #return open("./core/remotecontrol/{}".format(file), "rb").read()
        return send_from_directory("./core/remotecontrol/", file)
    except FileNotFoundError:
        return Response("404", status=404)
    
# SSH functions
@socketio.on("connect")
def connection():
    print("[+] sio client connected | token {}".format(request.sid))

@socketio.on("authenticate")
def auth(msg):
    username = msg.get("user", False)
    password = msg.get("pasw", False)

    if username and password:
        if PAMAuth.authenticate(username, password):
            sessionItems = generateSession(request.sid, username, password)
            socketio.sleep(0.25)
            socketio.emit("authstatus", {"status": 0}, to=request.sid) # no errors
            socketio.emit("sshbuf", {"buffer": sessionItems["shell"].buffer.decode('utf-8')}, to=request.sid)
        else:
            socketio.emit("authstatus", {"status": 2}, to=request.sid) # incorrect pass/user
    else:
        socketio.emit("authstatus", {"status": 1}, to=request.sid) # missing info

@socketio.on("disconnect")
def disconnect():
    token = request.sid

    print("disconnect")

    if token in sessions:
        shell = sessions[token]["shell"]
        shell.close()
        print("shell closed")

        sessions[token] = {}

@socketio.on("sshrx")
def ssh_write_byte(msg):
    sessionToken = request.sid

    if sessionToken in sessions and sessions[sessionToken]["authenticated"] == True: # user is real
        shell = sessions[sessionToken]["shell"]
        shell.writeByte(msg["byte"].encode("utf-8"))

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

        print('[+] wrote to {}'.format(filename))

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

previousBufferSize = 0
@socketio.on("sshreqtx")
def shellTransmitCallback():
    st = request.sid # st : session token

    if st in sessions and sessions[st]["authenticated"] == True: # user is real
        shell = sessions[st]["shell"]

        newBufferSize = len(shell.buffer)
        if newBufferSize > sessions[st]["pbs"]:
            newBufferText = shell.buffer[sessions[st]["pbs"]:newBufferSize]
            socketio.emit("sshtx", {"byte": newBufferText.decode('ascii')}, to=request.sid)

            sessions[st]["pbs"] = newBufferSize
        

#shell.byteCallback = shellTransmitCallback

#threading.Thread(target=shellTransmitCallback, daemon=True).start()
#socketio.start_background_task(shellTransmitCallback)

#threading.Thread(target=shell.constRead, daemon=True).start()
#shell.constRead()
#app.run(host="0.0.0.0")
    
socketio.run(app, port=5000, host="0.0.0.0")