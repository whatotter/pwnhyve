import time

from core.cc1101._shared import get_instance as _get_cc1101

transceiver = _get_cc1101()
transceiverEnabled = transceiver is not None

from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow


class PWNSignalGen(BasePwnhyvePlugin):

    _icons = {
        "XCVR_Tone":      "./core/icons/tool.bmp",
    }

    def XCVR_Tone(tpil: tinyPillow):
        if not transceiverEnabled:
            _no_hw(tpil)
            return

        term = tpil.gui.screenConsole()
        #freq_mhz = tpil.gui.slider("Frequency MHz", minimum=300, maximum=1000)
        power_dbm = tpil.gui.slider("Power dBm", minimum=-30, maximum=10)

        term.addText("TX: {:.1f}MHz @ {}dBm".format(transceiver.currentFreq, power_dbm))
        term.addText("PRESS ANY KEY TO STOP")

        try:
            #transceiver.setFreq(float(freq_mhz))
            transceiver.setPowerdBm(power_dbm)
            _tx_cw()
            tpil.waitForKey()
        finally:
            transceiver.sleepMode()

def _no_hw(tpil):
    term = tpil.gui.screenConsole()
    term.addText("No CC1101 detected")
    tpil.waitForKey()


def _tx_cw():
    if not transceiver:
        return
    transceiver.setCarrier()