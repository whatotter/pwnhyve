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
        global frequency

        a = tpil.gui.screenConsole()
        a.setText("setting CC1101 to RX...")

        transceiver.setupRawRecieve()
        time.sleep(0.1)

        fftRatios = []
        maxFFTs = 52
        fftLineHeight = 1
        underlineTextIndex = 0

        frequency = round(transceiver.getFreqMHz(), 4)
        def drawFrequency():
            textWidth = 4
            textHeight = 10
            textOffset = 2

            textInitialX, textInitialY = 1,1

            # draw target frequency aswell
            tpil.text(
                [textInitialX,textInitialY], 
                f"{frequency:.3f}  MHz", 
                fontSize=16
                )
            
            if underlineTextIndex >= 3: # decimal point is in the way, so add to offset
                textInitialX += 2

            underlineStartX = textInitialX+(underlineTextIndex*(textOffset+textWidth))
            tpil.rect(
                [underlineStartX, textInitialY+textHeight], 
                [underlineStartX+textWidth, textInitialY+textHeight]
                )

        def interpretFrequencyChange(direction):
            global frequency

            value = 100 / (10**underlineTextIndex)

            print("changing value by {} (underlineTextIndex = {})".format(value, underlineTextIndex))

            transceiver.setFreq(frequency+(value*direction))
            frequency = round(transceiver.getFreqMHz(), 4)
            transceiver.setupRawRecieve() # redo this.. for some reason?


        def drawFFT():
            yCoord = 16

            xCoordCenter = 128/2
            maxFFTLineWidth = 64
            fftRatiosReversed = fftRatios.copy()[::-1]

            for fftRatio in fftRatiosReversed:
                fftLineWidth = maxFFTLineWidth*fftRatio
                fftHalfLineWidth = fftLineWidth/2

                tpil.rect(
                    [xCoordCenter-fftHalfLineWidth, yCoord], 
                    [xCoordCenter+fftHalfLineWidth, yCoord+fftLineHeight]
                    )
                yCoord += fftLineHeight

        a.exit()
        transceiver.setMS(5)
        while True:
            hasLiveBits = 0
            samplesToTake = 250

            samples = transceiver.recvSamples(samplesToTake, delayms=-1)

            for sample in samples:
                if sample:
                    hasLiveBits += 1

            if hasLiveBits and hasLiveBits > 10: # debug
                print("has live bits: {}/{} ({} ratio)".format(
                    hasLiveBits, samplesToTake,
                    hasLiveBits/samplesToTake
                ))

            fftRatios.append(hasLiveBits/samplesToTake) # save ratio of 1s and 0s
            fftRatios = fftRatios[-maxFFTs:] # get last 100 FFT ratios

            tpil.clear()
            drawFFT()
            drawFrequency()
            tpil.show()

            key = tpil.getKey(debounce=True)
            if key == "right":
                if 6 > underlineTextIndex:
                    underlineTextIndex += 1
            elif key == "left":
                if underlineTextIndex != 0:
                    underlineTextIndex -= 1
            elif key == "up":
                interpretFrequencyChange(1)
            elif key == "down":
                interpretFrequencyChange(-1)
            elif key == "press":
                break

        a.exit()


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
