import os
import sys
import toml
import datetime
import blinker

config = {}

stdout = sys.stdout
stderr = sys.stderr
ansiReset = "\033[0m"

logfile = open("pwnhyve.log", "a")

class redir:
    """
    redirect all prints to a log
    """

    log = []

    def write(string):
        global stdout, logfile

        modstr = string

        redir.log.append(modstr)
        logfile.write(modstr)

        stdout.write(modstr)
        if len(modstr) != 0 and (modstr[-1] == b"\n" or modstr[-1] == "\n"):
            stdout.write("\r")

        logfile.flush()
        
    def flush():
        global stdout, logfile
        stdout.flush()
        logfile.flush()


class redirERR:
    """
    redirect all errors to a log
    """

    def write(string):
        global stderr, logfile

        modstr = string

        redir.log.append(modstr)
        logfile.write(modstr)

        stderr.write(modstr)
        if len(modstr) != 0 and (modstr[-1] == b"\n" or modstr[-1] == "\n"):
            stderr.write("\r")

        logfile.flush()

    def flush():
        global stderr, logfile
        stderr.flush()
        logfile.flush()


sys.stdout = redir
sys.stderr = redirERR


class BaseIPC:
    def __init__(self, myname: str, signame: str) -> None:
        self.signalName = signame
        self.me = myname
        self.sig = blinker.signal(self.signalName)
        self.sig.connect(self.__intermediary__)

        self.subs = []
        self.recent = None
        pass

    def __intermediary__(self, sender, **kw):
        """
        prevents signals from looping to ourselves
        """
        if kw["from"] == self.me:
            return
        else:
            self.recent = kw
            for sub in self.subs:
                sub(sender, kw)

    def subscribe(self, func):
        """
        subscribe a function to the IPC tunnel, so when
        something is transmitted through, the data will
        be immediately sent to subscribed functions
        """
        return self.subs.append(func)

    def send(self, data) -> list:
        """
        send data to the IPC tunnel
        """
        return self.sig.send(self.signalName, **{"from": self.me, "data": data})

    def recv(self):
        """
        return the most recent thing sent
        """
        return self.recent


class IPC:
    class WebUiLink(BaseIPC):
        def __init__(self, myname: str) -> None:
            super().__init__(myname, "webui")

    class WorkerLink(BaseIPC):
        def __init__(self, myname: str) -> None:
            super().__init__(myname, "worker")

    class BaseIPC(BaseIPC):
        def __init__(self, myname: str, signame:str) -> None:
            super().__init__(myname, signame)


def ppANSI(string, ansi) -> str:
    """
    append ansi code to words wrapped in square brackets
    """
    words = string.split(" ")
    pretty = []

    for word in words:
        if word.startswith("[") and word.endswith("]"):
            pretty.append(ansi + word + ansiReset)
        else:
            pretty.append(word)

    string = " ".join(pretty)

    return string


def getChunk(chunkingList, divisor):
    returnList = []
    temp = []
    for x in range(0, len(chunkingList)):
        if x != divisor:
            temp.append(chunkingList[x])
        else:
            returnList.append([x for x in temp])
            temp = []
            temp.append(chunkingList[x])
            returnList.append([x for x in temp])

    return returnList


def uStatus(string, **kwargs):
    print(ppANSI("[+] " + string, "\033[0;36m"), **kwargs)


def uError(string, **kwargs):
    print("[ERROR] {}".format(string), **kwargs)


def uWarn(string, **kwargs):
    """
    warn
    ("[!]", yellow)
    """

    print(ppANSI("[!] " + string, "\033[0;33m"), **kwargs)


def uAlert(string, **kwargs):
    """
    alert
    "[!!!]", red
    """

    print(ppANSI("[X] " + string, "\033[0;31m"), **kwargs)


def uBright(string, **kwargs):
    """
    important, but not too important
    "[+]", white underline
    """
    print(ppANSI("[+] " + string, "\033[4;37m"), **kwargs)


def uGood(string, **kwargs):
    """
    success, kinda
    "[+]", green
    """
    print(ppANSI("[+] " + string, "\033[0;32m"), **kwargs)


def uSuccess(string, **kwargs):
    """
    success
    "[+]", green
    """
    print(ppANSI("[+] " + string, "\033[0;32m"), **kwargs)


def uInput(string, **kwargs):
    """
    i really don't know what this would be used for..
    """
    return input("[?] {}".format(string), **kwargs)


def lprint(stri):
    """
    write to the log, but don't print
    """
    sys.stdout.write(stri)


def robustJoin(*args: str) -> str:
    """cuz os.path.join is kinda stupid"""

    cleaned = []
    for folder in args:
        if folder.startswith("/"):
            cleaned.append(folder[1:])
        else:
            cleaned.append(folder)

    return os.path.join(*cleaned).replace("//", "/")


def getFolders(folder, base="./"):
    """returns only folders, prefixed with "/" """
    return [
        "/" + x
        for x in os.listdir(folder)
        if os.path.isdir(base + folder) and not x.startswith("_") and ".py" not in x
    ]


def initializeLogfile():
    logfile.write(
        "{} log started at {} {}\n\n".format(
            "/\\" * 6, str(datetime.datetime.now()), "/\\" * 6
        )
    )


config = toml.loads(open("./config.toml").read())
