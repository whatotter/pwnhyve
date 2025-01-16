# list of available pins to use

"""
    +-----+---------+----------+---------+-----+ 
    | BCM |   Name  | Physical | Name    | BCM | 
    +-----+---------+----++----+---------+-----+
    |     |    3.3v |  1 || 2  | 5v      |     |
    |   2 |   SDA 1 |  3 || 4  | 5v      |     |
    |   3 |   SCL 1 |  5 || 6  | 0v      |     |
    |   4 | GPIO  7 |  7 || 8  | TxD     | 14  |
    |     |      0v |  9 || 10 | RxD     | 15  |
                         ||                    
                         || 14 | 0v      |     |
    |  22 | GPIO  3 | 15 ||                    
    |     |    3.3v | 17 || 18                    
                         || 20 | 0v      |     |
                         ||                    
                         ||                    
    |     |      0v | 25 || 26 | CE1     | 7   |
                         ||                    
                         || 30 | 0v      |     |
                         ||                    
                         || 34 | 0v      |     |
                         ||                    
                         ||                    
    |     |      0v | 39 ||                    
    +-----+---------+----++----+---------+-----+
"""

pins = { # name -> BCM
    "GPIO4": 4,
    "GPIO17": 17,
    "GPIO1": 1,
    "GPIO0": 0,
    #"GPIO3": 22,
    "SCL": 3,
    "SDA": 2,
    "TxD": 14,
    "RxD": 15,
}

pinLocations = { # which pin it is, left to right, pins facing up

    "GND1": 1,
    "GPIO4": 2,
    "GPIO17": 3,
    "SCLK": 4,
    "GPIO7": 5,
    "MISO": 6,
    "MOSI": 7,
    "5V": 8,


    "GND2": 9,
    "GPIO22": 10,
    "SCL": 11,
    "SDA": 12,
    "RxD": 13,
    "TxD": 14,
    "GPIO1": 15,
    "GND3": 16,
    "GPIO0": 17,
    "3v3": 18,

    #"GPIO3": -1
}

pinsInverted = {v: k for k, v in pins.items()} # BCM pin -> name
physPinsInv = {v: k for k, v in pinLocations.items()} # physical pin -> pin name

def pinLookup(bcm):
    return pinsInverted[bcm]

def physicalPinLookup(pin):
    """
    returns BCM pin from a physical pin, from the 18pin header
    """
    return pins[physPinsInv[pin]]

def requestPin(tpil, highlightedPins=[], append={}, minimize=False):

    def pinName(pin):

        if not minimize:
            return "{} (pin {}) {}".format(
                pin, pinLocations[pin], append.get(pin, "")
            )
        else:
            return "Pin {} {}".format(
                pinLocations[pin], append.get(pin, "")
            )

    pinsNamed = [pinName(x) for x in list(pins)]
    hlPinsNamed = [pinName(x) for x in highlightedPins]
    
    print("+---------------------------------------+")
    print("append: {}".format(append))
    print("pins: {}".format(pinsNamed))
    print("highlight: {}".format(hlPinsNamed))
    print("+---------------------------------------+")

    pinName = tpil.gui.menu( # returns pin name (e.g. GPIO4)
        pinsNamed,
        highlight=hlPinsNamed,
        icons=None
    )

    if pinName == None:
        return None

    if not minimize:
        pin = pinName.split(" ", 1)[0] # hacky
    else:
        return physicalPinLookup(int(pinName[1:].split(" ")[0]))

    return pins[pin] # translate pin name to BCM pin (e.g. 23)