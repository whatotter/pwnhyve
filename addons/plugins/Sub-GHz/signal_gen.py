import time

from core.cc1101._shared import get_instance as _get_cc1101

transceiver = _get_cc1101()
transceiverEnabled = transceiver is not None

from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow


class PWNSignalGen(BasePwnhyvePlugin):

    _icons = {
        "SG_CW_Tone":      "./core/icons/tool.bmp",
        "SG_Sweep":        "./core/icons/tool.bmp",
    }

    def SG_CW_Tone(tpil: tinyPillow):
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

    def SG_Sweep(tpil: tinyPillow):
        if not transceiverEnabled:
            _no_hw(tpil)
            return

        term = tpil.gui.screenConsole()
        f_start = tpil.gui.slider("Start MHz", start=400, minimum=300, maximum=500)
        f_end = tpil.gui.slider("End MHz", minimum=f_start + 1, maximum=1000, start=f_start + 50)
        power_dbm = tpil.gui.slider("Power dBm", minimum=-30, start=0, maximum=10)

        term.addText("sweep: {:.0f}-{:.0f}MHz".format(f_start, f_end))
        term.addText("PRESS ANY KEY TO STOP")

        transceiver.setupRawTransmission()

        try:
            transceiver.setPowerdBm(power_dbm)
            f = f_start
            while f <= f_end:
                if tpil.checkIfKey():
                    break
                transceiver.setFreq(float(f))
                transceiver.rawTransmitBits("11111111")
                time.sleep(0.01)
                f += 0.1
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


def _tx_modulated(pattern, mod_type):
    if not transceiver:
        return

    transceiver.setModulation(mod_type.lower())
    for _ in range(20):
        for b in pattern:
            if b:
                transceiver.setCarrier()
            else:
                transceiver.sleepMode()
            time.sleep(0.001)


def _gen_bit_pattern(choice):
    if choice == "10101010":
        return [1, 0, 1, 0, 1, 0, 1, 0] * 10
    elif choice == "11110000":
        return [1, 1, 1, 1, 0, 0, 0, 0] * 10
    else:
        import random
        return [random.randint(0, 1) for _ in range(80)]
