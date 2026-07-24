import struct
from typing import List, Union


def bitsToOctet(bits: Union[str, List[int]]) -> List[str]:
    if isinstance(bits, list):
        bits = ''.join(str(b) for b in bits)
    _bytes = []
    for x in range(0, len(bits), 8):
        _bytes.append(bits[x:8 + x])
    if not _bytes:
        return []
    if len(_bytes[-1]) != 8:
        _bytes[-1] = _bytes[-1].ljust(8, '0')
    return _bytes


def bitToByte(byte: int) -> str:
    return format(byte, '08b')


def deleteTrailingNull(bits: Union[str, List[int]]) -> Union[str, List[int]]:
    if isinstance(bits, list):
        start = 0
        while start < len(bits) and bits[start] == 0:
            start += 1
        end = len(bits)
        while end > start and bits[end - 1] == 0:
            end -= 1
        return bits[start:end]
    return bits.lstrip('0').rstrip('0')


def bin2(num: int) -> str:
    a = bin(num)[2:]
    return a.zfill(8)


def b2h(_bytes: List[bytes]) -> List[str]:
    return [b.hex() for b in _bytes]


def hexToBytes(hexa: List[str]) -> List[str]:
    _bytes = []
    for x in hexa:
        _bytes.append(bin2(int(x, 0)))
    return _bytes


def octetsToHex(octets: List[Union[str, List[str]]]) -> List[str]:
    hexa = []
    for x in octets:
        if isinstance(x, list):
            a = "0x%X" % int(''.join(str(y) for y in x), base=2)
        else:
            a = "0x%X" % int(str(x), base=2)
        hexa.append(a)
    hexa = _stripLeadingZeros(hexa)
    return hexa if hexa else ["0x0"]


def _stripLeadingZeros(hexa: List[str]) -> List[str]:
    while hexa and hexa[0] == "0x0":
        hexa.pop(0)
    return hexa


def bitsToHex(bits: Union[str, List[int]]) -> str:
    val = 0
    for b in bits:
        bit = int(b)
        val = (val << 1) | bit
    return hex(val)


def intToBits(num: int, width: int = 8) -> str:
    return format(num, f'0{width}b')


def bitsToInt(bits: str) -> int:
    return int(bits, 2) if bits else 0
