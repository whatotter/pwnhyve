import time
import os

import core.cc1101.binary as binTranslate
import core.cc1101.flipsub as fsub
from core.cc1101._shared import get_instance as _get_cc1101
from core.cc1101.protocols.registry import build_default_registry
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow

transceiver = _get_cc1101()
transceiverEnabled = transceiver is not None


class PWNSignalID(BasePwnhyvePlugin):

    _icons = {
        "ID_Live_Signal":    "./core/icons/router.bmp",
        "ID_From_File":      "./core/icons/router.bmp",
        "ID_From_Bits":      "./core/icons/router.bmp",
    }

    def ID_Live_Signal(tpil: tinyPillow):
        if not transceiverEnabled:
            _no_hw(tpil)
            return

        reg = build_default_registry()
        term = tpil.gui.screenConsole()
        term.addText("setting CC1101 to RX...")
        transceiver.setupRawRecieve()
        transceiver.recvInf()
        time.sleep(0.5)

        term.addText("recording... press any key to stop")
        while True:
            if tpil.checkIfKey():
                break

        bits = transceiver.recvStop()
        transceiver.sleepMode()

        pulses = fsub.bitsToRawData(bits)

        results = reg.recognize(pulses)

        if results:
            for r in results:
                term.addText(str(r))
        else:
            term.addText("no protocol matched")
            term.addText("raw data saved to file anyway")

        save_path = _save_signal(bits, pulses)
        term.addText("saved: " + save_path)

        tpil.waitForKey()

    def ID_From_File(tpil: tinyPillow):
        subdir = os.path.join(".", "addons", "subghz")
        try:
            files = os.listdir(subdir)
        except FileNotFoundError:
            term = tpil.gui.screenConsole()
            term.addText("no subghz/ directory")
            tpil.waitForKey()
            return

        fle = tpil.gui.menu(files)
        fsubData = fsub.flipperConv(os.path.join(subdir, fle))

        raw_data = fsubData.get("RAW_Data")
        pulses = None
        bits = None

        if raw_data:
            pulses = [int(x) for x in raw_data.split(" ") if x]
        else:
            bit_data = fsubData.get("BIT_Data")
            if bit_data:
                bits = [int(x) for x in bit_data.split(" ") if x]

        reg = build_default_registry()
        term = tpil.gui.screenConsole()
        term.addText("analyzing: " + fle)

        if pulses:
            results = reg.recognize(pulses)
        elif bits:
            hex_str = binTranslate.octetsToHex(binTranslate.bitsToOctet(bits))
            term.addText("no RAW_Data, showing bits")
            term.addText("Bits: " + "".join(str(b) for b in bits))
            term.addText("Hex: " + hex_str)
            results = []
        else:
            term.addText("no RAW_Data or BIT_Data found")
            tpil.waitForKey()
            return

        if results:
            for r in results:
                term.addText(str(r))
        else:
            term.addText("no protocol matched")

        tpil.waitForKey()

    def ID_From_Bits(tpil: tinyPillow):
        term = tpil.gui.screenConsole()
        term.addText("enter hex string or bit string")
        term.addText("hex: AA BB CC")
        term.addText("bits: 10101010")
        inp = tpil.gui.enterText()
        bits = _parse_input(inp)
        if not bits:
            term.addText("could not parse input")
            tpil.waitForKey()
            return

        hex_str = binTranslate.octetsToHex(binTranslate.bitsToOctet(bits))
        known_protocols = _match_by_bitlen(len(bits))
        term.addText("Bits: " + str(len(bits)))
        term.addText("Hex: " + hex_str)
        if known_protocols:
            term.addText("Possible: " + ", ".join(known_protocols))
        else:
            term.addText("No protocol matches this bit length")

        tpil.waitForKey()


def _match_by_bitlen(bit_count):
    from core.cc1101.protocols.princeton import PrincetonDecoder
    from core.cc1101.protocols.came import CameDecoder
    from core.cc1101.protocols.holtek import HoltekDecoder
    from core.cc1101.protocols.nice_flo import NiceFloDecoder
    from core.cc1101.protocols.keeloq import KeeLoqDecoder
    from core.cc1101.protocols.somfy import SomfyTelisDecoder
    from core.cc1101.protocols.intertechno import IntertechnoDecoder
    from core.cc1101.protocols.secplus_v1 import SecPlusV1Decoder
    matches = []
    for cls in [PrincetonDecoder, CameDecoder, HoltekDecoder, NiceFloDecoder,
                KeeLoqDecoder, SomfyTelisDecoder, IntertechnoDecoder, SecPlusV1Decoder]:
        if hasattr(cls, "min_count_bit") and bit_count == cls.min_count_bit:
            matches.append(cls.name)
    return matches


def _no_hw(tpil):
    term = tpil.gui.screenConsole()
    term.addText("No CC1101 detected")
    tpil.waitForKey()


def _save_signal(bits, pulses):
    subdir = os.path.join(".", "addons", "subghz")
    os.makedirs(subdir, exist_ok=True)
    ts = str(int(time.time()))
    path = os.path.join(subdir, "signal_" + ts + ".sub")
    hex_str = " ".join(binTranslate.octetsToHex(binTranslate.bitsToOctet(bits)))
    with open(path, "w") as f:
        f.write("\n".join([
            "Filetype: Flipper SubGhz RAW File",
            "Version: 1",
            "Frequency: {}".format(round(transceiver.currentFreq) if transceiverEnabled else 0),
            "Preset: FuriHalSubGhzPresetOok650Async",
            "Protocol: RAW",
            "RAW_Data: " + " ".join(str(p) for p in pulses),
            "HEX_Data: " + hex_str,
            "BIT_Data: " + " ".join(str(b) for b in bits),
        ]))
    return path


def _parse_input(inp):
    inp = inp.strip()
    if not inp:
        return None
    if all(c in "01 " for c in inp):
        return [int(b) for b in inp.replace(" ", "")]
    try:
        raw = inp.replace(" ", "").replace("0x", "").replace(",", "")
        bits = ""
        for h in raw:
            v = int(h, 16)
            bits += format(v, "04b")
        return [int(b) for b in bits]
    except ValueError:
        pass
    return None
