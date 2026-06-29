import os
import time

import core.cc1101.ccrf as ccrf
import core.cc1101.binary as binTranslate
import core.cc1101.flipsub as fsub
from core.cc1101.protocols.registry import build_default_registry

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

"""
try:
    transceiver = ccrf.pCC1101()
    freq = transceiver.currentFreq
    strfrq = str(int(freq / 1e6))
    transceiverEnabled = True
except Exception:
    print("[+] CC1101 not detected")
"""

from core.cc1101._shared import get_instance as _get_cc1101
try:
    transceiver = _get_cc1101()
    freq = transceiver.currentFreq
    strfrq = str(int(freq / 1e6))
except:
    transceiver = None
    freq = 0
    strfrq = "0"

transceiverEnabled = transceiver is not None


def scText(text, caption, maxln=5):
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
        "Read_Raw_Signal":         "./core/icons/router.bmp",
        "XCVR_Power":        "./core/icons/router.bmp",
        "XCVR_Frequency":    "./core/icons/router.bmp",
        "Replay_Signals":      "./core/icons/routeremit.bmp",
        "FM_Transmit":         "./core/icons/routeremit.bmp",
    }

    # ── Read / Record ──────────────────────────────────────────────

    def Read_Raw_Signal(tpil: tinyPillow):
        global freq, rbyt

        if not checkForTransciever(tpil):
            return

        term = tpil.gui.screenConsole()

        term.clearText()
        transceiver.setupRawRecieve()
        time.sleep(0.1)

        term.addText(f"RXing @ {transceiver.getFreqMHz():.3f}MHz")
        term.addText(f"Hit 'Left' to exit.")
        term.addText(f"Waiting on your key..")

        key = tpil.waitForKey()
        if key == "left":
            return

        term.clearText()
        term.addText("Recording signal")
        term.addText("Press any key to stop.")

        transceiver.recvInf(ns=1000)

        while True:
            if tpil.checkIfKey():
                break

        bits = transceiver.recvStop()

        term.exit()
        transceiver.sleepMode()

        while True:
            mnu = tpil.gui.menu(
                ["Save to File", "Retry", "View", "Discard", "Identify"],
                disableBack=True,
            )

            if mnu == "Save to File":
                name = tpil.gui.enterText(suffix=".sub")

                octets = binTranslate.bitsToOctet(bits)
                hexs = binTranslate.octetsToHex(octets)
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

            elif mnu == "Retry":
                PWNsubGhz.XCVR_Read_Raw(tpil)
                return

            elif mnu == "View":
                a = tpil.gui.screenConsole()

                byts = binTranslate.bitsToOctet(
                    binTranslate.deleteTrailingNull(bits)
                )
                hexs = binTranslate.octetsToHex(byts)

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
                    elif z == "3":
                        tpil.gui.toast([
                            "Up/Down: Scroll",
                            "Left: Exit"
                            ])

                a.exit()

            elif mnu == "Identify":
                identTerm = tpil.gui.screenConsole()

                reg = build_default_registry()

                pulses = fsub.bitsToRawData(bits)
                results = reg.recognize(pulses)

                if results:
                    for r in results:
                        identTerm.addText(str(r))
                else:
                    identTerm.addText("No protocol matched.")

                tpil.waitForKey()
                identTerm.exit()

            elif mnu in ("Continue", "Discard"):
                transceiver.sleepMode()
                return

    # ── Power ──────────────────────────────────────────────────────

    def XCVR_Power(tpil: tinyPillow):
        if not checkForTransciever(tpil):
            return

        powerStrings = []
        for registerValue, dBm in transceiver.patable.items():
            powerStrings.append("{} / {}".format(hex(registerValue), dBm))

        choice = tpil.gui.menu(powerStrings)
        registerValue = int(choice.split(" ")[0], base=16)
        transceiver.adjustOOKSensitivity(0, registerValue)

    # ── Replay ─────────────────────────────────────────────────────

    def Replay_Signals(tpil: tinyPillow):
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
        slpval = 250

        while True:
            a.text = scText(
                "Bit delay ({}ns)".format(slpval),
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
                    transceiver.rawTransmitBin(binfile, ns=slpval)
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

            elif key == "3":
                tpil.gui.toast("L3: Transmit (repeat while held)\nUp: Increase bit delay\nDown: Decrease bit delay\nLeft: Exit")

        a.exit()
        transceiver.sleepMode()

    # ── Frequency ──────────────────────────────────────────────────

    def XCVR_Frequency(tpil: tinyPillow):
        global freq, strfrq

        if not checkForTransciever(tpil):
            return

        startFreq = "{:.3f}".format(transceiver.currentFreq / 1e6)
        a = tpil.gui.setFloat(
            "Frequency (300-950 MHz)",
            _min=300.0,
            _max=950.0,
            start=startFreq,
        )

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
