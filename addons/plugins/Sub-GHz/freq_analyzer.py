import time
import math

from core.cc1101._shared import get_instance as _get_cc1101
transceiver = _get_cc1101()
transceiverEnabled = transceiver is not None

from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow


class PWNFreqAnalyzer(BasePwnhyvePlugin):

    _icons = {
        "Frequency_Analyzer":     "./core/icons/tool.bmp",
    }

    def Frequency_Analyzer(tpil: tinyPillow):
        if not transceiverEnabled:
            _no_hw(tpil)
            return

        from core.cc1101.protocols.modulation import Modulation

        term = tpil.gui.screenConsole()
        term.addText("Frequency Analyzer")
        term.addText("shows active freqs")

        freq_start = tpil.gui.slider("Start MHz", minimum=300, maximum=500)
        freq_end = tpil.gui.slider("End MHz", minimum=freq_start + 1, maximum=1000)

        mod_choice = tpil.gui.menu(["OOK", "2FSK"])
        mod = Modulation.OOK if mod_choice == "OOK" else Modulation.FSK2

        term.clearText()
        term.addText("scanning {:d}-{:d} MHz".format(freq_start, freq_end))
        term.addText("mod: " + mod_choice)
        term.addText("PRESS ANY KEY TO STOP")

        results = _scan_freqs(freq_start, freq_end, mod, term, tpil)

        term.clearText()
        if not results:
            term.addText("no signals found")
        else:
            term.addText("Active frequencies:")
            for f, rssi in results[:10]:
                bar = "#" * max(1, min(20, int((rssi + 120) / 3)))
                term.addText("{:.1f}MHz {:3.0f}dBm {}".format(f, rssi, bar))

        tpil.waitForKey()


def _no_hw(tpil):
    term = tpil.gui.screenConsole()
    term.addText("No CC1101 detected")
    tpil.waitForKey()


def _scan_freqs(f_start, f_end, mod, term, tpil):
    results = []
    step_mhz = 0.5
    f = f_start

    from core.cc1101.protocols.modulation import MOD_NAMES
    mod_name = MOD_NAMES.get(mod, "OOK")

    while f <= f_end:
        if tpil.checkIfKey():
            break

        freq_hz = int(f)
        try:
            transceiver.setFreq(freq_hz)
            if mod_name == "OOK":
                transceiver.setModulation(0)
            else:
                transceiver.setModulation(1)
            transceiver.setupRawRecieve()
            time.sleep(0.05)

            rssi = transceiver.readRSSI()
        except Exception:
            rssi = -120

        if rssi > -85:
            results.append((f, rssi))

        f += step_mhz

    transceiver.sleepMode()
    results.sort(key=lambda x: x[1], reverse=True)
    return results
