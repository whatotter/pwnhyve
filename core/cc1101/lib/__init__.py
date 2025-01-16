# python-cc1101 - Python Library to Transmit RF Signals via CC1101 Transceivers
#
# Copyright (C) 2020 Fabian Peter Hammerle <fabian@hammerle.me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import contextlib
import datetime
import enum
import fcntl
import logging
import math
import typing
import warnings

import spidev

import cc1101._gpio
from cc1101.addresses import (
    ConfigurationRegisterAddress,
    FIFORegisterAddress,
    PatableAddress,
    StatusRegisterAddress,
    StrobeAddress,
)
from cc1101.options import (
    GDOSignalSelection,
    ModulationFormat,
    PacketLengthMode,
    SyncMode,
    _TransceiveMode,
)

_LOGGER = logging.getLogger(__name__)


class Pin(enum.Enum):
    GDO0 = "GDO0"


class MainRadioControlStateMachineState(enum.IntEnum):
    """
    MARCSTATE - Main Radio Control State Machine State
    """

    # see "Figure 13: Simplified State Diagram"
    # and "Figure 25: Complete Radio Control State Diagram"
    IDLE = 0x01
    STARTCAL = 0x08  # after IDLE
    BWBOOST = 0x09  # after STARTCAL
    FS_LOCK = 0x0A
    RX = 0x0D
    RXFIFO_OVERFLOW = 0x11
    TX = 0x13
    # TXFIFO_UNDERFLOW = 0x16


class _ReceivedPacket:  # unstable
    # "Table 31: Typical RSSI_offset Values"
    _RSSI_OFFSET_dB = 74

    def __init__(
        self,
        *,
        payload: bytes,
        rssi_index: int,  # byte
        checksum_valid: bool,
        link_quality_indicator: int,  # 7bit
    ):
        self.payload = payload
        self._rssi_index = rssi_index
        assert 0 <= rssi_index < (1 << 8), rssi_index
        self.checksum_valid = checksum_valid
        self.link_quality_indicator = link_quality_indicator
        assert 0 <= link_quality_indicator < (1 << 7), link_quality_indicator

    @property
    def rssi_dbm(self) -> float:
        """
        Estimated Received Signal Strength Indicator (RSSI) in dBm

        see section "17.3 RSSI"
        """
        if self._rssi_index >= 128:
            return (self._rssi_index - 256) / 2 - self._RSSI_OFFSET_dB
        return self._rssi_index / 2 - self._RSSI_OFFSET_dB

    def __str__(self) -> str:
        return f"{type(self).__name__}(RSSI {self.rssi_dbm:.0f}dBm, 0x{self.payload.hex()})"


def _format_patable(settings: typing.Iterable[int], insert_spaces: bool) -> str:
    # "Table 39: Optimum PATABLE Settings" uses hexadecimal digits
    # "0" for brevity
    settings_hex = tuple(map(lambda s: "0" if s == 0 else f"0x{s:x}", settings))
    if len(settings_hex) == 1:
        return f"({settings_hex[0]},)"
    delimiter = ", " if insert_spaces else ","
    return f"({delimiter.join(settings_hex)})"


class CC1101:
    # pylint: disable=too-many-public-methods

    # > All transfers on the SPI interface are done
    # > most significant bit first.
    # > All transactions on the SPI interface start with
    # > a header byte containing a R/W bit, a access bit (B),
    # > and a 6-bit address (A5 - A0).
    # > [...]
    # > Table 45: SPI Address Space
    _WRITE_SINGLE_BYTE = 0x00
    # > Registers with consecutive addresses can be
    # > accessed in an efficient way by setting the
    # > burst bit (B) in the header byte. The address
    # > bits (A5 - A0) set the start address in an
    # > internal address counter. This counter is
    # > incremented by one each new byte [...]
    _WRITE_BURST = 0x40
    _READ_SINGLE_BYTE = 0x80
    _READ_BURST = 0xC0

    # 29.3 Status Register Details
    _SUPPORTED_PARTNUM = 0
    # > The two versions of the chip will behave the same.
    # https://e2e.ti.com/support/wireless-connectivity/sub-1-ghz/f/156/p/428028/1529544#1529544
    _SUPPORTED_VERSIONS = [
        0x04,  #  https://github.com/fphammerle/python-cc1101/issues/15
        0x14,
    ]

    _CRYSTAL_OSCILLATOR_FREQUENCY_HERTZ = 26e6
    # see "21 Frequency Programming"
    # > f_carrier = f_XOSC / 2**16 * (FREQ + CHAN * ((256 + CHANSPC_M) * 2**CHANSPC_E-2))
    _FREQUENCY_CONTROL_WORD_HERTZ_FACTOR = _CRYSTAL_OSCILLATOR_FREQUENCY_HERTZ / 2**16

    # roughly estimated / tested with SDR receiver, docs specify:
    # > can [...] be programmed for operation at other frequencies
    # > in the 300-348 MHz, 387-464 MHz and 779-928 MHz bands.
    _TRANSMIT_MIN_FREQUENCY_HERTZ = 281.7e6

    # > The PATABLE is an 8-byte table that defines the PA control settings [...]
    _PATABLE_LENGTH_BYTES = 8

    def __init__(
        self,
        spi_bus: int = 0,
        spi_chip_select: int = 0,
        lock_spi_device: bool = False,
        spi_max_speed_hz: int = 55700,
    ) -> None:
        """
        lock_spi_device:
            When True, an advisory, exclusive lock will be set on the SPI device file
            non-blockingly via flock upon entering the context.
            If the SPI device file is already locked (e.g., by a different process),
            a BlockingIOError will be raised.
            The lock will be removed automatically, when leaving the context.
            The lock can optionally be released earlier by calling .unlock_spi_device().
            >>> transceiver = cc1101.CC1101(lock_spi_device=True)
            >>> # not locked
            >>> with transceiver:
            >>>     # locked
            >>> # lock removed
            >>> with transceiver:
            >>>     # locked
            >>>     transceiver.unlock_spi_device()
            >>>     # lock removed
        """
        self._spi = spidev.SpiDev()
        self._spi_max_speed_hz = spi_max_speed_hz
        self._spi_bus = int(spi_bus)
        # > The BCM2835 core common to all Raspberry Pi devices has 3 SPI Controllers:
        # > SPI0, with two hardware chip selects, [...]
        # > SPI1, with three hardware chip selects, [...]
        # > SPI2, also with three hardware chip selects, is only usable on a Compute Module [...]
        # https://github.com/raspberrypi/documentation/blob/d41d69f8efa3667b1a8b01a669238b8bd113edc1/hardware/raspberrypi/spi/README.md#hardware
        # https://www.raspberrypi.org/documentation/hardware/raspberrypi/spi/README.md
        self._spi_chip_select = int(spi_chip_select)
        self._lock_spi_device = lock_spi_device

    @property
    def _spi_device_path(self) -> str:
        # https://github.com/doceme/py-spidev/blob/v3.4/spidev_module.c#L1286
        return f"/dev/spidev{self._spi_bus}.{self._spi_chip_select}"

    @staticmethod
    def _log_chip_status_byte(chip_status: int) -> None:
        # see "10.1 Chip Status Byte" & "Table 23: Status Byte Summary"
        # > The command strobe registers are accessed by transferring
        # > a single header byte [...]. That is, only the R/W̄ bit,
        # > the burst access bit (set to 0), and the six address bits [...]
        # > The R/W̄ bit can be either one or zero and will determine how the
        # > FIFO_BYTES_AVAILABLE field in the status byte should be interpreted.
        _LOGGER.debug(
            "chip status byte: CHIP_RDYn=%d STATE=%s FIFO_BYTES_AVAILBLE=%d",
            chip_status >> 7,
            bin((chip_status >> 4) & 0b111),
            chip_status & 0b1111,
        )

    def _read_single_byte(
        self, register: typing.Union[ConfigurationRegisterAddress, FIFORegisterAddress]
    ) -> int:
        response = self._spi.xfer([register | self._READ_SINGLE_BYTE, 0])
        assert len(response) == 2, response
        self._log_chip_status_byte(response[0])
        return response[1]

    def _read_burst(
        self,
        start_register: typing.Union[
            ConfigurationRegisterAddress, PatableAddress, FIFORegisterAddress
        ],
        length: int,
    ) -> typing.List[int]:
        response = self._spi.xfer([start_register | self._READ_BURST] + [0] * length)
        assert len(response) == length + 1, response
        self._log_chip_status_byte(response[0])
        return response[1:]

    def _read_status_register(self, register: StatusRegisterAddress) -> int:
        # > For register addresses in the range 0x30-0x3D,
        # > the burst bit is used to select between
        # > status registers when burst bit is one, and
        # > between command strobes when burst bit is
        # > zero. [...]
        # > Because of this, burst access is not available
        # > for status registers and they must be accessed
        # > one at a time. The status registers can only be
        # > read.
        response = self._spi.xfer([register | self._READ_BURST, 0])
        assert len(response) == 2, response
        self._log_chip_status_byte(response[0])
        return response[1]

    def _command_strobe(self, register: StrobeAddress) -> None:
        # see "10.4 Command Strobes"
        _LOGGER.debug("sending command strobe 0x%02x", register)
        response = self._spi.xfer([register | self._WRITE_SINGLE_BYTE])
        assert len(response) == 1, response
        self._log_chip_status_byte(response[0])

    def _write_burst(
        self,
        start_register: typing.Union[
            ConfigurationRegisterAddress, PatableAddress, FIFORegisterAddress
        ],
        values: typing.List[int],
    ) -> None:
        _LOGGER.debug(
            "writing burst: start_register=0x%02x values=%s", start_register, values
        )
        response = self._spi.xfer([start_register | self._WRITE_BURST] + values)
        assert len(response) == len(values) + 1, response
        self._log_chip_status_byte(response[0])
        #assert all(v == response[0] for v in response[1:]), response #FUCKYOU

    def _reset(self) -> None:
        self._command_strobe(StrobeAddress.SRES)

    @classmethod
    def _filter_bandwidth_floating_point_to_real(
        cls, *, mantissa: int, exponent: int
    ) -> float:
        """
        See "13 Receiver Channel Filter Bandwidth"
        """
        return cls._CRYSTAL_OSCILLATOR_FREQUENCY_HERTZ / (
            8 * (4 + mantissa) * (2**exponent)
        )

    def _get_filter_bandwidth_hertz(self) -> float:
        """
        MDMCFG4.CHANBW_E & MDMCFG4.CHANBW_M

        > [...] decimation ratio for the delta-sigma ADC input stream
        > and thus the channel bandwidth.

        See "13 Receiver Channel Filter Bandwidth"

        """
        mdmcfg4 = self._read_single_byte(ConfigurationRegisterAddress.MDMCFG4)
        return self._filter_bandwidth_floating_point_to_real(
            exponent=mdmcfg4 >> 6, mantissa=(mdmcfg4 >> 4) & 0b11
        )

    def _set_filter_bandwidth(self, *, mantissa: int, exponent: int) -> None:
        """
        MDMCFG4.CHANBW_E & MDMCFG4.CHANBW_M
        """
        mdmcfg4 = self._read_single_byte(ConfigurationRegisterAddress.MDMCFG4)
        mdmcfg4 &= 0b00001111
        assert 0 <= exponent <= 0b11, exponent
        mdmcfg4 |= exponent << 6
        assert 0 <= mantissa <= 0b11, mantissa
        mdmcfg4 |= mantissa << 4
        self._write_burst(
            start_register=ConfigurationRegisterAddress.MDMCFG4, values=[mdmcfg4]
        )

    def _get_symbol_rate_exponent(self) -> int:
        """
        MDMCFG4.DRATE_E
        """
        return self._read_single_byte(ConfigurationRegisterAddress.MDMCFG4) & 0b00001111

    def _set_symbol_rate_exponent(self, exponent: int):
        mdmcfg4 = self._read_single_byte(ConfigurationRegisterAddress.MDMCFG4)
        mdmcfg4 &= 0b11110000
        mdmcfg4 |= exponent
        self._write_burst(
            start_register=ConfigurationRegisterAddress.MDMCFG4, values=[mdmcfg4]
        )

    def _get_symbol_rate_mantissa(self) -> int:
        """
        MDMCFG3.DRATE_M
        """
        return self._read_single_byte(ConfigurationRegisterAddress.MDMCFG3)

    def _set_symbol_rate_mantissa(self, mantissa: int) -> None:
        self._write_burst(
            start_register=ConfigurationRegisterAddress.MDMCFG3, values=[mantissa]
        )

    @classmethod
    def _symbol_rate_floating_point_to_real(
        cls, *, mantissa: int, exponent: int
    ) -> float:
        # see "12 Data Rate Programming"
        return (
            (256 + mantissa)
            * (2**exponent)
            * cls._CRYSTAL_OSCILLATOR_FREQUENCY_HERTZ
            / (2**28)
        )

    @classmethod
    def _symbol_rate_real_to_floating_point(cls, real: float) -> typing.Tuple[int, int]:
        # see "12 Data Rate Programming"
        assert real > 0, real
        exponent = math.floor(
            math.log2(real / cls._CRYSTAL_OSCILLATOR_FREQUENCY_HERTZ) + 20
        )
        mantissa = round(
            real * 2**28 / cls._CRYSTAL_OSCILLATOR_FREQUENCY_HERTZ / 2**exponent
            - 256
        )
        if mantissa == 256:
            exponent += 1
            mantissa = 0
        assert 0 < exponent <= 2**4, exponent
        assert mantissa <= 2**8, mantissa
        return mantissa, exponent

    def get_symbol_rate_baud(self) -> float:
        return self._symbol_rate_floating_point_to_real(
            mantissa=self._get_symbol_rate_mantissa(),
            exponent=self._get_symbol_rate_exponent(),
        )

    def set_symbol_rate_baud(self, real: float) -> None:
        # > The data rate can be set from 0.6 kBaud to 500 kBaud [...]
        mantissa, exponent = self._symbol_rate_real_to_floating_point(real)
        self._set_symbol_rate_mantissa(mantissa)
        self._set_symbol_rate_exponent(exponent)

    def get_modulation_format(self) -> ModulationFormat:
        mdmcfg2 = self._read_single_byte(ConfigurationRegisterAddress.MDMCFG2)
        return ModulationFormat((mdmcfg2 >> 4) & 0b111)

    def _set_modulation_format(self, modulation_format: ModulationFormat) -> None:
        mdmcfg2 = self._read_single_byte(ConfigurationRegisterAddress.MDMCFG2)
        mdmcfg2 &= 0b10001111
        mdmcfg2 |= modulation_format << 4
        self._write_burst(ConfigurationRegisterAddress.MDMCFG2, [mdmcfg2])

    def enable_manchester_code(self) -> None:
        """
        MDMCFG2.MANCHESTER_EN

        Enable manchester encoding & decoding for the entire packet,
        including the preamble and synchronization word.
        """
        mdmcfg2 = self._read_single_byte(ConfigurationRegisterAddress.MDMCFG2)
        mdmcfg2 |= 0b1000
        self._write_burst(ConfigurationRegisterAddress.MDMCFG2, [mdmcfg2])

    def get_sync_mode(self) -> SyncMode:
        mdmcfg2 = self._read_single_byte(ConfigurationRegisterAddress.MDMCFG2)
        return SyncMode(mdmcfg2 & 0b11)

    def set_sync_mode(
        self,
        mode: SyncMode,
        *,
        _carrier_sense_threshold_enabled: typing.Optional[bool] = None,  # unstable
    ) -> None:
        """
        MDMCFG2.SYNC_MODE

        see "14.3 Byte Synchronization"

        Carrier Sense (CS) Threshold (when receiving packets, API unstable):
        > Carrier sense can be used as a sync word qualifier
        > that requires the signal level to be higher than the threshold
        > for a sync word > search to be performed [...]
        > CS can be used to avoid interference from other RF sources [...]
        True: enable, False: disable, None: keep current setting
        See "17.4 Carrier Sense (CS)"
        """
        mdmcfg2 = self._read_single_byte(ConfigurationRegisterAddress.MDMCFG2)
        mdmcfg2 &= 0b11111100
        mdmcfg2 |= mode
        if _carrier_sense_threshold_enabled is not None:
            if _carrier_sense_threshold_enabled:
                mdmcfg2 |= 0b00000100
            else:
                mdmcfg2 &= 0b11111011
        self._write_burst(ConfigurationRegisterAddress.MDMCFG2, [mdmcfg2])

    def get_preamble_length_bytes(self) -> int:
        """
        MDMCFG1.NUM_PREAMBLE

        Minimum number of preamble bytes to be transmitted.

        See "15.2 Packet Format"
        """
        index = (
            self._read_single_byte(ConfigurationRegisterAddress.MDMCFG1) >> 4
        ) & 0b111
        return 2 ** (index >> 1) * (2 + (index & 0b1))

    def _set_preamble_length_index(self, index: int) -> None:
        assert 0 <= index <= 0b111
        mdmcfg1 = self._read_single_byte(ConfigurationRegisterAddress.MDMCFG1)
        mdmcfg1 &= 0b10001111
        mdmcfg1 |= index << 4
        self._write_burst(ConfigurationRegisterAddress.MDMCFG1, [mdmcfg1])

    def set_preamble_length_bytes(self, length: int) -> None:
        """
        see .get_preamble_length_bytes()
        """
        if length < 1:
            raise ValueError(
                f"invalid preamble length {length} given"
                "\ncall .set_sync_mode(cc1101.SyncMode.NO_PREAMBLE_AND_SYNC_WORD)"
                " to disable preamble"
            )
        if length % 3 == 0:  # pylint: disable=consider-ternary-expression
            index = math.log2(length / 3) * 2 + 1
        else:
            index = math.log2(length / 2) * 2
        if not index.is_integer() or index < 0 or index > 0b111:
            raise ValueError(
                f"unsupported preamble length: {length} bytes"
                "\nsee MDMCFG1.NUM_PREAMBLE in cc1101 docs"
            )
        self._set_preamble_length_index(int(index))

    def _get_power_amplifier_setting_index(self) -> int:
        """
        see ._set_power_amplifier_setting_index
        """
        return self._read_single_byte(ConfigurationRegisterAddress.FREND0) & 0b111

    def _set_power_amplifier_setting_index(self, setting_index: int) -> None:
        """
        FREND0.PA_POWER

        > This value is an index to the PATABLE,
        > which can be programmed with up to 8 different PA settings.

        > In OOK/ASK mode, this selects the PATABLE index to use
        > when transmitting a '1'.
        > PATABLE index zero is used in OOK/ASK when transmitting a '0'.
        > The PATABLE settings from index 0 to the PA_POWER value are
        > used for > ASK TX shaping, [...]

        see "Figure 32: Shaping of ASK Signal"

        > If OOK modulation is used, the logic 0 and logic 1 power levels
        > shall be programmed to index 0 and 1 respectively.
        """
        assert 0 <= setting_index <= 0b111, setting_index
        frend0 = self._read_single_byte(ConfigurationRegisterAddress.FREND0)
        frend0 &= 0b11111000
        frend0 |= setting_index
        self._write_burst(ConfigurationRegisterAddress.FREND0, [frend0])

    def _verify_chip(self) -> None:
        partnum = self._read_status_register(StatusRegisterAddress.PARTNUM)
        if partnum != self._SUPPORTED_PARTNUM:
            raise ValueError(
                f"unexpected chip part number {partnum} (expected: {self._SUPPORTED_PARTNUM})"
            )
        version = self._read_status_register(StatusRegisterAddress.VERSION)
        if version not in self._SUPPORTED_VERSIONS:
            msg = f"Unsupported chip version 0x{version:02x}"
            supported_versions = ", ".join(
                f"0x{v:02x}" for v in self._SUPPORTED_VERSIONS
            )
            msg += f" (expected one of [{supported_versions}])"
            if version == 0:
                msg += (
                    "\n\nPlease verify that all required pins are connected"
                    " (see https://github.com/fphammerle/python-cc1101#wiring-raspberry-pi)"
                    " and that you selected the correct SPI bus and chip/slave select line."
                )
            raise ValueError(msg)

    def _configure_defaults(self) -> None:
        # next major/breaking release will probably stick closer to CC1101's defaults
        # 6:4 MOD_FORMAT: OOK (default: 2-FSK)
        self._set_modulation_format(ModulationFormat.ASK_OOK)
        self._set_power_amplifier_setting_index(1)
        self._disable_data_whitening()
        # 7:6 unused
        # 5:4 FS_AUTOCAL: calibrate when going from IDLE to RX or TX
        # 3:2 PO_TIMEOUT: default
        # 1 PIN_CTRL_EN: default
        # 0 XOSC_FORCE_ON: default
        self._write_burst(ConfigurationRegisterAddress.MCSM0, [0b010100])
        # > Default is CLK_XOSC/192 (See Table 41 on page 62).
        # > It is recommended to disable the clock output in initialization,
        # > in order to optimize RF performance.
        self._write_burst(
            ConfigurationRegisterAddress.IOCFG0,
            # required for _wait_for_packet()
            [GDOSignalSelection.RX_FIFO_AT_OR_ABOVE_THRESHOLD_OR_PACKET_END_REACHED],
        )

    def __enter__(self) -> CC1101:
        # https://docs.python.org/3/reference/datamodel.html#object.__enter__
        try:
            self._spi.open(self._spi_bus, self._spi_chip_select)
        except PermissionError as exc:
            raise PermissionError(
                f"Could not access {self._spi_device_path}"
                "\nVerify that the current user has both read and write access."
                "\nOn some systems, like Raspberry Pi OS / Raspbian,"
                "\n\tsudo usermod -a -G spi $USER"
                "\nfollowed by a re-login grants sufficient permissions."
            ) from exc
        if self._lock_spi_device:
            # advisory, exclusive, non-blocking
            # lock removed in __exit__ by SpiDev.close()
            fcntl.flock(self._spi.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            self._spi.max_speed_hz = self._spi_max_speed_hz
            self._reset()
            self._verify_chip()
            self._configure_defaults()
            #marcstate = self.get_main_radio_control_state_machine_state() # mvv
            #if marcstate != MainRadioControlStateMachineState.IDLE:
                #raise ValueError(f"expected marcstate idle (actual: {marcstate.name})")
        except:
            self._spi.close()
            raise
        return self

    def __exit__(self, exc_type, exc_value, traceback):  # -> typing.Literal[False]
        # https://docs.python.org/3/reference/datamodel.html#object.__exit__
        self._spi.close()
        return False

    def unlock_spi_device(self) -> None:
        """
        Manually release the lock set on the SPI device file.

        Alternatively, the lock will be released automatically,
        when leaving the context.

        Method fails silently, if the SPI device file is not locked.

        >>> transceiver = cc1101.CC1101(lock_spi_device=True)
        >>> # not locked
        >>> with transceiver:
        >>>     # locked
        >>> # lock removed
        >>> with transceiver:
        >>>     # locked
        >>>     transceiver.unlock_spi_device()
        >>>     # lock removed
        """
        fileno = self._spi.fileno()
        if fileno != -1:
            fcntl.flock(fileno, fcntl.LOCK_UN)

    def get_main_radio_control_state_machine_state(
        self,
    ) -> MainRadioControlStateMachineState:
        return MainRadioControlStateMachineState(
            self._read_status_register(StatusRegisterAddress.MARCSTATE)
        )

    def get_marc_state(self) -> MainRadioControlStateMachineState:
        """
        alias for get_main_radio_control_state_machine_state()
        """
        return self.get_main_radio_control_state_machine_state()

    @classmethod
    def _frequency_control_word_to_hertz(cls, control_word: typing.List[int]) -> float:
        return (
            int.from_bytes(control_word, byteorder="big", signed=False)
            * cls._FREQUENCY_CONTROL_WORD_HERTZ_FACTOR
        )

    @classmethod
    def _hertz_to_frequency_control_word(cls, hertz: float) -> typing.List[int]:
        return list(
            round(hertz / cls._FREQUENCY_CONTROL_WORD_HERTZ_FACTOR).to_bytes(
                length=3, byteorder="big", signed=False
            )
        )

    def _get_base_frequency_control_word(self) -> typing.List[int]:
        # > The base or start frequency is set by the 24 bitfrequency
        # > word located in the FREQ2, FREQ1, FREQ0 registers.
        return self._read_burst(
            start_register=ConfigurationRegisterAddress.FREQ2, length=3
        )

    def _set_base_frequency_control_word(self, control_word: typing.List[int]) -> None:
        self._write_burst(
            start_register=ConfigurationRegisterAddress.FREQ2, values=control_word
        )

    def get_base_frequency_hertz(self) -> float:
        return self._frequency_control_word_to_hertz(
            self._get_base_frequency_control_word()
        )

    def set_base_frequency_hertz(self, freq: float) -> None:
        if freq < (self._TRANSMIT_MIN_FREQUENCY_HERTZ - 50e3):
            # > [use] warnings.warn() in library code if the issue is avoidable
            # > and the client application should be modified to eliminate the warning[.]
            # > [use] logging.warning() if there is nothing the client application
            # > can do about the situation, but the event should still be noted.
            # https://docs.python.org/3/howto/logging.html#when-to-use-logging
            warnings.warn(
                "CC1101 is unable to transmit at frequencies"
                f" below {(self._TRANSMIT_MIN_FREQUENCY_HERTZ / 1e6):.1f} MHz"
            )
        self._set_base_frequency_control_word(
            self._hertz_to_frequency_control_word(freq)
        )

    def __str__(self) -> str:
        sync_mode = self.get_sync_mode()
        attrs = (
            f"marcstate={self.get_main_radio_control_state_machine_state().name.lower()}",
            f"base_frequency={(self.get_base_frequency_hertz() / 1e6):.2f}MHz",
            f"symbol_rate={(self.get_symbol_rate_baud() / 1000):.2f}kBaud",
            f"modulation_format={self.get_modulation_format().name}",
            f"sync_mode={sync_mode.name}",
            f"preamble_length={self.get_preamble_length_bytes()}B"
            if sync_mode != SyncMode.NO_PREAMBLE_AND_SYNC_WORD
            else None,
            f"sync_word=0x{self.get_sync_word().hex()}"
            if sync_mode != SyncMode.NO_PREAMBLE_AND_SYNC_WORD
            else None,
            "packet_length{}{}B".format(  # pylint: disable=consider-using-f-string
                "≤"
                if self.get_packet_length_mode() == PacketLengthMode.VARIABLE
                else "=",
                self.get_packet_length_bytes(),
            ),
            "output_power="
            + _format_patable(self.get_output_power(), insert_spaces=False),
        )
        # pylint: disable=consider-using-f-string
        return "CC1101({})".format(", ".join(filter(None, attrs)))

    def get_configuration_register_values(
        self,
        start_register: ConfigurationRegisterAddress = min(
            ConfigurationRegisterAddress
        ),
        end_register: ConfigurationRegisterAddress = max(ConfigurationRegisterAddress),
    ) -> typing.Dict[ConfigurationRegisterAddress, int]:
        assert start_register <= end_register, (start_register, end_register)
        values = self._read_burst(
            start_register=start_register, length=end_register - start_register + 1
        )
        return {
            ConfigurationRegisterAddress(start_register + i): v
            for i, v in enumerate(values)
        }

    def get_sync_word(self) -> bytes:
        """
        SYNC1 & SYNC0

        See "15.2 Packet Format"

        The first byte's most significant bit is transmitted first.
        """
        return bytes(
            self._read_burst(
                start_register=ConfigurationRegisterAddress.SYNC1, length=2
            )
        )

    def set_sync_word(self, sync_word: bytes) -> None:
        """
        See .set_sync_word()
        """
        if len(sync_word) != 2:
            raise ValueError(f"expected two bytes, got {sync_word!r}")
        self._write_burst(
            start_register=ConfigurationRegisterAddress.SYNC1, values=list(sync_word)
        )

    def get_packet_length_bytes(self) -> int:
        """
        PKTLEN

        Packet length in fixed packet length mode,
        maximum packet length in variable packet length mode.

        > In variable packet length mode, [...]
        > any packet received with a length byte
        > with a value greater than PKTLEN will be discarded.
        """
        return self._read_single_byte(ConfigurationRegisterAddress.PKTLEN)

    def set_packet_length_bytes(self, packet_length: int) -> None:
        """
        see get_packet_length_bytes()
        """
        assert 1 <= packet_length <= 255, f"unsupported packet length {packet_length}"
        self._write_burst(
            start_register=ConfigurationRegisterAddress.PKTLEN, values=[packet_length]
        )

    def _disable_data_whitening(self):
        """
        PKTCTRL0.WHITE_DATA

        see "15.1 Data Whitening"

        > By setting PKTCTRL0.WHITE_DATA=1 [default],
        > all data, except the preamble and the sync word
        > will be XOR-ed with a 9-bit pseudo-random (PN9)
        > sequence before being transmitted.
        """
        pktctrl0 = self._read_single_byte(ConfigurationRegisterAddress.PKTCTRL0)
        pktctrl0 &= 0b10111111
        self._write_burst(
            start_register=ConfigurationRegisterAddress.PKTCTRL0, values=[pktctrl0]
        )

    def disable_checksum(self) -> None:
        """
        PKTCTRL0.CRC_EN

        Disable automatic 2-byte cyclic redundancy check (CRC) sum
        appending in TX mode and checking in RX mode.

        See "Figure 19: Packet Format".
        """
        pktctrl0 = self._read_single_byte(ConfigurationRegisterAddress.PKTCTRL0)
        pktctrl0 &= 0b11111011
        self._write_burst(
            start_register=ConfigurationRegisterAddress.PKTCTRL0, values=[pktctrl0]
        )

    def _get_transceive_mode(self) -> _TransceiveMode:
        pktctrl0 = self._read_single_byte(ConfigurationRegisterAddress.PKTCTRL0)
        return _TransceiveMode((pktctrl0 >> 4) & 0b11)

    def _set_transceive_mode(self, mode: _TransceiveMode) -> None:
        _LOGGER.info("changing transceive mode to %s", mode.name)
        pktctrl0 = self._read_single_byte(ConfigurationRegisterAddress.PKTCTRL0)
        pktctrl0 &= ~0b00110000
        pktctrl0 |= mode << 4
        self._write_burst(
            start_register=ConfigurationRegisterAddress.PKTCTRL0, values=[pktctrl0]
        )

    def get_packet_length_mode(self) -> PacketLengthMode:
        pktctrl0 = self._read_single_byte(ConfigurationRegisterAddress.PKTCTRL0)
        return PacketLengthMode(pktctrl0 & 0b11)

    def set_packet_length_mode(self, mode: PacketLengthMode) -> None:
        pktctrl0 = self._read_single_byte(ConfigurationRegisterAddress.PKTCTRL0)
        pktctrl0 &= 0b11111100
        pktctrl0 |= mode
        self._write_burst(
            start_register=ConfigurationRegisterAddress.PKTCTRL0, values=[pktctrl0]
        )

    def _get_patable(self) -> typing.Tuple[int, ...]:
        """
        see "10.6 PATABLE Access" and "24 Output Power Programming"

        default: (0xC6, 0, 0, 0, 0, 0, 0, 0)
        """
        return tuple(
            self._read_burst(
                start_register=PatableAddress.PATABLE, length=self._PATABLE_LENGTH_BYTES
            )
        )

    def _set_patable(self, settings: typing.Iterable[int]):
        settings = list(settings)
        assert all(0 <= l <= 0xFF for l in settings), settings
        assert 0 < len(settings) <= self._PATABLE_LENGTH_BYTES, settings
        self._write_burst(start_register=PatableAddress.PATABLE, values=settings)

    def get_output_power(self) -> typing.Tuple[int, ...]:
        """
        Returns the enabled output power settings
        (up to 8 bytes of the PATABLE register).

        see .set_output_power()
        """
        return self._get_patable()[: self._get_power_amplifier_setting_index() + 1]

    def set_output_power(self, power_settings: typing.Iterable[int]) -> None:
        """
        Configures output power levels by setting PATABLE and FREND0.PA_POWER.
        Up to 8 bytes may be provided.

        > [PATABLE] provides flexible PA power ramp up and ramp down
        > at the start and end of transmission when using 2-FSK, GFSK,
        > 4-FSK, and MSK modulation as well as ASK modulation shaping.

        For OOK modulation, exactly 2 bytes must be provided:
        0 to turn off the transmission for logical 0,
        and a level > 0 to turn on the transmission for logical 1.
        >>> transceiver.set_output_power((0, 0xC6))

        See "Table 39: Optimum PATABLE Settings for Various Output Power Levels [...]"
        and section "24 Output Power Programming".
        """
        power_settings = list(power_settings)
        # checks in sub-methods
        self._set_power_amplifier_setting_index(len(power_settings) - 1)
        self._set_patable(power_settings)

    def _flush_tx_fifo_buffer(self) -> None:
        # > Only issue SFTX in IDLE or TXFIFO_UNDERFLOW states.
        _LOGGER.debug("flushing tx fifo buffer")
        self._command_strobe(StrobeAddress.SFTX)

    def transmit(self, payload: bytes) -> None:
        """
        The most significant bit is transmitted first.

        In variable packet length mode,
        a byte indicating the packet's length will be prepended.

        > In variable packet length mode,
        > the packet length is configured by the first byte [...].
        > The packet length is defined as the payload data,
        > excluding the length byte and the optional CRC.
        from "15.2 Packet Format"

        Call .set_packet_length_mode(cc1101.PacketLengthMode.FIXED)
        to switch to fixed packet length mode.
        """
        # see "15.2 Packet Format"
        # > In variable packet length mode, [...]
        # > The first byte written to the TXFIFO must be different from 0.
        packet_length_mode = self.get_packet_length_mode()
        packet_length = self.get_packet_length_bytes()
        if packet_length_mode == PacketLengthMode.VARIABLE:
            if not payload:
                raise ValueError(f"empty payload {payload!r}")
            if len(payload) > packet_length:
                raise ValueError(
                    f"payload exceeds maximum payload length of {packet_length} bytes"
                    "\nsee .get_packet_length_bytes()"
                    f"\npayload: {payload!r}"
                )
            payload = int.to_bytes(len(payload), length=1, byteorder="big") + payload
        elif (
            packet_length_mode == PacketLengthMode.FIXED
            and len(payload) != packet_length
        ):
            raise ValueError(
                f"expected payload length of {packet_length} bytes, got {len(payload)}"
                + "\nsee .set_packet_length_mode() and .get_packet_length_bytes()"
                + f"\npayload: {payload!r}"
            )
        marcstate = self.get_main_radio_control_state_machine_state()
        if marcstate != MainRadioControlStateMachineState.IDLE:
            raise RuntimeError(
                f"device must be idle before transmission (current marcstate: {marcstate.name})"
            )
        self._flush_tx_fifo_buffer()
        self._write_burst(FIFORegisterAddress.TX, list(payload))
        _LOGGER.info("transmitting 0x%s (%r)", payload.hex(), payload)
        self._command_strobe(StrobeAddress.STX)

    @contextlib.contextmanager
    def asynchronous_transmission(self) -> typing.Iterator[Pin]:
        """
        > [...] the GDO0 pin is used for data input [...]
        > The CC1101 modulator samples the level of the asynchronous input
        > 8 times faster than the programmed data rate.
        see "27.1 Asynchronous Serial Operation"

        >>> with cc1101.CC1101() as transceiver:
        >>>     transceiver.set_base_frequency_hertz(433.92e6)
        >>>     transceiver.set_symbol_rate_baud(600)
        >>>     print(transceiver)
        >>>     with transceiver.asynchronous_transmission():
        >>>         # send digital signal to GDO0 pin
        """
        self._set_transceive_mode(_TransceiveMode.ASYNCHRONOUS_SERIAL)
        self._command_strobe(StrobeAddress.STX)
        try:
            # > In TX, the GDO0 pin is used for data input (TX data).
            yield Pin.GDO0
        finally:
            self._command_strobe(StrobeAddress.SIDLE)
            self._set_transceive_mode(_TransceiveMode.FIFO)

    def _enable_receive_mode(self) -> None:
        self._command_strobe(StrobeAddress.SRX)

    def _get_received_packet(self) -> typing.Optional[_ReceivedPacket]:  # unstable
        """
        see section "20 Data FIFO"
        """
        rxbytes = self._read_status_register(StatusRegisterAddress.RXBYTES)
        # PKTCTRL1.APPEND_STATUS is enabled by default
        if rxbytes < 2:
            return None
        buffer = self._read_burst(start_register=FIFORegisterAddress.RX, length=rxbytes)
        return _ReceivedPacket(
            payload=bytes(buffer[:-2]),
            rssi_index=buffer[-2],
            checksum_valid=bool(buffer[-1] >> 7),
            link_quality_indicator=buffer[-1] & 0b0111111,
        )

    def _wait_for_packet(  # unstable
        self,
        timeout: datetime.timedelta,
        gdo0_gpio_line_name: bytes = b"GPIO24",  # recommended in README.md
    ) -> typing.Optional[_ReceivedPacket]:
        """
        depends on IOCFG0 == 0b00000001 (see _configure_defaults)
        """
        # pylint: disable=protected-access
        gdo0 = cc1101._gpio.GPIOLine.find(name=gdo0_gpio_line_name)
        self._enable_receive_mode()
        if not gdo0.wait_for_rising_edge(consumer=b"CC1101:GDO0", timeout=timeout):
            self._command_strobe(StrobeAddress.SIDLE)
            _LOGGER.debug(
                "reached timeout of %.02f seconds while waiting for packet",
                timeout.total_seconds(),
            )
            return None  # timeout
        return self._get_received_packet()
