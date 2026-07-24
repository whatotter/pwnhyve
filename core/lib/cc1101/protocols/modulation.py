from enum import IntEnum


class Modulation(IntEnum):
    OOK = 0
    FSK2 = 1
    FSK4 = 2


MOD_NAMES = {
    Modulation.OOK: "OOK",
    Modulation.FSK2: "2FSK",
    Modulation.FSK4: "4FSK",
}


def modulation_name(mod: Modulation) -> str:
    return MOD_NAMES.get(mod, "?")
