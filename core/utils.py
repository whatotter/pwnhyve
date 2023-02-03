try:
    import keyboard
except ImportError:
    keyboardDisabled = True

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

class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

def uStatus(string, **kwargs):
    print("[+] {}".format(string), **kwargs)

def uError(string, **kwargs):
    print("[ERROR] {}".format(string), **kwargs)

def uSuccess(string, **kwargs):
    print("[SUCCESS] {}".format(string), **kwargs)

def uInput(string, **kwargs):
    return input("[?] {}".format(string), **kwargs)


class enableInterrupt():
    def __init__(self, socket):
        self.getch = _Getch()
        self.socket = socket

    def start(self):
        a = self.getch().decode('ascii')

        if a == "\x03":
            self.socket.close()
            return

class fakeGPIO():
    """
    for debugging when pi is not available
    """
    def __init__(self, gpioPins):
        self.gpioPins = gpioPins
        return

    def input(self, key):

        print("{}: {}".format(key, not keyboard.is_pressed(key)))

        return not keyboard.is_pressed(key)
