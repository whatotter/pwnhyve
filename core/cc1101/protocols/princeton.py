from .base import BaseProtocolDecoder, dur_diff, add_bit, reverse_key


class PrincetonDecoder(BaseProtocolDecoder):
    name = "Princeton"
    te_short = 390
    te_long = 1170
    te_delta = 300
    min_count_bit = 24

    RESET = 0
    SAVE_DUR = 1
    CHECK_DUR = 2

    def __init__(self, callback=None):
        super().__init__(callback)
        self.last_data = 0
        self.guard_time = 30

    def reset(self):
        super().reset()
        self.step = self.RESET
        self.last_data = 0
        self.guard_time = 30

    def feed(self, level: bool, duration: int):
        if self.step == self.RESET:
            if not level:
                expected = self.te_short * 36
                delta = self.te_delta * 36
                if dur_diff(duration, expected) < delta:
                    self.step = self.SAVE_DUR
                    self.decode_data = 0
                    self.decode_count_bit = 0
                    self.te = 0
                    self.guard_time = 30

        elif self.step == self.SAVE_DUR:
            if level:
                self.te_last = duration
                self.te += duration
                self.step = self.CHECK_DUR

        elif self.step == self.CHECK_DUR:
            if not level:
                if duration >= self.te_long * 2:
                    self.step = self.SAVE_DUR
                    if self.decode_count_bit == self.min_count_bit:
                        if self.last_data == self.decode_data and self.last_data:
                            self.te //= (self.decode_count_bit * 4 + 1)
                            self.guard_time = round(duration / self.te) if self.te else 30
                            if self.guard_time < 15 or self.guard_time > 72:
                                self.guard_time = 30
                            self.serial = self.decode_data >> 4
                            self.btn = self.decode_data & 0xF
                            if self.callback:
                                self.callback(self)
                    self.last_data = self.decode_data
                    self.decode_data = 0
                    self.decode_count_bit = 0
                    self.te = 0
                    return

                self.te += duration

                short_ok = dur_diff(self.te_last, self.te_short) < self.te_delta
                long_ok = dur_diff(self.te_last, self.te_long) < self.te_delta * 3
                dur_short = dur_diff(duration, self.te_short) < self.te_delta
                dur_long = dur_diff(duration, self.te_long) < self.te_delta * 3

                if short_ok and dur_long:
                    add_bit(self, 0)
                    self.step = self.SAVE_DUR
                elif long_ok and dur_short:
                    add_bit(self, 1)
                    self.step = self.SAVE_DUR
                else:
                    self.step = self.RESET
            else:
                self.step = self.RESET

    def result_string(self) -> str:
        rev = reverse_key(self.decode_data, self.min_count_bit)
        return (
            f"{self.name} {self.decode_count_bit}bit\n"
            f"Key:0x{self.decode_data:08X}\n"
            f"Rev:0x{rev:08X}\n"
            f"Sn:0x{self.serial:05X} Btn:{self.btn:X}\n"
            f"Te:{self.te}us  GT:Te*{self.guard_time}"
        )
