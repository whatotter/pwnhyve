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
    
    def hexDataToBits(self, uslp=1):
        bits = []
        for heex in self["HEX_Data"].split(' '):
            # Convert the hex string to an integer
            print(heex)
            hex_num = int(heex, 16)
            # Convert the integer to a binary string, remove the '0b' prefix, and pad to 4 bits
            binary_str = bin(hex_num)[2:].zfill(4)
            # Extend the bits list with the individual bits
            bits.extend(int(bit) for bit in binary_str)
        print(bits)
        return bits

    def rawDataToBits(self, nsBitRate=1000):
        """
        https://forum.flipper.net/t/protocol-documentation/4794/3

        ```
        RAW_Data: 2000 -1000 3000
        send for 2000 microseconds, wait for 1000 microseconds and then send for 3000 microseconds again.
        ```
        """

        """
        if self.p.get("BIT_Data", False):
            print("[FS>BIT] got bit_data from file, returned that")
            return [int(x) for x in self.p["BIT_Data"]]
        """

        """
        1 microsecond = 1000 nanoseconds

        bits = bit * ((pulse * 1000) / nsBitRate)
        """

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

            #data += bit * round((pulse/uslp)/10)
            bits = bit * round((pulse * 1000) / nsBitRate)
            data += bits
            
        return data
    
    def bits(self):
        return [int(x) for x in self.p["BIT_Data"].split(" ")]
    
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