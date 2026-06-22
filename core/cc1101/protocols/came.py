from .base import BaseProtocolDecoder, dur_diff, add_bit


CAME_NAMES = {
    12: "CAME",
    18: "Airforce",
    24: "CAME",
    25: "Prastel",
    42: "Prastel",
}


class CameDecoder(BaseProtocolDecoder):
    name = "CAME"
    te_short = 320
    te_long = 640
    te_delta = 150
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
                expected = self.te_short * 56
                delta = self.te_delta * 63
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
                    if self.decode_count_bit in (12, 18, 24, 25, 42):
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
        display_name = CAME_NAMES.get(self.decode_count_bit, "CAME")
        return (
            f"{display_name} {self.decode_count_bit}bit\n"
            f"Key:0x{self.decode_data:010X}\n"
        )
