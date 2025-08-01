import os
import time

import core.cc1101.ccrf as ccrf
import core.cc1101.binary as binTranslate
import core.cc1101.flipsub as fsub

from core.plugin import BasePwnhyvePlugin 
from core.utils import IPC
from core.pil_simplify import tinyPillow

ui = IPC.WebUiLink("subghz")

rbyt = {}
sctext = ""
transceiverEnabled = False

def blinkerSub(sender, **kw):
    print(f"Caught signal from {sender!r}, data {kw!r}")

ui.subscribe(blinkerSub)

try:
    transceiver = ccrf.pCC1101()
    freq = transceiver.currentFreq
    strfrq = str(freq)[:3]
    transceiverEnabled = True
except:
    print("[+] CC1101 not detected")

def scText(text, caption, maxln=6):
    global sctext

    s = (sctext+"\n"+str(text)).strip().split("\n")
    lines = len(s)

    if lines > maxln-1:
        while len(s) > maxln-1:
            print("pop!")
            s.pop(0)
    elif lines != maxln-1:
        while len(s) != maxln-1:
            s.append("")

    s.append(caption)

    return '\n'.join(s)

def checkForTransciever(tpil:tinyPillow):

    if not transceiverEnabled:
        a = tpil.gui.screenConsole()
        a.addText("No CC1101 detected - this function is disabled")

        tpil.waitForKey()
        return False
    
    return True

class PWNsubGhz(BasePwnhyvePlugin):

    _icons = {
        "XCVR_Read_Raw": "./core/icons/router.bmp",
        "Set_XCVR_Power": "./core/icons/router.bmp",
        "Set_XCVR_Frequency": "./core/icons/router.bmp",
        "XCVR_Replay_Data": "./core/icons/routeremit.bmp",
        "Play_FM_Radio": "./core/icons/routeremit.bmp",
    }
    
    def XCVR_Read_Raw(tpil:tinyPillow):
        global freq, rbyt

        if not checkForTransciever(tpil): return

        transceiver.rst()

        a = tpil.gui.screenConsole()
        
        a.setText("setting CC1101 to RX...")
        a.addText("{}hz | RAW | RX".format(strfrq))

        transceiver.setupRawRecieve()

        time.sleep(1)

        """
        while True:
            a = transceiver.rawRecv(100)
            print(''.join([str(x) for x in a]))
            time.sleep(0.25)
        """
        
        #a.addText("hit any key to start RX")

        a.addText("hit any key to start recording")

        tpil.waitForKey()

        a.addText("hit any key to stop")
        
        transceiver.recvInf() # start reading

        while True:
            if tpil.checkIfKey():
                break

        bits = transceiver.recvStop()

        #print(hexs)


        """
        while True:
            a.text = "recording.."
            bits = transceiver.rawRecv(1000, uslp=0.5)
            a.text = "waiting.."
            z = disp.waitForKey()
            if z == disp.pinout["KEY_LEFT_PIN"]:
                break
        
        rbyt["data"] = bits
        """

        #a.addText("done recording")

        #disp.waitForKey()
        a.exit() 

        transceiver.csn(0)

        while True:
            mnu = tpil.gui.menu(["continue", "save to file", "retry", "view", "discard"], disableBack=True)

            if mnu == "save to file":

                octets = binTranslate.bitsToOctet(
                    bits
                )

                hexs = binTranslate.octetsToHex(octets)

                with open("./addons/subghz/"+tpil.gui.enterText(suffix=".sub"), "w") as f:
                    fdata = (
                        "Filetype: Flipper SubGhz RAW File",
                        "Version: 1",
                        "Frequency: {}".format(round(freq)),
                        "Preset: FuriHalSubGhzPresetOok650Async", # am i confident this is correct? fuck no
                        "Protocol: RAW",
                        "RAW_Data: {}".format(
                            ' '.join([str(x) for x in fsub.bitsToRawData(bits)])
                            ),
                        "HEX_Data: {}".format(" ".join(hexs)),
                        "BIT_Data: {}".format(' '.join([str(x) for x in bits]))
                    )
                    f.write("\n".join(fdata))
                    f.flush()

            elif mnu == "retry":
                PWNsubGhz.Read_Raw(tpil) # kids, don't do this
                return
            
            elif mnu == "view":

                byts = binTranslate.bitsToOctet(
                    binTranslate.deleteTrailingNull(bits)
                )

                hexs = binTranslate.octetsToHex(byts)

                a = tpil.gui.screenConsole()

                lines = []
                curline = []
                maxhexperline = 6

                elipsesAdded = False
                currentHexVal = -100

                for hexa in hexs:
                    if hexa == currentHexVal: # if current hexadecimal is the same as the most recent
                        if not elipsesAdded:
                            curline.append('...') # add elipses
                            elipsesAdded = True
                        
                        #continue
                    else: # if its not
                        if elipsesAdded: # but the most recent addition is elipses
                            if hexa == currentHexVal: # and if the current hex value is the same as the most recent hex value (NOT elipses)
                                print("unoriginal")
                                #continue # then continue, we don't want more elipses
                            else:
                                print("original")
                                elipsesAdded = False
                                curline.append(hexa)

                    currentHexVal = hexa

                    print(curline)

                    if len(curline) == maxhexperline:
                        lines.append(' '.join(curline))
                        curline.clear()
                        
                if len(curline) != 0:
                    lines.append(' '.join(curline))

                lines.append("EOF.")

                offset = 0

                while True:
                    selectedLines = lines[0+offset:6+offset]

                    a.text = '\n'.join(selectedLines)

                    a.update()
                    z = tpil.waitForKey()

                    if z == "down":
                        offset += 1 if selectedLines[0] != "EOF." else 0
                    elif z == "up":
                        offset -= 1 if offset != 0 else 0
                    elif z == "left":
                        break


                a.exit()
            
            elif mnu == "continue" or mnu == "discard":
                transceiver.sleepMode()
                return

    def Set_XCVR_Power(tpil:tinyPillow):
        if not checkForTransciever(tpil): return

        powerStrings = []

        for registerValue, dBm in transceiver.patable:
            powerStrings.append(
                "{} / {}".format(hex(registerValue), dBm)
            )

        registerValue = int(tpil.gui.menu(powerStrings).split(" ")[0], base=16)

        transceiver.adjustOOKSensitivity(0, registerValue)

    def XCVR_Replay_Data(tpil:tinyPillow):
        global strfrq, freq
        if not checkForTransciever(tpil): return

        fle = tpil.gui.menu(os.listdir("./addons/subghz"))

        fsubData = fsub.flipperConv("./addons/subghz/"+fle)
        print(".sub file frequency is at {}".format(fsubData["Frequency"]))

        transceiver.currentFreq = float(fsubData["Frequency"])
        transceiver.trs.set_base_frequency_hertz(transceiver.currentFreq)

        bitData = fsubData.rawDataToBits()


        a = tpil.gui.screenConsole()

        a.addText("preparing..")
        
        transceiver.setupRawTransmission()


        ########### calculate bin file ############
        binfile = ccrf.fio.calcBinFile(bitData, "/tmp/CC1101_TX.bin")

        while True:
            print('waiting...')
            a.text = scText("press dpad to play data\ndpad left to exit\nup, down to edit bit delay", "{}hz | TX".format(strfrq))
            a.forceUpdate()

            key = tpil.waitForKey(debounce=True)

            if key == 'press':
                a.text = scText("transmitting..", "{}hz | TX".format(strfrq))
                a.forceUpdate()

                time.sleep(0.25) # just for GPIO to\ finish writes

                print("transmitting")

                repeats = 0
                while True:
                    print("on transmission repeat {}".format(repeats))
                    transceiver.rawTransmitBin(binfile)
                    repeats += 1

                    print(f"base_frequency={(transceiver.trs.get_base_frequency_hertz() / 1e6):.2f}MHz",)
                    
                    if tpil.checkIfKey() == 'press':
                        continue
                    else:
                        break

                print("done transmitting")

            elif key == 'left':
                break

            elif key == 'up':
                slpval += 1
            elif key == 'down':
                slpval -= 1 if slpval != 0 else 0

        a.quit()
        transceiver.sleepMode()

        #transceiver.setFreq(beforefreq)
        #freq = beforefreq
        #strfrq = str(beforefreq)[:3]
        #transceiver.revertTransceiver()

    def Set_XCVR_Frequency(tpil:tinyPillow):
        global freq, strfrq

        if not checkForTransciever(tpil): return

        a = tpil.gui.setFloat("Frequency (300-950mhz)", _min=300.0, _max=950.0,
                              start=str(int(transceiver.currentFreq/1e6))+".000"
                              #    ^ round the float into an int       ^ then add THREE place values
                              ).start()

        transceiver.setFreq(a)

        print(f"base_frequency={(transceiver.trs.get_base_frequency_hertz() / 1e6):.2f}MHz",)