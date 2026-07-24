from .base import BaseProtocolDecoder, dur_diff, soft_score, add_bit, reverse_key


class IntertechnoDecoder(BaseProtocolDecoder):
    name = "Intertechno"
    te_short = 275
    te_long = 1375
    te_delta = 150
    min_count_bit = 32

    RESET = 0
    FOUND_HEADER_LOW = 1
    FOUND_HEADER_HIGH = 2
    FOUND_SYNC_HIGH = 3
    FOUND_SYNC_LOW = 4
    SAVE_DUR = 5
    CHECK_DUR = 6
    CONSUME_HIGH = 7
    CONSUME_LOW = 8

    def reset(self):
        super().reset()
        self.step = self.RESET

    def feed(self, level: bool, duration: int):
        if self.step == self.RESET:
            if not level and duration >= self.te_short * 37 - self.te_delta * 15:
                self.step = self.FOUND_HEADER_LOW

        elif self.step == self.FOUND_HEADER_LOW:
            if level and dur_diff(duration, self.te_short) < self.te_delta:
                self.step = self.FOUND_HEADER_HIGH
            elif not level:
                pass
            else:
                self.step = self.RESET

        elif self.step == self.FOUND_HEADER_HIGH:
            if not level:
                self.step = self.FOUND_SYNC_HIGH
            else:
                self.step = self.RESET

        elif self.step == self.FOUND_SYNC_HIGH:
            if level and dur_diff(duration, self.te_short) < self.te_delta:
                self.step = self.FOUND_SYNC_LOW
            elif not level:
                pass
            else:
                self.step = self.RESET

        elif self.step == self.FOUND_SYNC_LOW:
            if not level and dur_diff(duration, self.te_short * 10) < self.te_delta * 3:
                self.step = self.SAVE_DUR
                self.decode_data = 0
                self.decode_count_bit = 0
            elif level:
                self.step = self.RESET

        elif self.step == self.SAVE_DUR:
            if level:
                if soft_score(duration, self.te_short, self.te_delta) > 0:
                    self.step = self.CHECK_DUR
                else:
                    self.step = self.RESET

        elif self.step == self.CHECK_DUR:
            if not level:
                if duration >= self.te_short * 11:
                    self.step = self.FOUND_HEADER_LOW
                    if self.decode_count_bit >= self.min_count_bit:
                        if self.callback:
                            self.callback(self)
                    self.reset()
                    return
                score0 = soft_score(duration, self.te_short, self.te_delta)
                score1 = soft_score(duration, self.te_long, self.te_delta)
                if score0 >= score1 and score0 >= 0.3:
                    add_bit(self, 0)
                    self.confidence *= score0
                elif score1 >= 0.3:
                    add_bit(self, 1)
                    self.confidence *= score1
                else:
                    bit = 0 if score0 >= score1 else 1
                    add_bit(self, bit)
                    self.confidence *= max(score0, score1, 0.01) * 0.5
                self.step = self.CONSUME_HIGH
            else:
                self.step = self.RESET

        elif self.step == self.CONSUME_HIGH:
            if level and dur_diff(duration, self.te_short) < self.te_delta:
                self.step = self.CONSUME_LOW
            elif level:
                self.step = self.RESET

        elif self.step == self.CONSUME_LOW:
            if level:
                self.step = self.RESET
            elif duration >= self.te_short * 11:
                if self.decode_count_bit >= self.min_count_bit:
                    if self.callback:
                        self.callback(self)
                self.reset()
            else:
                short_score = soft_score(duration, self.te_short, self.te_delta)
                long_score = soft_score(duration, self.te_long, self.te_delta)
                if short_score >= long_score and short_score > 0:
                    self.step = self.SAVE_DUR
                elif long_score > 0:
                    self.step = self.SAVE_DUR
                else:
                    self.step = self.RESET

    def result_string(self) -> str:
        serial = (self.decode_data >> 6) & 0x3FFFFFF
        all_btn = (self.decode_data >> 5) & 1
        on_off = (self.decode_data >> 4) & 1
        ch = (~self.decode_data) & 0xF
        rev = reverse_key(self.decode_data, self.decode_count_bit)
        btn = "On" if on_off else "Off"
        if all_btn:
            btn = "All " + btn
        return (
            f"{self.name} {self.decode_count_bit}bit\n"
            f"Key:0x{self.decode_data:08X}\n"
            f"Rev:0x{rev:08X}\n"
            f"Sn:{serial:06X} Ch:{ch} {btn}\n"
            f"Conf:{self.confidence:.2f}"
        )
