from .base import BaseProtocolDecoder, dur_diff, soft_score, add_bit, reverse_key


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
        self.guard_time = 30

    def reset(self):
        super().reset()
        self.step = self.RESET
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
            elif duration >= self.te_long * 2:
                self._on_gap(duration)

        elif self.step == self.CHECK_DUR:
            if not level:
                if duration >= self.te_long * 2:
                    self._on_gap(duration)
                    return

                self.te += duration

                short_last_score = soft_score(self.te_last, self.te_short, self.te_delta)
                long_last_score = soft_score(self.te_last, self.te_long, self.te_delta * 3)
                short_dur_score = soft_score(duration, self.te_short, self.te_delta)
                long_dur_score = soft_score(duration, self.te_long, self.te_delta * 3)

                score0 = short_last_score * long_dur_score
                score1 = long_last_score * short_dur_score

                if score0 >= score1 and score0 >= 0.3:
                    add_bit(self, 0)
                    self.confidence *= score0
                elif score1 >= 0.3:
                    add_bit(self, 1)
                    self.confidence *= score1
                elif max(score0, score1) > 0:
                    bit = 0 if score0 >= score1 else 1
                    add_bit(self, bit)
                    self.confidence *= max(score0, score1) * 0.5
                else:
                    add_bit(self, 0)
                    self.confidence *= 0.1

                self.step = self.SAVE_DUR
            else:
                self.step = self.RESET

    def _on_gap(self, duration):
        if self.decode_count_bit == self.min_count_bit - 1:
            short_last_score = soft_score(self.te_last, self.te_short, self.te_delta)
            long_last_score = soft_score(self.te_last, self.te_long, self.te_delta * 3)
            if short_last_score >= long_last_score and short_last_score > 0:
                add_bit(self, 0)
                self.confidence *= short_last_score
            elif long_last_score > 0:
                add_bit(self, 1)
                self.confidence *= long_last_score
            else:
                add_bit(self, 0)
                self.confidence *= 0.1

        if self.decode_count_bit >= self.min_count_bit:
            self.te //= (self.decode_count_bit * 4 + 1)
            self.guard_time = round(duration / self.te) if self.te else 30
            if self.guard_time < 15 or self.guard_time > 72:
                self.guard_time = 30
            self.serial = self.decode_data >> 4
            self.btn = self.decode_data & 0xF
            if self.callback:
                self.callback(self)

        self.decode_data = 0
        self.decode_count_bit = 0
        self.te = 0
        self.confidence = 1.0
        self.step = self.SAVE_DUR

    def result_string(self) -> str:
        rev = reverse_key(self.decode_data, self.min_count_bit)
        return (
            f"{self.name} {self.decode_count_bit}bit\n"
            f"Conf:{self.confidence:.2f}"
            f"Key:0x{self.decode_data:08X}\n"
            f"Rev:0x{rev:08X}\n"
            f"Sn:0x{self.serial:05X}\n"
            f"Btn:{self.btn:X}\n"
            f"Te:{self.te}us\n"
            f"GT:Te*{self.guard_time}\n"
        )
