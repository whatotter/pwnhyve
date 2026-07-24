from .base import BaseProtocolDecoder, dur_diff, soft_score, add_bit, reverse_key


HOLTEK_HEADER_MASK = 0xF000000000
HOLTEK_HEADER = 0x5000000000


class HoltekDecoder(BaseProtocolDecoder):
    name = "Holtek"
    te_short = 430
    te_long = 870
    te_delta = 100
    min_count_bit = 40

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
            if level and dur_diff(duration, self.te_short) < self.te_delta:
                self.step = self.SAVE_DUR
                self.decode_data = 0
                self.decode_count_bit = 0
            else:
                self.step = self.RESET

        elif self.step == self.SAVE_DUR:
            if not level:
                gap = self.te_short * 10 + self.te_delta
                if duration >= gap:
                    if (self.decode_count_bit == self.min_count_bit and
                            (self.decode_data & HOLTEK_HEADER_MASK) == HOLTEK_HEADER):
                        self.serial = reverse_key((self.decode_data >> 16) & 0xFFFFF, 20)
                        btn_raw = self.decode_data & 0xFFFF
                        btn_val = self._decode_btn(btn_raw)
                        self.btn = btn_val
                        if self.callback:
                            self.callback(self)
                    self.decode_data = 0
                    self.decode_count_bit = 0
                    self.step = self.FOUND_START
                    return
                self.te_last = duration
                self.step = self.CHECK_DUR
            else:
                self.step = self.RESET

        elif self.step == self.CHECK_DUR:
            if level:
                short_last_score = soft_score(self.te_last, self.te_short, self.te_delta)
                long_last_score = soft_score(self.te_last, self.te_long, self.te_delta * 2)
                short_dur_score = soft_score(duration, self.te_short, self.te_delta)
                long_dur_score = soft_score(duration, self.te_long, self.te_delta * 2)

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

    @staticmethod
    def _decode_btn(btn: int) -> int:
        if (btn & 0xF) != 0xA:
            return 0x10 | (btn & 0xF)
        elif ((btn >> 4) & 0xF) != 0xA:
            return 0x20 | ((btn >> 4) & 0xF)
        elif ((btn >> 8) & 0xF) != 0xA:
            return 0x30 | ((btn >> 8) & 0xF)
        elif ((btn >> 12) & 0xF) != 0xA:
            return 0x40 | ((btn >> 12) & 0xF)
        return 0

    def result_string(self) -> str:
        hi = (self.decode_data >> 32) & 0xFFFFFFFF
        lo = self.decode_data & 0xFFFFFFFF
        btn_label = "ON" if (self.btn & 0xF) == 0xE else "OFF" if (self.btn & 0xF) == 0xB else ""
        return (
            f"{self.name} {self.decode_count_bit}bit\n"
            f"Key:0x{hi:08X}{lo:08X}\n"
            f"Sn:0x{self.serial:05X} Btn:{self.btn >> 4:X} {btn_label}\n"
            f"Conf:{self.confidence:.2f}"
        )
