from .base import BaseProtocolDecoder, dur_diff, soft_score, add_bit, reverse_key
from .modulation import Modulation, modulation_name


def _build_result(name, count, data, te, mod_name):
    rev = reverse_key(data, count)
    lines = [
        f"{name} {count}bit",
        f"Key:0x{data:016X}" if data > 0xFFFFFFFF else f"Key:0x{data:08X}",
        f"Rev:0x{rev:016X}" if rev > 0xFFFFFFFF else f"Rev:0x{rev:08X}",
        f"Mod:{mod_name} Te:{te}us",
    ]
    return "\n".join(lines)


class PreambleConfig:
    NONE = 0
    FIXED_LOW = 1
    FIXED_HIGH = 2
    SYNC_GAP = 3


class GenericDecoder(BaseProtocolDecoder):
    name = "Generic"
    modulation = Modulation.OOK
    te_short = 0
    te_long = 0
    te_delta = 0
    min_count_bit = 0

    RESET = 0
    FOUND_HDR = 1
    SAVE_DUR = 2
    CHECK_DUR = 3

    def __init__(self, name, te_short, te_long, te_delta, min_count_bit,
                 preamble_type=PreambleConfig.FIXED_LOW,
                 preamble_te_mult=36, preamble_delta_mult=None,
                 encoding="HL", invert=False, end_min_te_mult=2,
                 long_tol=None, mod=Modulation.OOK, header_mask=None,
                 header_val=None, callback=None):
        self.name = name
        self.te_short = te_short
        self.te_long = te_long
        self.te_delta = te_delta
        self.min_count_bit = min_count_bit
        self.modulation = mod
        self._preamble_type = preamble_type
        self._preamble_te_mult = preamble_te_mult
        self._preamble_delta_mult = preamble_delta_mult or preamble_te_mult
        self._encoding = encoding
        self._invert = invert
        self._end_min_te_mult = end_min_te_mult
        self._header_mask = header_mask
        self._header_val = header_val
        self._long_tol = long_tol

        BaseProtocolDecoder.__init__(self, callback)
        self.reset()

    def reset(self):
        BaseProtocolDecoder.reset(self)
        self.step = self.RESET

    def feed(self, level: bool, duration: int):
        if self.step == self.RESET:
            self._reset_check(level, duration)
        elif self.step == self.FOUND_HDR:
            self._found_hdr(level, duration)
        elif self.step == self.SAVE_DUR:
            self._save_dur(level, duration)
        elif self.step == self.CHECK_DUR:
            self._check_dur(level, duration)

    def _reset_check(self, level, duration):
        if self._preamble_type == PreambleConfig.NONE:
            self.step = self.SAVE_DUR
            self.decode_data = 0
            self.decode_count_bit = 0
            return

        if level:
            return

        if self._preamble_type == PreambleConfig.FIXED_LOW:
            expected = self.te_short * self._preamble_te_mult
            tol = self.te_delta * self._preamble_delta_mult
            if dur_diff(duration, expected) < tol:
                self.step = self.FOUND_HDR

        elif self._preamble_type == PreambleConfig.SYNC_GAP:
            if duration >= self.te_short * self._preamble_te_mult - \
                          self.te_delta * self._preamble_delta_mult:
                self.step = self.SAVE_DUR
                self.decode_data = 0
                self.decode_count_bit = 0

    def _found_hdr(self, level, duration):
        if not level:
            return
        if self._encoding == "HL":
            if dur_diff(duration, self.te_short) < self.te_delta:
                self.te_last = duration
                self.step = self.CHECK_DUR
                self.decode_data = 0
                self.decode_count_bit = 0
        else:
            self.step = self.SAVE_DUR
            self.decode_data = 0
            self.decode_count_bit = 0

    def _save_dur(self, level, duration):
        if self._encoding == "HL":
            if level:
                self.te_last = duration
                self.step = self.CHECK_DUR
            elif duration >= self.te_long * self._end_min_te_mult:
                self._emit_if_ready()
                self.reset()
            else:
                self.step = self.RESET
        else:
            if not level:
                if duration >= self.te_long * self._end_min_te_mult:
                    self._emit_if_ready()
                    self.reset()
                    return
                self.te_last = duration
                self.step = self.CHECK_DUR
            else:
                self.step = self.RESET

    def _check_dur(self, level, duration):
        if self._encoding == "HL":
            if not level:
                end_thresh = self.te_long * self._end_min_te_mult
                if duration >= end_thresh:
                    self._emit_if_ready()
                    self.reset()
                    return
                self._decode_bit_hl(duration)
            else:
                self.step = self.RESET
        else:
            if level:
                if duration >= self.te_long * self._end_min_te_mult:
                    self._emit_if_ready()
                    self.reset()
                    return
                self._decode_bit_lh(duration)
            else:
                self.step = self.RESET

    def _decode_bit_hl(self, low_dur):
        long_tol = self._long_tol if self._long_tol is not None else self.te_delta * 3

        short_last_score = soft_score(self.te_last, self.te_short, self.te_delta)
        long_last_score = soft_score(self.te_last, self.te_long, long_tol)
        short_dur_score = soft_score(low_dur, self.te_short, self.te_delta)
        long_dur_score = soft_score(low_dur, self.te_long, long_tol)

        if self._invert:
            score0 = long_last_score * short_dur_score
            score1 = short_last_score * long_dur_score
        else:
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

    def _decode_bit_lh(self, high_dur):
        short_last_score = soft_score(self.te_last, self.te_short, self.te_delta)
        long_last_score = soft_score(self.te_last, self.te_long, self.te_delta)
        short_dur_score = soft_score(high_dur, self.te_short, self.te_delta)
        long_dur_score = soft_score(high_dur, self.te_long, self.te_delta)

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

    def _emit_if_ready(self):
        if self.decode_count_bit >= self.min_count_bit:
            if self._header_mask is not None and self._header_val is not None:
                if (self.decode_data & self._header_mask) != self._header_val:
                    return
            self.te = self.te or self.te_short
            if self.callback:
                self.callback(self)

    def result_string(self) -> str:
        return _build_result(self.name, self.decode_count_bit,
                             self.decode_data, self.te_short,
                             modulation_name(self.modulation))



