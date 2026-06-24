import os
import time

import core.cc1101.binary as binTranslate
import core.cc1101.flipsub as fsub
from core.cc1101._shared import get_instance as _get_cc1101
from core.cc1101.protocols.registry import build_default_registry
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow


class PWNRAWTools(BasePwnhyvePlugin):

    _icons = {
        "Signal_Browser":    "./core/icons/router.bmp",
        "RT_Info":      "./core/icons/router.bmp",
        "RT_Convert":   "./core/icons/router.bmp",
        "RT_Replay":    "./core/icons/router.bmp",
    }

    def Signal_Browser(tpil: tinyPillow):
        subdir = os.path.join(".", "addons", "subghz")
        try:
            files = _list_sub_files(subdir)
        except FileNotFoundError:
            term = tpil.gui.screenConsole()
            term.addText("no subghz/ directory")
            tpil.waitForKey()
            return

        while True:
            fle = tpil.gui.menu(files + ["[back]"])
            if fle == "[back]":
                return

            path = os.path.join(subdir, fle)
            fsubData = fsub.flipperConv(path)
            term = tpil.gui.screenConsole()
            term.addText("File: " + fle)

            for key in ["Frequency", "Preset", "Protocol"]:
                val = fsubData.get(key, fsubData.p.get(key))
                if val:
                    line = "{}: {}".format(key, str(val)[:60])
                    term.addText(line)

            choice = tpil.gui.menu(["Delete Signal", "Analyze Signal", "Isolate Signal", "back"])
            if choice == "Delete Signal":
                os.remove(path)
                files = _list_sub_files(subdir)
                term.addText("deleted")
                tpil.waitForKey()
            elif choice == "Analyze Signal":
                raw_data = fsubData.get("RAW_Data")
                if raw_data:
                    pulses = [int(x) for x in raw_data.split(" ") if x]
                    reg = build_default_registry()
                    results = reg.recognize(pulses)

                    if results:
                        tpil.gui.toast(["Protocol Analysis:"] + [str(r) for r in results])
                    else:
                        tpil.gui.toast(["No protocols matched."])
                else:
                    term.addText("no RAW_Data in file")
                tpil.waitForKey()
            elif choice == "Isolate Signal":
                raw_data = fsubData.get("RAW_Data")
                if not raw_data:
                    term.addText("no RAW_Data in file")
                    tpil.waitForKey()
                else:
                    pulses = [int(x) for x in raw_data.split(" ") if x]
                    before = len(pulses)
                    while pulses and pulses[0] < 0:
                        pulses.pop(0)
                    while pulses and pulses[-1] < 0:
                        pulses.pop()
                    trimmed = " ".join(str(p) for p in pulses)
                    after = len(pulses)
                    cut = before - after
                    with open(path, "w") as f:
                        fsubData.sset("RAW_Data", trimmed)
                        for k in ["Filetype", "Version", "Frequency", "Preset", "Protocol"]:
                            v = fsubData.get(k)
                            if v is not None:
                                f.write("{}: {}\n".format(k, v))
                        f.write("RAW_Data: " + trimmed + "\n")
                    tpil.gui.toast("Trimmed {} bits".format(cut))
                    tpil.waitForKey()
            else:
                return

    def Signal_Library_Info(tpil: tinyPillow):
        subdir = os.path.join(".", "addons", "subghz")
        try:
            files = _list_sub_files(subdir)
        except FileNotFoundError:
            term = tpil.gui.screenConsole()
            term.addText("no subghz/ directory")
            tpil.waitForKey()
            return

        term = tpil.gui.screenConsole()
        total = len(files)
        ook = fsk = raw = 0
        for fname in files:
            path = os.path.join(subdir, fname)
            try:
                d = fsub.flipperConv(path)
                proto = d.get("Protocol", "")
                if "RAW" in proto.upper():
                    raw += 1
                elif "FSK" in proto.upper():
                    fsk += 1
                else:
                    ook += 1
            except Exception:
                pass

        term.addText("Sub-GHz Library")
        term.addText("Total files: " + str(total))
        term.addText("OOK: " + str(ook) + "  FSK: " + str(fsk))
        term.addText("RAW: " + str(raw))
        tpil.waitForKey()

def _list_sub_files(subdir):
    return sorted([f for f in os.listdir(subdir) if f.endswith(".sub") or f.endswith(".txt")])


def _pulses_to_bits(pulses, fsub_data):
    bit_data = fsub_data.get("BIT_Data")
    if bit_data:
        return [int(b) for b in bit_data.replace(" ", "")]
    return fsub.bitsToRawData(fsub.rawDataToBits(pulses))
