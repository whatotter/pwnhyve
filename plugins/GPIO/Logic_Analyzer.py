import os
from core.plugin import BasePwnhyvePlugin 
from core.pil_simplify import tinyPillow
import plugins.GPIO._pins as pinMGR
from core.pio.fastio import FastIO

def calcHZ(ns):
    return 1/(ns/(1*10**9))

def calcNS(hz):
    return (1 / hz) * 1e9

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

def strhzToNS(string):
    adj = string.lower().replace("hz", "")
    if "m" in adj: # is mhz
        return round(calcNS(int(adj[:-1]) * 1_000_000))
    if "k" in adj: # is khz
        return round(calcNS(int(adj[:-1]) * 1_000))
    return round(calcNS(int(adj))) # is just plain hz

def samplesToCSV(dataset, length, filename:str="samples.csv"):
    """
    turn captured samples into CSV format for sigrok
    """

    csv = open(filename, "w")

    csv.write("{}, {}".format(
        pinMGR.pinsInverted[LA_CFG["Channel 1"]["value"]],
        pinMGR.pinsInverted[LA_CFG["Channel 2"]["value"]]
    ))

    for index in range(length):
        csv.write("{},{}\n".format(
            dataset["ch1"][index],
            dataset["ch2"][index]
            ))

    csv.flush()

    return filename

fastio = FastIO()

LA_CFG = {
    "Channel 1": {"value": 14, "type": "pin"},   # channel 1 pin
    "Channel 2": {"value": 15, "type": "pin"},  # channel 2 pin
    "Samples": { # amount of samples
        "value": 10000, 
        "type": "predefined", 
        "choices": [
            100, 1000, 
            10000, 100_000, 
            500_000, 1_000_000,
            2_500_000, 5_000_000,
            10_000_000, 25_000_000 # should be way more than enough, right?
            ]
        },
    "Sample Rate": { # value is in nanoseconds
        "value": "100kHz", # should be good for most things
        "type": "predefined",
        "choices": [
            "500hz", "1kHz", 
            "10kHz", "50kHz",
            "100kHz", "250kHz",
            "500kHz", "1mHz",
            "1.5mHz"
        ]
    },
    "Export": {
        "type": "export"
    }
}

def editConfig(tpil):
    global LA_CFG, dataset, samplesRecorded
    while True:
        choice = tpil.gui.menu(list(LA_CFG), icons=None)
        if choice == None: return # user hit back button

        cfgParameter = LA_CFG[choice] # this is what we'll be editing
        if cfgParameter["type"] == "predefined":
            nv = tpil.gui.menu([str(x) for x in cfgParameter["choices"]], icons=None)
            cfgParameter["value"] = nv
            print('[+] {} -> {}'.format(choice, nv))

        elif cfgParameter["type"] == "pin":
            channelPins = [ # channel pins to highlight as selected
                LA_CFG["Channel 1"]["value"],
                LA_CFG["Channel 2"]["value"]
                ]

            cfgParameter["value"] = pinMGR.requestPin(tpil, highlightedPins=channelPins)

        elif cfgParameter["type"] == "export":
            samplesToCSV(dataset, samplesRecorded)
            tpil.clear() # flash the user showing that we did infact save samples
            tpil.show()
            continue

        LA_CFG[choice] = cfgParameter

class PWNLA(BasePwnhyvePlugin):
    _icons = {
        "Logic_Analyzer": "./core/icons/graph.bmp",
    }
        
    def Logic_Analyzer(tpil:tinyPillow):
        global xCoord, previousBit, bitsBeforeActivity, dataset, samplesRecorded

        CH1_HIGH = tpil.resizeCoordinate2Res(1)
        CH1_LOW = tpil.resizeCoordinate2Res(CH1_HIGH + 10)

        CH2_HIGH = tpil.resizeCoordinate2Res(24)
        CH2_LOW = tpil.resizeCoordinate2Res(CH2_HIGH + 10)

        keyLegends = tpil.gui.keyLegend(tpil, {"left": "", "right": "", "up": "+", "down": "-", "press": "REC"})

        previousBit = None
        activityPositions = []
        snapPosition = 0

        startX = 4
        xCoord = startX

        bitWidth = 16
        minBitWidth = 0.001
        bitMove = 1

        dataset = { # this should be immutable - never change this - our dataset
            "ch1": [0,1,1,0,1,0,1,0]*8,
            "ch2": [1,1,1,0,1,0,1,1]*8
        }
        samplesRecorded = 8*8

        channels = dataset.copy() # this is mutable

        samplesPopped = 0

        def drawLine(bits:bool, lineLength, channel="ch1"):
            global xCoord, previousBit, bitsBeforeActivity
            print("[!!!] drawing {} samples".format(len(bits)))

            highCoord = CH1_HIGH if channel == "ch1" else CH2_HIGH
            lowCoord = CH1_LOW if channel == "ch1" else CH2_LOW

            bitLength = 0
            previousBit = bits[0]
            bitsPassed = 0

            for bit in bits:
                bitsPassed += 1

                if bit != previousBit: # if bit is different, then draw the previous bit
                    bitLength = lineLength*bitsPassed

                    if bit == 0: # if this new bit is LOW, then the previous bit was HIGH
                        tpil.rect((xCoord, highCoord), (xCoord+bitLength, highCoord))
                    else: # if this new bit is HIGH, then previous was LOW
                        tpil.rect((xCoord, lowCoord), (xCoord+bitLength, lowCoord))

                    activityPositions.append(bitsPassed - 2) # so we can snap to here (where there's activity), quickly

                    tpil.rect((xCoord, highCoord), (xCoord, lowCoord)) # draw the change (_|‾)

                    xCoord += bitLength
                    bitLength = 0
                    previousBit = bit

                if (xCoord >= tpil.disp.width or bitLength >= tpil.disp.width) and len(activityPositions) >= 1: # dont render anymore than we need to
                    break


            print("[=] real: {} bits drawn".format(bitsPassed))

            if bitLength != 0:
                tpil.rect((xCoord, highCoord), (xCoord, lowCoord)) # draw the change

                if previousBit == 1: # if previous bit was HIGH, and we were waiting for a LOW, then the bit is HIGH
                    tpil.rect((xCoord, highCoord), (xCoord+bitLength, highCoord))
                else: # if previous bit was LOW, and we were waiting for a HIGH, then the bit is LOW
                    tpil.rect((xCoord, lowCoord), (xCoord+bitLength, lowCoord))

            print("[+] {} snap positions found".format(activityPositions))

        showZoom = False # if this is true, show the zoom value on the bottom right
        outOfConfig = False # if this is true, we just got out the config menu
        while True:
            print("+" + ("-"*30) + "+")
            tpil.clear()

            keyLegends.draw()

            activityPositions = [] # clear our snap array, so it can be recalculated
            if samplesRecorded >= 600000:
                tpil.text([32, 32], "too many samples!!! :'(", fontSize=16)
            else:
                for channel, samples in channels.items(): # for every channel we set exists, and it's corresponding samples
                    drawLine(samples, bitWidth, channel=channel)

                    previousBit = None
                    xCoord = startX

            # calculate scroll bar
            scrollBarWidth = round(tpil.disp.width*(tpil.disp.width/samplesRecorded))
            xOffset = samplesPopped * (tpil.disp.width/samplesRecorded)
            tpil.rect((xOffset, 50), (xOffset+scrollBarWidth, 52))

            if showZoom:
                tpil.text([100, 40], str(bitWidth), fontSize=16)
                showZoom = False
            
            if outOfConfig:
                tpil.text([32, 40], "{}s read".format(
                    round((strhzToNS(LA_CFG["Sample Rate"]["value"]) * int(LA_CFG["Samples"]["value"])) / 1_000_000_000, 2)
                ), fontSize=16)
                outOfConfig = False

            # show everything
            tpil.show()

            # handle keys
            key = tpil.waitForKey()
            if key == "up": # zoom in
                showZoom = True
                if 2 >= bitWidth: # we want to zoom in a little bit less
                    if 0.25 >= bitWidth: # a way bit less
                        if 0.05 >= bitWidth:
                            bitWidth += 0.001
                        else:
                            bitWidth += 0.01
                    else:
                        bitWidth += 0.1 # go by 1/10ths, same way as ln 216
                else:
                    bitWidth += 2

            elif key == "down": # zoom out
                showZoom = True
                if 2 >= bitWidth: # we want to zoom out MORE
                    if 0.25 >= bitWidth: # ZOOM OUT MOAR!!!
                        if 0.05 >= bitWidth: # !!!!!!!!!!!!!
                            bitWidth -= 0.001
                        else:
                            bitWidth -= 0.005
                    else:
                        bitWidth -= 0.1 # go by 1/10ths instead
                        
                else:
                    bitWidth -= 2

            elif key == "right": # move 1 sample right
                if samplesPopped != samplesRecorded:
                    samplesPopped += bitMove * (5 if 2 > bitWidth else 1) # scroll more if we're zoomed out all the way

            elif key == "left": # move 1 sample left
                if samplesPopped != 0: samplesPopped -= bitMove

            elif key == "press": # rerecord
                # clear the display
                tpil.clear()
                keyLegends.draw()
                tpil.show()

                # record our samples
                fastio.setNS(strhzToNS(LA_CFG["Sample Rate"]["value"]))
                LAProc = fastio.readSamples([
                    LA_CFG["Channel 1"]["value"], 
                    LA_CFG["Channel 2"]["value"]
                    ], LA_CFG["Samples"]["value"], output="/tmp/logic_analyzer", bg=True)
                
                #CH2Proc = fastio.readSamples(CH2Pin, 10000, output="/tmp/channel2.bin", bg=True)[0]

                print("[+] waiting on read")
                LAProc.wait()
                print('[+] read finished')

                # update our data
                dataset = {
                    "ch1": fastio.__parseBin__(LA_CFG["Channel 1"]["value"], binf="/tmp/logic_analyzer"),
                    "ch2": fastio.__parseBin__(LA_CFG["Channel 2"]["value"], binf="/tmp/logic_analyzer")
                }

                samplesRecorded = int(LA_CFG["Samples"]["value"])
                channels = dataset.copy()
                bitMove = round(samplesRecorded/1000)

                if 1 > bitMove:
                    bitMove = 1

                newRecording = True

            elif key == "1": # reconfigure
                editConfig(tpil)
                outOfConfig = True

            elif key == '3':
                dataset.clear()
                samples.clear()
                return

            elif key == '2': # snap to next data position
                if snapPosition >= len(activityPositions)-1:
                    snapPosition = 0

                if len(activityPositions) == 0:
                    continue

                samplesPopped = activityPositions[snapPosition]

                snapPosition += 1

            if 0 >= bitWidth: bitWidth = minBitWidth
            else:
                bitWidth = round(bitWidth, 3)

            # handle our scrolling
            for _ch, _sp in dataset.items(): # per channel and sample
                channels[_ch] = _sp[samplesPopped:]

            xCoord = startX

