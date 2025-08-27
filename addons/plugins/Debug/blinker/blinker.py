from core.utils import IPC
from core.plugin import BasePwnhyvePlugin

ui = IPC.WebUiLink("blink")

def blinkerSub(sender, data):
    print(f"Caught signal from {sender}, data {data}")

ui.subscribe(blinkerSub)

class PWNBlinkerTest(BasePwnhyvePlugin):
    def wait(tpil):
        ui.send("blablablablalbal")
        print("waiting for blinker sub")
        tpil.waitForKey()
