from .base import BaseProtocolDecoder, dur_diff, soft_score


PACKET_TRITS = 21
TRITS_TO_BITS = {0: 0, 1: 1, 2: 0}


def _decode_trit(low_dur: int, high_dur: int, te: int, td: int) -> tuple:
    s_low_short = soft_score(low_dur, te, td)
    s_low_med = soft_score(low_dur, te * 2, td)
    s_low_long = soft_score(low_dur, te * 3, td * 2)
    s_high_short = soft_score(high_dur, te, td)
    s_high_med = soft_score(high_dur, te * 2, td)
    s_high_long = soft_score(high_dur, te * 3, td * 2)

    score2 = s_low_short * s_high_long
    score1 = s_low_med * s_high_med
    score0 = s_low_long * s_high_short

    scores = {0: score0, 1: score1, 2: score2}
    best = max(scores, key=scores.get)
    return best, scores[best]


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
                trit, trit_conf = _decode_trit(self.te_last, duration,
                                               self.te_short, self.te_delta)
                self.confidence *= trit_conf if trit_conf > 0 else 0.1
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
                trit, trit_conf = _decode_trit(self.te_last, duration,
                                               self.te_short, self.te_delta)
                self.confidence *= trit_conf if trit_conf > 0 else 0.1
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
            f"Roll:0x{rolling_code:08X}\n"
            f"Conf:{self.confidence:.2f}"
        )
