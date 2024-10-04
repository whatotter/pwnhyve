import os
import time
import core.cc1101.ccrf as ccrf
import core.cc1101.binary as binTranslate
import core.cc1101.flipsub as fsub
from core.plugin import BasePwnhyvePlugin 
import math

transceiver = ccrf.pCC1101()
freq = transceiver.currentFreq
strfrq = str(freq)[:3]

rbyt = {}

#transceiver.revertTransceiver()

sctext = ""
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

class PWNsubGhz(BasePwnhyvePlugin):

    icons = {
        "Read_Raw": "./core/icons/skullemit.bmp"
    }
    
    def Read_Raw(tpil):
        global freq, rbyt

        transceiver.rst()

        a = tpil.gui.screenConsole(tpil)
        
        a.text = (scText("setting CC1101 to RX...", "{}hz | RAW | RX".format(strfrq)))

        transceiver.setupRawRecieve()

        time.sleep(1)

        """
        while True:
            a = transceiver.rawRecv(100)
            print(''.join([str(x) for x in a]))
            time.sleep(0.25)
        """
        
        #a.addText("hit any key to start RX")

        a.text = scText("hit any key to start recording", "{}hz | RAW | RX".format(strfrq))

        tpil.waitForKey()

        a.text = scText("hit any key to stop", "{}hz | RAW | RX".format(strfrq))
        
        transceiver.recvInf() # start reading

        while True:
            if tpil.checkIfKey(key='p'):
                break

        bits = transceiver.recvStop()
        rbyt["data"] = bits

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

                byts = binTranslate.bitsToOctet(
                    binTranslate.deleteTrailingNull(bits)
                )

                hexs = binTranslate.bytesToHex(byts)

                with open("./subghz/"+tpil.gui.enterText(suffix=".sub"), "w") as f:
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
                        "BIT_Data: {}".format("".join(bits))
                    )
                    f.write("\n".join(fdata))
            elif mnu == "retry":
                PWNsubGhz.Read_Raw(tpil) # kids, don't do this
                return
            
            elif mnu == "view":

                byts = binTranslate.bitsToOctet(
                    binTranslate.deleteTrailingNull(bits)
                )

                hexs = binTranslate.bytesToHex(byts)

                a = tpil.gui.screenConsole(tpil)

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

                    z = tpil.waitForKey()

                    if z == "d":
                        offset += 1 if selectedLines[0] != "EOF." else 0
                    elif z == "u":
                        offset -= 1 if offset != 0 else 0
                    elif z == "l":
                        break


                a.exit()
            
            elif mnu == "discard":
                #rbyt.pop("data")
                return
            
            elif mnu == "continue":
                return

        pass

    def Set_Power(tpil):
        a = tpil.gui.slider(tpil, "OOK power", max_=255, start=0xc6).start()
        transceiver.adjustOOKSensitivity(0, a)

        print('[CC1101] set OOK power to {}'.format(a))

    def Replay_Data(tpil):
        global strfrq, freq

        fle = tpil.gui.menu(os.listdir("./subghz"))

        fsubData = fsub.flipperConv("./subghz/"+fle)
        print(".sub file frequency is at {}".format(fsubData["Frequency"]))
        transceiver.currentFreq = float(fsubData["Frequency"])
        RAW_Data = fsubData["RAW_Data"]

        a = tpil.gui.screenConsole(tpil)

        a.addText("preparing..")
        
        transceiver.rst()

        slpval = 5
        while True:
            print('waiting...')
            a.text = scText("press dpad to play data\ndpad left to exit\nup, down to edit bit delay", "{}hz | bit-delay: {} | TX".format(strfrq, slpval))
            a.forceUpdate()

            key = tpil.waitForKey(debounce=True)

            if key == 'p':
                a.text = scText("transmitting..", "{}hz | bit-delay: {} | TX".format(strfrq, slpval))
                a.forceUpdate()

                time.sleep(0.25) # just for GPIO to\ finish writes

                print("transmitting")

                repeats = 0
                while True:
                    print("on transmission repeat {}".format(repeats))
                    transceiver.flipperTransmit(RAW_Data)
                    repeats += 1
                    
                    if tpil.checkIfKey(key="press"):
                        continue
                    else:
                        break

                print("done transmitting")

            elif key == 'l':
                break

            elif key == 'u':
                slpval += 1
            elif key == 'd':
                slpval -= 1 if slpval != 0 else 0

        a.quit()

        #transceiver.setFreq(beforefreq)
        #freq = beforefreq
        #strfrq = str(beforefreq)[:3]
        #transceiver.revertTransceiver()

    def Set_Frequency(draw,disp,image,GPIO):
        global freq, strfrq
        a = disp.gui.setFloat(draw,disp,image,GPIO,"Frequency (300-950mhz)", _min=300.0, _max=950.0,
                              start=str(int(transceiver.currentFreq/1e6))+".000"
                              #    ^ round the float into an int       ^ then add THREE place values
                              ).start()

        print(a)
        freq2 = round(a, 2) 
        freqmath = eval("{}e6".format(freq2))
        print("{} vs {}".format(freq, freqmath))
        
        transceiver.currentFreq = freqmath
        transceiver.rst()

        freq = transceiver.currentFreq
        strfrq = str(freq)[:3]

        print(f"base_frequency={(transceiver.trs.get_base_frequency_hertz() / 1e6):.2f}MHz",)

    def Reset(draw,disp,image,GPIO):
        global freq, strfrq

        transceiver.rst()

        #freq = transceiver.trs.get_base_frequency_hertz()
        #strfrq = str(freq)[:3]