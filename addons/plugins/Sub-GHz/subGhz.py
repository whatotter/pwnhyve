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
    strfrq = str(int(freq / 1e6))
    transceiverEnabled = True
except Exception:
    print("[+] CC1101 not detected")

def scText(text, caption, maxln=6):
    global sctext
    s = (sctext + "\n" + str(text)).strip().split("\n")
    lines = len(s)
    if lines > maxln - 1:
        while len(s) > maxln - 1:
            s.pop(0)
    elif lines != maxln - 1:
        while len(s) != maxln - 1:
            s.append("")
    s.append(caption)
    return '\n'.join(s)

def checkForTransciever(tpil: tinyPillow):
    if not transceiverEnabled:
        a = tpil.gui.screenConsole()
        a.addText("No CC1101 detected - this function is disabled")
        tpil.waitForKey()
        return False
    return True

def _syncFreqDisplay():
    global freq, strfrq
    freq = transceiver.currentFreq
    strfrq = str(int(freq / 1e6))

class PWNsubGhz(BasePwnhyvePlugin):

    _icons = {
        "XCVR_Read_Raw":         "./core/icons/router.bmp",
        "Set_XCVR_Power":        "./core/icons/router.bmp",
        "Set_XCVR_Frequency":    "./core/icons/router.bmp",
        "XCVR_Replay_Data":      "./core/icons/routeremit.bmp",
        "Play_FM_Radio":         "./core/icons/routeremit.bmp",
    }

    # ── Read / Record ──────────────────────────────────────────────

    def XCVR_Read_Raw(tpil: tinyPillow):
        global freq, rbyt

        if not checkForTransciever(tpil):
            return

        a = tpil.gui.screenConsole()
        a.setText("setting CC1101 to RX...")
        a.addText("{} MHz | RAW | RX".format(strfrq))

        transceiver.setupRawRecieve()
        time.sleep(1)

        a.addText("hit any key to start recording")
        tpil.waitForKey()

        a.addText("recording... hit any key to stop")

        transceiver.recvInf()

        while True:
            if tpil.checkIfKey():
                break

        bits = transceiver.recvStop()
        a.exit()

        while True:
            mnu = tpil.gui.menu(
                ["continue", "save to file", "retry", "view", "discard"],
                disableBack=True,
            )

            if mnu == "save to file":
                octets = binTranslate.bitsToOctet(bits)
                hexs = binTranslate.octetsToHex(octets)

                name = tpil.gui.enterText(suffix=".sub")
                path = os.path.join(".", "addons", "subghz", name)
                with open(path, "w") as f:
                    fdata = (
                        "Filetype: Flipper SubGhz RAW File",
                        "Version: 1",
                        "Frequency: {}".format(round(freq)),
                        "Preset: FuriHalSubGhzPresetOok650Async",
                        "Protocol: RAW",
                        "RAW_Data: {}".format(
                            " ".join(str(x) for x in fsub.bitsToRawData(bits))
                        ),
                        "HEX_Data: {}".format(" ".join(hexs)),
                        "BIT_Data: {}".format(" ".join(str(x) for x in bits)),
                    )
                    f.write("\n".join(fdata))
                    f.flush()

            elif mnu == "retry":
                PWNsubGhz.XCVR_Read_Raw(tpil)
                return

            elif mnu == "view":
                byts = binTranslate.bitsToOctet(
                    binTranslate.deleteTrailingNull(bits)
                )
                hexs = binTranslate.octetsToHex(byts)

                a = tpil.gui.screenConsole()
                lines = _formatHexView(hexs)
                offset = 0

                while True:
                    selectedLines = lines[offset:offset + 6]
                    a.text = '\n'.join(selectedLines)
                    a.update()
                    z = tpil.waitForKey()

                    if z == "down":
                        if selectedLines and selectedLines[0] != "EOF.":
                            offset += 1
                    elif z == "up":
                        offset = max(0, offset - 1)
                    elif z == "left":
                        break

                a.exit()

            elif mnu in ("continue", "discard"):
                transceiver.sleepMode()
                return

    # ── Power ──────────────────────────────────────────────────────

    def Set_XCVR_Power(tpil: tinyPillow):
        if not checkForTransciever(tpil):
            return

        powerStrings = []
        for registerValue, dBm in transceiver.patable.items():
            powerStrings.append("{} / {}".format(hex(registerValue), dBm))

        choice = tpil.gui.menu(powerStrings)
        registerValue = int(choice.split(" ")[0], base=16)
        transceiver.adjustOOKSensitivity(0, registerValue)

    # ── Replay ─────────────────────────────────────────────────────

    def XCVR_Replay_Data(tpil: tinyPillow):
        global strfrq, freq

        if not checkForTransciever(tpil):
            return

        subdir = os.path.join(".", "addons", "subghz")
        try:
            files = os.listdir(subdir)
        except FileNotFoundError:
            a = tpil.gui.screenConsole()
            a.addText("no subghz/ directory found")
            tpil.waitForKey()
            return

        fle = tpil.gui.menu(files)
        fsubData = fsub.flipperConv(os.path.join(subdir, fle))

        try:
            subFreq = float(fsubData["Frequency"])
        except (KeyError, ValueError):
            a = tpil.gui.screenConsole()
            a.addText("invalid or missing frequency in .sub file")
            tpil.waitForKey()
            return

        transceiver.currentFreq = subFreq
        transceiver.setFreq(subFreq, doCalc=False)
        _syncFreqDisplay()

        bitData = fsubData.rawDataToBits()

        a = tpil.gui.screenConsole()
        a.addText("preparing..")

        transceiver.setupRawTransmission()

        binfile = ccrf.fio.calcBinFile(bitData, "/tmp/CC1101_TX.bin")
        slpval = 500

        while True:
            a.text = scText(
                "press dpad to play data\ndpad left to exit\nup, down to edit bit delay ({}ns)".format(slpval),
                "{} MHz | TX".format(strfrq),
            )
            a.forceUpdate()

            key = tpil.waitForKey(debounce=True)

            if key == 'press':
                a.text = scText("transmitting..", "{} MHz | TX".format(strfrq))
                a.forceUpdate()

                time.sleep(0.25)

                repeats = 0
                while True:
                    print("transmission repeat {}".format(repeats))
                    transceiver.rawTransmitBin(binfile)
                    repeats += 1

                    print("freq={:.2f} MHz".format(transceiver.getFreqMHz()))

                    if tpil.checkIfKey() == 'press':
                        continue
                    else:
                        break

                print("done transmitting")

            elif key == 'left':
                break

            elif key == 'up':
                slpval += 100
            elif key == 'down':
                slpval = max(100, slpval - 100)

        a.exit()
        transceiver.sleepMode()

    # ── Frequency ──────────────────────────────────────────────────

    def Set_XCVR_Frequency(tpil: tinyPillow):
        global freq, strfrq

        if not checkForTransciever(tpil):
            return

        startFreq = "{:.3f}".format(transceiver.currentFreq / 1e6)
        a = tpil.gui.setFloat(
            "Frequency (300-950 MHz)",
            _min=300.0,
            _max=950.0,
            start=startFreq,
        ).start()

        transceiver.setFreq(a)
        _syncFreqDisplay()

        print("freq={:.2f} MHz".format(transceiver.getFreqMHz()))


# ── Helper: format hex data for scrolling view ─────────────────────

def _formatHexView(hexs, maxPerLine=6):
    lines = []
    curline = []
    prevVal = None
    skipped = False

    for h in hexs:
        if h == prevVal:
            if not skipped:
                curline.append("...")
                skipped = True
            continue

        skipped = False
        curline.append(h)
        prevVal = h

        if len(curline) == maxPerLine:
            lines.append(" ".join(curline))
            curline = []

    if curline:
        lines.append(" ".join(curline))
    lines.append("EOF.")
    return lines
