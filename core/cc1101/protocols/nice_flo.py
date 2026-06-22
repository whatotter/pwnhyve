from .base import BaseProtocolDecoder, dur_diff, add_bit, reverse_key


class NiceFloDecoder(BaseProtocolDecoder):
    name = "NiceFlo"
    te_short = 700
    te_long = 1400
    te_delta = 200
    min_count_bit = 12

    RESET = 0
    FOUND_START = 1
    SAVE_DUR = 2
    CHECK_DUR = 3

    def reset(self):
        super().reset()
        self.step = self.RESET

    def feed(self, level: bool, duration: int):
        if self.step == self.RESET:
            if not level:
                expected = self.te_short * 36
                delta = self.te_delta * 36
                if dur_diff(duration, expected) < delta:
                    self.step = self.FOUND_START

        elif self.step == self.FOUND_START:
            if not level:
                pass
            elif dur_diff(duration, self.te_short) < self.te_delta:
                self.step = self.SAVE_DUR
                self.decode_data = 0
                self.decode_count_bit = 0
            else:
                self.step = self.RESET

        elif self.step == self.SAVE_DUR:
            if not level:
                if duration >= self.te_short * 4:
                    self.step = self.FOUND_START
                    if self.decode_count_bit >= self.min_count_bit:
                        self.serial = 0
                        self.btn = 0
                        if self.callback:
                            self.callback(self)
                    return
                self.te_last = duration
                self.step = self.CHECK_DUR
            else:
                self.step = self.RESET

        elif self.step == self.CHECK_DUR:
            if level:
                short_te = dur_diff(self.te_last, self.te_short) < self.te_delta
                long_te = dur_diff(self.te_last, self.te_long) < self.te_delta
                dur_short = dur_diff(duration, self.te_short) < self.te_delta
                dur_long = dur_diff(duration, self.te_long) < self.te_delta

                if short_te and dur_long:
                    add_bit(self, 0)
                    self.step = self.SAVE_DUR
                elif long_te and dur_short:
                    add_bit(self, 1)
                    self.step = self.SAVE_DUR
                else:
                    self.step = self.RESET
            else:
                self.step = self.RESET

    def result_string(self) -> str:
        return (
            f"{self.name} {self.decode_count_bit}bit\n"
            f"Key:0x{self.decode_data:08X}\n"
            f"Rev:0x{reverse_key(self.decode_data, self.decode_count_bit):08X}"
        )
