from typing import List, Optional, Dict, Union


class flipperConv:
    def __init__(self, file: str) -> None:
        self.p: Dict[str, str] = {}
        self.file = file
        self.openSub(file)

    def openSub(self, file: str) -> Dict[str, str]:
        with open(file, "r") as f:
            data = f.read().strip().split("\n")

        jsonified: Dict[str, str] = {}
        for ln in data:
            if ": " not in ln:
                continue
            x, y = ln.split(": ", 1)
            jsonified[x] = y

        self.p = jsonified
        return jsonified

    def hexDataToBits(self) -> List[int]:
        raw = self.p.get("HEX_Data", "")
        bits: List[int] = []
        for heex in raw.split(' '):
            if not heex:
                continue
            hex_num = int(heex, 16)
            binary_str = bin(hex_num)[2:].zfill(4)
            bits.extend(int(bit) for bit in binary_str)
        return bits

    def rawDataToBits(self, nsBitRate: int = 1000) -> str:
        raw = self.p.get("RAW_Data")
        if raw is None:
            bit_data = self.p.get("BIT_Data")
            if bit_data is not None:
                return bit_data.replace(" ", "")
            return ""

        pulses = [int(x) for x in raw.split(" ") if x]
        data = ""

        for pulse in pulses:
            bit = "1" if pulse > 0 else "0"
            if pulse < 0:
                pulse = -pulse
            bits = bit * round((pulse * 1000) / nsBitRate)
            data += bits

        return data

    def bits(self) -> List[int]:
        raw = self.p.get("BIT_Data", "")
        return [int(x) for x in raw.split(" ") if x]

    def __getitem__(self, key: str) -> str:
        return self.p[key]

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.p.get(key, default)
    
    def sset(self, key: str, value: any):
        self.p[key] = value


def bitsToRawData(bits: Union[str, List[int]], uslp: int = 1) -> List[int]:
    assert uslp % 2 == 0 or uslp == 1

    pulses: List[int] = []
    cbit = None
    bitsInARow = 0
    equ = 1

    for bit in bits:
        bit_val = int(bit)
        if cbit is None:
            cbit = bit_val
            bitsInARow = 1
            continue

        if bit_val == cbit:
            bitsInARow += 1
        else:
            if cbit == 1:
                equ = 1
            else:
                equ = -1
            pulses.append(round((bitsInARow / uslp) * equ))
            bitsInARow = 1
            cbit = bit_val

    if cbit is not None:
        equ = 1 if cbit == 1 else -1
        pulses.append(round((bitsInARow / uslp) * equ))

    return pulses
