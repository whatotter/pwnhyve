from .base import BaseProtocolDecoder, dur_diff, soft_score, add_bit, reverse_key


SOMFY_BTN = {0x1: "My", 0x2: "Up", 0x4: "Down", 0x8: "Prog"}


class SomfyTelisDecoder(BaseProtocolDecoder):
    name = "SomfyTelis"
    te_short = 640
    te_long = 1280
    te_delta = 250
    min_count_bit = 56

    RESET = 0
    FOUND_PREAMBLE = 1
    CHECK_PREAMBLE = 2
    FOUND_SYNC = 3
    SAVE_DUR = 4
    CHECK_DUR = 5

    def reset(self):
        super().reset()
        self.step = self.RESET
        self._preamble_cnt = 0

    def feed(self, level: bool, duration: int):
        if self.step == self.RESET:
            if not level:
                pass
            elif dur_diff(duration, self.te_short * 4) < self.te_delta * 4:
                self.step = self.FOUND_PREAMBLE
                self._preamble_cnt = 0

        elif self.step == self.FOUND_PREAMBLE:
            if not level:
                if dur_diff(duration, self.te_short * 4) < self.te_delta * 4:
                    self._preamble_cnt += 1
                    self.step = self.CHECK_PREAMBLE
                else:
                    self.step = self.RESET
            else:
                self.step = self.RESET

        elif self.step == self.CHECK_PREAMBLE:
            if level:
                if dur_diff(duration, self.te_short * 4) < self.te_delta * 4:
                    self.step = self.FOUND_PREAMBLE
                elif (dur_diff(duration, self.te_short * 7) < self.te_delta * 7
                      and self._preamble_cnt >= 2):
                    self.step = self.FOUND_SYNC
                    self._preamble_cnt = 0
                else:
                    self.step = self.RESET
            else:
                self.step = self.RESET

        elif self.step == self.FOUND_SYNC:
            if not level and dur_diff(duration, self.te_short) < self.te_delta * 2:
                self.step = self.SAVE_DUR
                self.decode_data = 0
                self.decode_count_bit = 0
            else:
                self.step = self.RESET

        elif self.step == self.SAVE_DUR:
            if not level:
                if duration >= self.te_long * 2:
                    if self.decode_count_bit >= self.min_count_bit:
                        if self.callback:
                            self.callback(self)
                    self.reset()
                    return
                self.te_last = duration
                self.step = self.CHECK_DUR
            else:
                self.step = self.RESET

        elif self.step == self.CHECK_DUR:
            if level:
                short_last_score = soft_score(self.te_last, self.te_short, self.te_delta)
                long_last_score = soft_score(self.te_last, self.te_long, self.te_delta)
                short_dur_score = soft_score(duration, self.te_short, self.te_delta)
                long_dur_score = soft_score(duration, self.te_long, self.te_delta)

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

    def result_string(self) -> str:
        decrypted = self.decode_data ^ (self.decode_data >> 8)
        key = (decrypted >> 52) & 0xF
        btn = (decrypted >> 48) & 0xF
        ctrl = (decrypted >> 44) & 0xF
        cnt = (decrypted >> 28) & 0xFFFF
        serial = decrypted & 0xFFFFFF
        rev = reverse_key(self.decode_data, self.decode_count_bit)
        btn_name = SOMFY_BTN.get(btn, f"0x{btn:X}")
        return (
            f"{self.name} {self.decode_count_bit}bit\n"
            f"Key:0x{self.decode_data:014X}\n"
            f"Rev:0x{rev:014X}\n"
            f"Sn:{serial:06X} Cnt:{cnt:04X}\n"
            f"Btn:{btn_name} CRC:{ctrl:X}\n"
            f"Conf:{self.confidence:.2f}"
        )
