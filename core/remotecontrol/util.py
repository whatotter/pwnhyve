import json
import paramiko
import threading
from core.utils import *
import os

def worm(folder):
    for file in os.listdir(folder): # for every file in the folder
        joined = os.path.join(folder, file) # for later use

        if os.path.isdir(joined): # if it's a directory
            yield (joined, "folder") # yield that we've found a directory

            for actualFile in worm(joined): # call this function on the directory
                yield actualFile # and yield back everything it finds

        if os.path.isfile(joined): # if it's a file
            yield (joined, "file") # yield we found a file

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
        uStatus('[WebUI] [SSH] New shell active')
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

def loadAddons():
    base = "./addons/webui/"
    addons = os.listdir(base)
    existingAddons = []

    for addon in addons:
        if addon[0] == "_":
            continue
        
        items = os.listdir(
            os.path.join(base, addon)
            )
        
        if "main.html" in items and "manifest.json" in items:
            existingAddons.append({
                "path": "/addons/{}/main.html".format(addon),
                "manifest": json.loads(
                    open(
                        os.path.join(base, addon, "manifest.json")
                    ).read()
                )
            })

    print(existingAddons)
    return existingAddons