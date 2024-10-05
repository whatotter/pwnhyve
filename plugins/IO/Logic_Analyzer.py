import os
import time
import core.cc1101.binary as binTranslate
from core.plugin import BasePwnhyvePlugin 
import math
from core.pil_simplify import tinyPillow

def calcHZ(ns):
    return 1/(ns/(1*10**9))

def localizeHZ(hz):
    val = "Hz"
    div = 1

    if hz >= 1_000:
        val = "kHz"
        div = 1_000

    if hz >= 1_000_000:
        val = "mHz"
        div = 1_000_000

    return "{}{}".format(hz/div, val)

def samplesToCSV(channel1:list, channel2:list, filename:str="samples.csv"):
    """
    turn captured samples into CSV format for sigrok
    """

    csv = open(filename, "w")

    length = len(channel1) if len(channel1) >= len(channel2) else len(channel2) # pick whichever is bigger (samples should be the same length anyways)
    for index in range(length):
        s1, s2 = channel1[index], channel2[index]
        
        csv.write("{},{}".format(s1,s2))

    csv.flush()

    return filename



class PWNLA(BasePwnhyvePlugin):
    def Logic_Analyzer(tpil:tinyPillow):
        global xCoord, previousBit

        CH1_HIGH = tpil.resizeCoordinate2Res(1)
        CH1_LOW = tpil.resizeCoordinate2Res(CH1_HIGH + 10)

        CH2_HIGH = tpil.resizeCoordinate2Res(24)
        CH2_LOW = tpil.resizeCoordinate2Res(CH2_HIGH + 10)

        keyLegends = tpil.gui.keyLegend(tpil, {"left": "", "right": "", "up": "+", "down": "-", "1": "REC"})

        previousBit = None

        startX = 4
        xCoord = startX

        bitWidth = 16
        bitTime = 100 # in ns

        dataset = { # this should be immutable - never change this - our dataset
            "ch1": [0,1,1,0,1,0,1,0]*8,
            "ch2": [1,1,1,0,1,0,1,1]*8
        }
        samplesRecorded = 8*8

        samples = { # change this instead
            "ch1": dataset["ch1"],
            "ch2": dataset["ch2"],
        }

        samplesPopped = 0
        

        def drawLine(bit:bool, lineLength, channel="ch1"):
            global xCoord, previousBit

            highCoord = CH1_HIGH if channel == "ch1" else CH2_HIGH
            lowCoord = CH1_LOW if channel == "ch1" else CH2_LOW

            if previousBit != None:
                if bit != previousBit:
                    tpil.rect((xCoord, highCoord), (xCoord, lowCoord))
                
            previousBit = bit

            if bit:
                tpil.rect((xCoord, highCoord), (xCoord+lineLength, highCoord))
            else:
                tpil.rect((xCoord, lowCoord), (xCoord+lineLength, lowCoord))

            # timing dot
            tpil.rect(
                (xCoord, lowCoord),
                (xCoord, lowCoord+1)
            )
                
            xCoord += lineLength


        while True:
            tpil.clear()

            keyLegends.draw()

            for channel, sp in samples.items(): # for every channel we set exists, and it's corresponding samples
                for bit in sp: # draw the samples on the screen for that channel
                    drawLine(bit, bitWidth, channel=channel)

                previousBit = None
                xCoord = startX

            tpil.text(
                [round(tpil.disp.width/2), tpil.resizeCoordinate2Res(48)], 
                "{}ns / {}".format(bitTime, localizeHZ(calcHZ(bitTime))),
                fontSize=tpil.disp.recommendedFontSize, anchor="mm")

            tpil.show()
            key = tpil.waitForKey()

            if key == "up": # zoom in
                bitWidth += 8

            elif key == "down": # zoom out
                bitWidth -= 8

            elif key == "right": # move 1 sample right
                if samplesPopped != samplesRecorded: samplesPopped += 1

            elif key == "left": # move 1 sample left
                if samplesPopped != 0: samplesPopped -= 1

            if bitWidth == 0: bitWidth = 8

            for ch, sp in dataset.items(): # per channel and sample
                samples[ch] = dataset[ch][samplesPopped:]

            xCoord = startX

