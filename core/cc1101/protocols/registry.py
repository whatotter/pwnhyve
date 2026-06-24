from typing import Callable, Optional


class RecognizedSignal:
    def __init__(self, protocol_name: str, details: str, data: int, bit_count: int):
        self.protocol_name = protocol_name
        self.details = details
        self.data = data
        self.bit_count = bit_count

    def __repr__(self):
        return f"[{self.protocol_name}] {self.details}"

    def __str__(self):
        return f"{self.protocol_name} | {self.details}"


class ProtocolRegistry:
    def __init__(self):
        self._decoders = []
        self._matched = []

    def register(self, decoder_class, **kwargs):
        dec = decoder_class(callback=self._on_match, **kwargs)
        self._decoders.append(dec)
        return dec

    def _on_match(self, decoder):
        self._matched.append(decoder)

    def feed_all(self, level: bool, duration: int):
        for dec in self._decoders:
            dec.feed(level, duration)

    def feed_pulses(self, pulses):
        for pulse in pulses:
            if pulse == 0:
                continue
            level = pulse > 0
            duration = abs(pulse)
            self.feed_all(level, duration)

    def feed_bits(self, bits, te_us=390):
        for b in bits:
            bit_val = int(b)
            if bit_val == 0:
                self.feed_all(True, te_us)
                self.feed_all(False, te_us * 3)
            else:
                self.feed_all(True, te_us * 3)
                self.feed_all(False, te_us)

    def get_results(self):
        results = []
        seen_hashes = set()
        for dec in self._decoders:
            if dec.decode_count_bit >= dec.min_count_bit:
                h = dec.get_hash()
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    results.append(RecognizedSignal(
                        protocol_name=dec.name,
                        details=dec.result_string(),
                        data=dec.decode_data,
                        bit_count=dec.decode_count_bit,
                    ))
        self._matched.clear()
        return results

    def recognize(self, pulses):
        self.reset_all()
        self.feed_pulses(pulses)
        return self.get_results()

    def recognize_from_bits(self, bits, te_us=390):
        self.reset_all()
        self.feed_bits(bits, te_us)
        return self.get_results()

    def reset_all(self):
        self._matched.clear()
        for dec in self._decoders:
            dec.reset()


def build_default_registry(callback: Optional[Callable] = None) -> ProtocolRegistry:
    reg = ProtocolRegistry()
    _register_special(reg)
    _register_generic(reg)
    return reg


def _register_special(reg):
    from .princeton import PrincetonDecoder
    from .came import CameDecoder
    from .holtek import HoltekDecoder
    from .nice_flo import NiceFloDecoder
    from .keeloq import KeeLoqDecoder
    from .somfy import SomfyTelisDecoder
    from .intertechno import IntertechnoDecoder
    from .secplus_v1 import SecPlusV1Decoder

    reg.register(PrincetonDecoder)
    reg.register(CameDecoder)
    reg.register(HoltekDecoder)
    reg.register(NiceFloDecoder)
    reg.register(KeeLoqDecoder)
    reg.register(SomfyTelisDecoder)
    reg.register(IntertechnoDecoder)
    reg.register(SecPlusV1Decoder)


def _register_generic(reg):
    from .protocol_db import define_protocols
    for decoder in define_protocols():
        decoder.callback = reg._on_match
        reg._decoders.append(decoder)
