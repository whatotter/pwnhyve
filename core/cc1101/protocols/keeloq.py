from .base import BaseProtocolDecoder, dur_diff, add_bit, reverse_key


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

                short_te = dur_diff(self.te_last, self.te_short) < self.te_delta
                long_te = dur_diff(self.te_last, self.te_long) < self.te_delta * 3
                dur_short = dur_diff(duration, self.te_short) < self.te_delta
                dur_long = dur_diff(duration, self.te_long) < self.te_delta * 3

                if short_te and dur_long:
                    add_bit(self, 1)
                    self.step = self.SAVE_DUR
                elif long_te and dur_short:
                    add_bit(self, 0)
                    self.step = self.SAVE_DUR
                else:
                    self.step = self.RESET
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
            f"Mfr:{mfr} Ser:{serial} Cnt:{cnt}"
        )
