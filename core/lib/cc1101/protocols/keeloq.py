from .base import BaseProtocolDecoder, dur_diff, soft_score, add_bit, reverse_key


KEE_LOQ_KNOWN_MFR = {
    0x0016A3: "Nice",
    0x002E5A: "CAME",
    0x003B6A: "DoorHan",
    0x004C4B: "Faac",
    0x00617A: "Ditec",
    0x00A64E: "Allmatic",
    0x00B1C8: "Aprimatic",
    0x00D609: "BFT",
    0x00F4E7: "Mhouse/Dea",
    0x014B88: "Somfy",
    0x01A5B8: "Bentel",
    0x029257: "King Gates",
    0x02D422: "Proseco",
    0x035647: "Tau",
    0x03A4B7: "Roger",
}


class KeeLoqDecoder(BaseProtocolDecoder):
    name = "KeeLoq"
    te_short = 400
    te_long = 800
    te_delta = 140
    min_count_bit = 64

    RESET = 0
    SAVE_DUR = 1
    CHECK_DUR = 2

    def reset(self):
        super().reset()
        self.step = self.RESET

    def feed(self, level: bool, duration: int):
        if self.step == self.RESET:
            if not level and duration >= self.te_short * 10 - self.te_delta * 10:
                self.step = self.SAVE_DUR
                self.decode_data = 0
                self.decode_count_bit = 0
                self.te_last = 0

        elif self.step == self.SAVE_DUR:
            if level:
                self.te_last = duration
                self.step = self.CHECK_DUR
            elif duration >= self.te_short * 10 - self.te_delta * 10:
                if self.decode_count_bit >= self.min_count_bit:
                    if self.callback:
                        self.callback(self)
                self.reset()
            else:
                self.step = self.RESET

        elif self.step == self.CHECK_DUR:
            if not level:
                if duration >= self.te_short * 2 + self.te_delta:
                    if self.decode_count_bit >= self.min_count_bit:
                        if self.callback:
                            self.callback(self)
                    self.reset()
                    return

                short_last_score = soft_score(self.te_last, self.te_short, self.te_delta)
                long_last_score = soft_score(self.te_last, self.te_long, self.te_delta * 3)
                short_dur_score = soft_score(duration, self.te_short, self.te_delta)
                long_dur_score = soft_score(duration, self.te_long, self.te_delta * 3)

                score1 = short_last_score * long_dur_score
                score0 = long_last_score * short_dur_score

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
        mfr_code = (self.decode_data >> 36) & 0xFFFFFF
        mfr = KEE_LOQ_KNOWN_MFR.get(mfr_code, f"0x{mfr_code:06X}")
        serial = (self.decode_data >> 8) & 0xFFFFFFF
        cnt = self.decode_data & 0xFF
        rev = reverse_key(self.decode_data, self.decode_count_bit)
        return (
            f"{self.name} {self.decode_count_bit}bit\n"
            f"Key:0x{self.decode_data:016X}\n"
            f"Rev:0x{rev:016X}\n"
            f"Mfr:{mfr} Ser:{serial} Cnt:{cnt}\n"
            f"Conf:{self.confidence:.2f}"
        )
