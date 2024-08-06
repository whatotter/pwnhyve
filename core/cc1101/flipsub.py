class flipperConv():
    def __init__(self, file) -> None:
        self.p = None
        self.file = file

        self.openSub(file)

        pass
    
    def openSub(self, file):
        with open(file, "r") as f:
            data = f.read().strip().split("\n")
        
        jsonified = {}
        for ln in data:
            x,y = ln.split(": ", 1)
            jsonified[x] = y

        self.p = jsonified
        return jsonified

    def rawDataToBits(self, uslp=1):
        """
        https://forum.flipper.net/t/protocol-documentation/4794/3

        ```
        RAW_Data: 2000 -1000 3000
        send for 2000 microseconds, wait for 1000 microseconds and then send for 3000 microseconds again.
        ```
        """

        if self.p.get("BIT_Data", False):
            print("[FS>BIT] got bit_data from file, returned that")
            return [x for x in self.p["BIT_Data"]]

        assert uslp % 2 == 0 or uslp == 1 # make sure uslp is even

        pulses = [int(x) for x in self.p["RAW_Data"].split(" ")]
        print(pulses)
        data = ""

        for pulse in pulses:
            # each pulse value is in ms
            bit = "0"

            if pulse > 0:
                bit = "1"
            elif 0 > pulse:
                bit = "0"
                pulse = pulse*-1

            #print("{}: {}".format(pulse, bit * round(pulse/uslp)))

            data += bit * round((pulse/uslp)/10)
            
        return data
    
    def __getitem__(self, key):
        return self.p[key]
    
def bitsToRawData(bits, uslp=1):
    """
    https://forum.flipper.net/t/protocol-documentation/4794/3

    ```
    RAW_Data: 2000 -1000 3000
    send for 2000 microseconds, wait for 1000 microseconds and then send for 3000 microseconds again.
    ```
    """

    assert uslp % 2 == 0 or uslp == 1 # make sure uslp is even

    pulses = []
    
    cbit = None
    bitsInARow = 0
    equ = 1
    for bit in bits:
        if cbit == None:
            cbit = bit # set start bit
            bitsInARow += 1
            continue

        if bit == cbit: # if current bit is same as prev
            bitsInARow += 1
        else:
            if cbit == 1 or cbit == "1": # is high bit
                equ = 1 # set high bit, sets pulse number high
            else:
                equ = -1 # low bit, inverts pulse and turns it negative

            pulses.append(round((bitsInARow/uslp)*equ))
            bitsInARow = 0
            cbit = bit

    return pulses

"""
z = flipperConv("fan_light_toggle.sub")
(z.rawDataToBits())
"""