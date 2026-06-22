from .base import BaseProtocolDecoder, dur_diff


PACKET_TRITS = 21
TRITS_TO_BITS = {0: 0, 1: 1, 2: 0}


def _decode_trit(low_dur: int, high_dur: int, te: int, td: int) -> int:
    low_short = dur_diff(low_dur, te) < td
    low_med = dur_diff(low_dur, te * 2) < td
    low_long = dur_diff(low_dur, te * 3) < td * 2
    high_short = dur_diff(high_dur, te) < td
    high_med = dur_diff(high_dur, te * 2) < td
    high_long = dur_diff(high_dur, te * 3) < td * 2

    if low_short and high_long:
        return 2
    if low_med and high_med:
        return 1
    if low_long and high_short:
        return 0
    return -1


class SecPlusV1Decoder(BaseProtocolDecoder):
    name = "Security+1.0"
    te_short = 500
    te_long = 1500
    te_delta = 100
    min_count_bit = 21

    RESET = 0
    SAVE_LOW = 1
    CHECK_HIGH = 2
    GAP_LOW = 3
    GAP_HIGH = 4
    SECOND_SAVE_LOW = 5
    SECOND_CHECK_HIGH = 6

    def reset(self):
        super().reset()
        self.step = self.RESET
        self._trits = []
        self._trits2 = []
        self._pkt1 = 0
        self._pkt2 = 0

    def feed(self, level: bool, duration: int):
        if self.step == self.RESET:
            if not level and duration >= self.te_short * 120 - self.te_delta * 120:
                self.step = self.SAVE_LOW
                self.decode_data = 0
                self.decode_count_bit = 0
                self._trits = []
                self._trits2 = []
                self._pkt1 = 0
                self._pkt2 = 0

        elif self.step == self.SAVE_LOW:
            if not level:
                self.te_last = duration
                self.step = self.CHECK_HIGH
            elif duration >= self.te_short * 120 - self.te_delta * 120:
                pass
            else:
                self.step = self.RESET

        elif self.step == self.CHECK_HIGH:
            if level:
                trit = _decode_trit(self.te_last, duration,
                                    self.te_short, self.te_delta)
                if trit >= 0:
                    self._trits.append(trit)
                    self.decode_data = (self.decode_data << 2) | trit
                    self.decode_count_bit += 1
                    if len(self._trits) >= PACKET_TRITS:
                        self._pkt1 = self.decode_data
                        self.step = self.GAP_LOW
                    else:
                        self.step = self.SAVE_LOW
                else:
                    self.step = self.RESET
            else:
                self.step = self.RESET

        elif self.step == self.GAP_LOW:
            if not level and duration >= self.te_short * 120 - self.te_delta * 120:
                self.step = self.GAP_HIGH
            elif not level:
                pass
            else:
                self.step = self.RESET

        elif self.step == self.GAP_HIGH:
            if level:
                self.te_last = duration
                self.step = self.SECOND_SAVE_LOW
            else:
                self.step = self.RESET

        elif self.step == self.SECOND_SAVE_LOW:
            if not level:
                self.te_last = duration
                self.step = self.SECOND_CHECK_HIGH
            else:
                self.step = self.RESET

        elif self.step == self.SECOND_CHECK_HIGH:
            if level:
                trit = _decode_trit(self.te_last, duration,
                                    self.te_short, self.te_delta)
                if trit >= 0:
                    self._trits2.append(trit)
                    self.decode_data = (self.decode_data << 2) | trit
                    self.decode_count_bit += 1
                    if len(self._trits2) >= PACKET_TRITS:
                        self._pkt2 = self.decode_data
                        if self.callback:
                            self.callback(self)
                        self.reset()
                    else:
                        self.step = self.SECOND_SAVE_LOW
                else:
                    self.step = self.RESET
            else:
                self.step = self.RESET

    def result_string(self) -> str:
        pkt1 = self._pkt1
        pkt2 = self._pkt2
        combined = 0
        for i in range(PACKET_TRITS):
            t1 = (pkt1 >> (2 * (PACKET_TRITS - 1 - i))) & 3
            t2 = (pkt2 >> (2 * (PACKET_TRITS - 1 - i))) & 3
            combined = (combined << 1) | TRITS_TO_BITS[t1]
        for i in range(PACKET_TRITS):
            t2 = (pkt2 >> (2 * (PACKET_TRITS - 1 - i))) & 3
            combined = (combined << 1) | TRITS_TO_BITS[t2]
        fixed_code = (combined >> 32) & 0xFFFFFFFF
        rolling_code = combined & 0xFFFFFFFF
        return (
            f"{self.name} {self.decode_count_bit}trit\n"
            f"Pkt1:0x{pkt1:032X}\n"
            f"Pkt2:0x{pkt2:032X}\n"
            f"Fixed:0x{fixed_code:08X}\n"
            f"Roll:0x{rolling_code:08X}"
        )
