from typing import Callable, Optional


def dur_diff(a: int, b: int) -> int:
    return abs(a - b)


def add_bit(decoder, bit: int):
    decoder["decode_data"] = (decoder["decode_data"] << 1) | bit
    decoder["decode_count_bit"] += 1


def reverse_key(data: int, bits: int) -> int:
    rev = 0
    for i in range(bits):
        rev = (rev << 1) | ((data >> i) & 1)
    return rev


class BaseProtocolDecoder:
    name = "Base"
    te_short = 0
    te_long = 0
    te_delta = 0
    min_count_bit = 0

    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.reset()

    def reset(self):
        self.step = 0
        self.decode_data = 0
        self.decode_count_bit = 0
        self.te_last = 0
        self.serial = 0
        self.btn = 0
        self.cnt = 0
        self.te = 0

    def feed(self, level: bool, duration: int):
        raise NotImplementedError

    def result_string(self) -> str:
        rev = reverse_key(self.decode_data, self.decode_count_bit)
        return (
            f"{self.name} {self.decode_count_bit}bit\n"
            f"Key:0x{self.decode_data:X}\n"
            f"Rev:0x{rev:X}\n"
            f"Sn:0x{self.serial:X} Btn:{self.btn:X}"
        )

    def get_hash(self) -> int:
        h = self.decode_data
        h ^= h >> 16
        h ^= h >> 8
        return h & 0xFF
