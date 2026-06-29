import logging
import os
import time
from typing import List, Optional, Tuple, Union

from RPi import GPIO
import gpiozero as gpioz
from core.pio.fastio import FastIO

import core.cc1101.lib as cc1101
from core.cc1101.lib.options import (
    _TransceiveMode,
    ModulationFormat,
    SyncMode,
    PacketLengthMode,
)
from core.cc1101.lib.addresses import (
    ConfigurationRegisterAddress,
    FIFORegisterAddress,
    PatableAddress,
    StatusRegisterAddress,
    StrobeAddress,
)
from core.cc1101.lib import MainRadioControlStateMachineState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GDO0 = 12
GDO2 = 23
CSN = 18

fio = FastIO()


class pCC1101:
    PATABLE_433MHZ = {
        0x1b: "-16.2dBm",
        0x1e: "-14.3dBm",
        0x26: "-9.9dBm",
        0x6c: "-7.1dBm",
        0x37: "-5.6dBm",
        0x2c: "-4.7dBm",
        0x2e: "-3.5dBm",
        0x65: "-2.9dBm",
        0x3b: "-2.5dBm",
        0x64: "-2.3dBm",
        0x54: "-2.2dBm",
        0x3c: "-2.1dBm",
        0x3e: "-1.4dBm",
        0x61: "-0.5dBm",
        0x8c: "1.9dBm",
        0x87: "4.0dBm",
        0xCD: "5.5dBm",
        0xca: "6.4dBm",
        0xc9: "6.8dBm",
        0xc8: "7.1dBm",
        0xc7: "7.4dBm",
        0xc6: "7.8dBm",
        0xc5: "8.1dBm",
        0xc4: "8.5dBm",
        0xc3: "8.8dBm",
        0xc2: "9.2dBm",
        0xc1: "9.5dBm",
        0xc0: "9.9dBm",
    }

    def __init__(self, spi_bus: int = 0, spi_chip_select: int = 1, retries: int = 5):
        self.trs: Optional[cc1101.CC1101] = None
        self.success = False
        self.err: Optional[Exception] = None

        self.minFreq = 287.8

        for x in range(retries):
            try:
                self.trs = cc1101.CC1101(
                    spi_bus=spi_bus, spi_chip_select=spi_chip_select
                ).__enter__()
                logger.info("CC1101 init successful")
                self.success = True
                break
            except Exception as e:
                self.err = e
                logger.warning("CC1101 init attempt %d failed: %s", x + 1, e)
                self._csnRst()

        if not self.success:
            raise RuntimeError("CC1101 init failed after %d retries" % retries) from self.err

        self.snval = 0
        self.currentFreq: float = 303.81e6
        self.power = 0xC0
        self.patable = dict(self.PATABLE_433MHZ)

        self._m4RxBw = 0
        self._pc0WDATA = 0
        self._pc0PktForm = 0
        self._pc0CRC_EN = 0
        self._pc0LenConf = 0

        self.mode: str = "tx"

        self._setDefaults()
        self.setupRawTransmission()
        self.adjustOOKSensitivity(0, self.power)
        self.rawTransmitBits("10101010", delayms=10)

    # ------------------------------------------------------------------
    #  Sleep / Reset / Close
    # ------------------------------------------------------------------

    def sleepMode(self) -> None:
        self.trs._command_strobe(StrobeAddress.SIDLE)
        self.trs._command_strobe(StrobeAddress.SPWD)

    def rst(self) -> None:
        self._setDefaults()
        logger.info("cc1101 defaults restored")
        self.setupRawTransmission()
        logger.info("cc1101 set to TX")
        self.rawTransmitBits("10101010", delayms=100)
        logger.info("transmitted example bits")
        self.mode = "tx"

    def close(self) -> None:
        self.rst()
        self.trs._command_strobe(StrobeAddress.SIDLE)

    # ------------------------------------------------------------------
    #  GPIO helpers
    # ------------------------------------------------------------------

    def csn(self, value: int) -> None:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(CSN, GPIO.OUT)
        GPIO.output(CSN, value)

    def _csnRst(self) -> None:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(CSN, GPIO.IN)
        time.sleep(2.5)
        GPIO.setup(CSN, GPIO.OUT)
        GPIO.output(CSN, 1)
        time.sleep(0.5)
        GPIO.cleanup()

    # ------------------------------------------------------------------
    #  Frequency
    # ------------------------------------------------------------------

    def setFreq(self, val: float, doCalc: bool = True) -> None:
        """
        Set frequency. `val` must be a float, ergo `303.914`.

        Set `doCalc` to `False` if targeting a very specific frequency, this disables the `val * 10**6` calculation needed for the CC1101.

        Highly recommended to redo your configuration, so if you're trying to recieve, run `xcvr.setupRawRecieve()` after.
        Or, if doing TX, `xcvr.setupRawTransmission()`
        """
        self.trs._command_strobe(StrobeAddress.SIDLE)
        if doCalc:
            self.currentFreq = val * 10**6
        else:
            self.currentFreq = val
        logger.info("setting frequency to %s Hz", self.currentFreq)
        self.trs.set_base_frequency_hertz(self.currentFreq)
        time.sleep(0.01)
        abcd = self.trs.get_base_frequency_hertz()
        logger.info(
            "REQUESTED: %s -> ACTUAL: %.2f MHz", val, abcd / 1e6
        )

    def getFreqMHz(self) -> float:
        return self.trs.get_base_frequency_hertz() / 1e6

    # ------------------------------------------------------------------
    #  Modulation
    # ------------------------------------------------------------------

    def setModulation(self, mod: Union[str, ModulationFormat]) -> None:
        if isinstance(mod, str):
            table = {
                "2fsk": ModulationFormat.FSK2,
                "gfsk": ModulationFormat.GFSK,
                "ook": ModulationFormat.ASK_OOK,
                "4fsk": ModulationFormat.FSK4,
                "msk": ModulationFormat.MSK,
            }
            mod = table[mod.lower()]
        self.trs._set_modulation_format(mod)
        logger.info("modulation set to %s", mod.name)

    def getModulation(self) -> ModulationFormat:
        return self.trs.get_modulation_format()

    # ------------------------------------------------------------------
    #  Symbol / Data Rate
    # ------------------------------------------------------------------

    def setDataRate(self, baud: float) -> None:
        self.trs.set_symbol_rate_baud(baud)

    def getDataRate(self) -> float:
        return self.trs.get_symbol_rate_baud()

    # ------------------------------------------------------------------
    #  RX Bandwidth
    # ------------------------------------------------------------------

    def _split_MDMCFG4(self) -> None:
        calc = self.trs._read_status_register(ConfigurationRegisterAddress.MDMCFG4)
        self._m4RxBw = 0
        m4DaRa = 0
        while True:
            if calc >= 64:
                calc -= 64
                self._m4RxBw += 64
            elif calc >= 16:
                calc -= 16
                self._m4RxBw += 16
            else:
                m4DaRa = calc
                break
        self._m4DaRa = m4DaRa

    def setRxBW(self, f: float) -> None:
        self._split_MDMCFG4()
        s1 = 3
        s2 = 3
        for _ in range(3):
            if f > 101.5625:
                f /= 2
                s1 -= 1
            else:
                break
        for _ in range(3):
            if f > 58.1:
                f /= 1.25
                s2 -= 1
            else:
                break
        s1 *= 64
        s2 *= 16
        self._m4RxBw = s1 + s2
        self.trs._write_burst(
            ConfigurationRegisterAddress.MDMCFG4, [self._m4RxBw + self._m4DaRa]
        )

    # ------------------------------------------------------------------
    #  CCMode (raw asynchronous serial mode)
    # ------------------------------------------------------------------

    def setCCMode(self, v: int) -> None:
        if v == 1:
            self.trs._write_burst(ConfigurationRegisterAddress.IOCFG2, [0x0B])
            self.trs._write_burst(ConfigurationRegisterAddress.IOCFG0, [0x06])
            self.trs._write_burst(ConfigurationRegisterAddress.PKTCTRL0, [0x05])
            self.trs._write_burst(ConfigurationRegisterAddress.MDMCFG3, [0x05])
            self.trs._write_burst(ConfigurationRegisterAddress.MDMCFG4, [11 + self._m4RxBw])
        else:
            self.trs._write_burst(ConfigurationRegisterAddress.IOCFG2, [0x0D])
            self.trs._write_burst(ConfigurationRegisterAddress.IOCFG0, [0x0D])
            self.trs._write_burst(ConfigurationRegisterAddress.PKTCTRL0, [0x32])
            self.trs._write_burst(ConfigurationRegisterAddress.MDMCFG3, [0x93])
            self.trs._write_burst(ConfigurationRegisterAddress.MDMCFG4, [7 + self._m4RxBw])
        self.trs._set_modulation_format(ModulationFormat.ASK_OOK)

    # ------------------------------------------------------------------
    #  TX Setup
    # ------------------------------------------------------------------

    def setupRawTransmission(self, output_power: int = 0xCB) -> None:
        self.setCCMode(0)
        self.trs._set_transceive_mode(_TransceiveMode.ASYNCHRONOUS_SERIAL)
        self.trs._command_strobe(StrobeAddress.SIDLE)
        self.trs._command_strobe(StrobeAddress.STX)
        self.mode = "tx"
        self.adjustOOKSensitivity(0, self.power)

    def setCarrier(self) -> None:
        self.trs._command_strobe(StrobeAddress.SIDLE)
        self.trs._set_transceive_mode(_TransceiveMode.ASYNCHRONOUS_SERIAL)
        self.setCCMode(0)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(GDO0, GPIO.OUT)
        GPIO.output(GDO0, GPIO.HIGH)
        self.trs._command_strobe(StrobeAddress.STX)
        self.mode = "tx"

    def unsetCarrier(self) -> None:
        self.trs._command_strobe(StrobeAddress.SIDLE)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(GDO0, GPIO.IN)

    def revertTransceiver(self) -> None:
        self.trs._command_strobe(StrobeAddress.SIDLE)
        self.trs._command_strobe(StrobeAddress.SRX)

    # ------------------------------------------------------------------
    #  RX Setup
    # ------------------------------------------------------------------

    def setupRawRecieve(self) -> None:
        self.setCCMode(0)
        self.trs._set_transceive_mode(_TransceiveMode.ASYNCHRONOUS_SERIAL)
        self.trs._command_strobe(StrobeAddress.SIDLE)
        self.trs._command_strobe(StrobeAddress.SRX)
        self.mode = "rx"

    # ------------------------------------------------------------------
    #  Power / PATABLE
    # ------------------------------------------------------------------

    def adjustOOKSensitivity(self, zero: int, one: int) -> None:
        assert 0 <= zero <= 0xFF, "zero out of range"
        assert 0 <= one <= 0xFF, "one out of range"
        self.trs.set_output_power((zero, one))

    def getOutputPower(self) -> Tuple[int, ...]:
        return self.trs.get_output_power()

    def setPowerdBm(self, dbm: float) -> None:
        closest = min(
            self.PATABLE_433MHZ.items(),
            key=lambda kv: abs(float(kv[1].replace("dBm", "")) - dbm),
        )
        reg_val, label = closest
        logger.info("setting power to %s (0x%02X)", label, reg_val)
        self.adjustOOKSensitivity(0, reg_val)

    # ------------------------------------------------------------------
    #  TX methods
    # ------------------------------------------------------------------

    def rawTransmitBytes(self, bt: bytes) -> None:
        """
        Transmit !BYTES! onto GDO0
        """
        os.remove("fastio.bin")
        with open("fastio.bin", "wb") as f:
            f.write(bt)
            f.flush()
        fio.send(GDO0, "fastio.bin")

    def rawTransmitBits(self, bits, **kwargs) -> None:
        """
        Transmit !BITS! onto GDO0 
        """
        fio.send(GDO0, [int(x) for x in bits], ns=500)

    def rawTransmitBin(self, binfile: str) -> None:
        fio.send(GDO0, binfile, ns=500)

    def flipperTransmit(self, RAW_Data: str) -> None:
        fio.flipperSend(GDO0, RAW_Data)

    # ------------------------------------------------------------------
    #  RX methods
    # ------------------------------------------------------------------

    def setMS(self, delayms:int) -> None:
        """
        Sets FastIO speed, in microseconds
        """
        fio.setNS(delayms * 1000)

    def recvSamples(self, bits: int, delayms: int = 5) -> list[bool]:
        if delayms != -1: # don't change FastIO speed if it's not requested to
            fio.setNS(delayms * 1000)

        return fio.readSamples(GDO2, bits)[0]

    def recvInf(self) -> None:
        fio.setNS(1000)
        fio.infread(GDO2, filename="/tmp/rawrx")

    def recvStop(self) -> list:
        fio.close()
        return fio.__parseBin__(GDO2, binf="/tmp/rawrx", remove=True)

    def flipperRecv(self):
        raise NotImplementedError("use flipperconv class")

    # ------------------------------------------------------------------
    #  Register-level helpers
    # ------------------------------------------------------------------

    def readRegister(self, addr: int) -> int:
        return self.trs._read_single_byte(ConfigurationRegisterAddress(addr))

    def writeRegister(self, addr: int, value: int) -> None:
        self.trs._write_burst(ConfigurationRegisterAddress(addr), [value])

    def readBurst(self, start_addr: int, length: int) -> List[int]:
        return self.trs._read_burst(ConfigurationRegisterAddress(start_addr), length)

    def writeBurst(self, start_addr: int, values: List[int]) -> None:
        self.trs._write_burst(ConfigurationRegisterAddress(start_addr), values)

    def dumpRegisters(self) -> None:
        for reg in ConfigurationRegisterAddress:
            val = self.trs._read_single_byte(reg)
            logger.info("  0x%02X (%s) = 0x%02X", reg.value, reg.name, val)

    def readStatusRegister(self, addr: int) -> int:
        return self.trs._read_status_register(StatusRegisterAddress(addr))

    def readRSSI(self) -> float:
        raw = self.trs._read_status_register(StatusRegisterAddress.RSSI)
        if raw >= 128:
            return (raw - 256) / 2 - 74
        return raw / 2 - 74

    def readLQI(self) -> int:
        return self.trs._read_status_register(StatusRegisterAddress.LQI) & 0b01111111

    def getMarcState(self) -> MainRadioControlStateMachineState:
        return self.trs.get_main_radio_control_state_machine_state()

    def getPartNumber(self) -> int:
        return self.trs._read_status_register(StatusRegisterAddress.PARTNUM)

    def getVersion(self) -> int:
        return self.trs._read_status_register(StatusRegisterAddress.VERSION)

    def getFrequencyEstimate(self) -> int:
        return self.trs._read_status_register(StatusRegisterAddress.FREQEST)

    # ------------------------------------------------------------------
    #  Sync word
    # ------------------------------------------------------------------

    def setSyncWord(self, word: bytes) -> None:
        self.trs.set_sync_word(word)

    def getSyncWord(self) -> bytes:
        return self.trs.get_sync_word()

    # ------------------------------------------------------------------
    #  Preamble
    # ------------------------------------------------------------------

    def setPreambleLength(self, length: int) -> None:
        self.trs.set_preamble_length_bytes(length)

    def getPreambleLength(self) -> int:
        return self.trs.get_preamble_length_bytes()

    def setPreambleIndex(self, index: int) -> None:
        self.trs._set_preamble_length_index(index)

    # ------------------------------------------------------------------
    #  Packet format helpers
    # ------------------------------------------------------------------

    def setPktFormat(self, val: str) -> None:
        if val == "async":
            self.trs._set_transceive_mode(_TransceiveMode.ASYNCHRONOUS_SERIAL)
        elif val == "fifo":
            self.trs._set_transceive_mode(_TransceiveMode.FIFO)
        elif val == "sync":
            self.trs._set_transceive_mode(_TransceiveMode.SYNCHRONOUS_SERIAL)
        elif val == "random":
            self.trs._set_transceive_mode(_TransceiveMode.RANDOM_TRANSMISSION)

    def setPacketLengthMode(self, mode: str) -> None:
        table = {"fixed": PacketLengthMode.FIXED, "variable": PacketLengthMode.VARIABLE}
        self.trs.set_packet_length_mode(table[mode.lower()])

    def setPacketLength(self, length: int) -> None:
        self.trs.set_packet_length_bytes(length)

    def getPacketLength(self) -> int:
        return self.trs.get_packet_length_bytes()

    # ------------------------------------------------------------------
    #  Checksum / Whitening
    # ------------------------------------------------------------------

    def disableChecksum(self) -> None:
        self.trs.disable_checksum()

    def enableManchester(self) -> None:
        self.trs.enable_manchester_code()

    # ------------------------------------------------------------------
    #  Sync mode
    # ------------------------------------------------------------------

    def setSyncMode(self, mode: str) -> None:
        table = {
            "none": SyncMode.NO_PREAMBLE_AND_SYNC_WORD,
            "16_15": SyncMode.TRANSMIT_16_MATCH_15_BITS,
            "16_16": SyncMode.TRANSMIT_16_MATCH_16_BITS,
            "32_30": SyncMode.TRANSMIT_32_MATCH_30_BITS,
        }
        self.trs.set_sync_mode(table[mode.lower()])

    def getSyncMode(self) -> str:
        return self.trs.get_sync_mode().name.lower()

    # ------------------------------------------------------------------
    #  CCA / Channel assessment
    # ------------------------------------------------------------------

    def isChannelClear(self) -> bool:
        rssi = self.readRSSI()
        return rssi < -80

    def getRSSIdBm(self) -> float:
        return self.readRSSI()

    def getChannelNumber(self) -> int:
        return self.trs._read_single_byte(ConfigurationRegisterAddress.CHANNR)

    def setChannel(self, ch: int) -> None:
        assert 0 <= ch <= 0xFF
        self.trs._write_burst(ConfigurationRegisterAddress.CHANNR, [ch])

    # ------------------------------------------------------------------
    #  Defaults
    # ------------------------------------------------------------------

    def _setDefaults(self) -> None:
        self.trs._command_strobe(StrobeAddress.SIDLE)
        self.setRxBW(650.0)
        self.setCCMode(0)
        self.trs.set_base_frequency_hertz(self.currentFreq)
        time.sleep(0.5)
        abcd = self.trs.get_base_frequency_hertz()
        logger.info("base_frequency=%.2f MHz", abcd / 1e6)
        self.trs._write_burst(ConfigurationRegisterAddress.MDMCFG1, [0x02])
        self.trs._write_burst(ConfigurationRegisterAddress.MDMCFG0, [0xF8])
        self.trs._write_burst(ConfigurationRegisterAddress.DEVIATN, [0x90])
        self.trs._write_burst(ConfigurationRegisterAddress.FREND1, [0x56])
        self.trs._write_burst(ConfigurationRegisterAddress.MCSM0, [0x18])
        self.trs._write_burst(ConfigurationRegisterAddress.FOCCFG, [0x16])
        self.trs._write_burst(ConfigurationRegisterAddress.BSCFG, [0x1C])
        self.trs._write_burst(0x1B, [0xC7])
        self.trs._write_burst(0x1C, [0x00])
        self.trs._write_burst(0x1D, [0xB2])
        self.trs._write_burst(ConfigurationRegisterAddress.FSCAL3, [0xE9])
        self.trs._write_burst(ConfigurationRegisterAddress.FSCAL2, [0x2A])
        self.trs._write_burst(ConfigurationRegisterAddress.FSCAL1, [0x00])
        self.trs._write_burst(ConfigurationRegisterAddress.FSCAL0, [0x1F])
        self.trs._write_burst(ConfigurationRegisterAddress.PKTCTRL1, [0x04])
        self.trs._write_burst(ConfigurationRegisterAddress.ADDR, [0x00])
        self.trs._write_burst(ConfigurationRegisterAddress.PKTLEN, [0x00])

    # ------------------------------------------------------------------
    #  Legacy compat: split_PKTCTRL0 / Split_MDMCFG4 (kept for API compat)
    # ------------------------------------------------------------------

    def split_PKTCTRL0(self):
        calc = self.trs._read_status_register(ConfigurationRegisterAddress.PKTCTRL0)
        self._pc0WDATA = 0
        self._pc0PktForm = 0
        self._pc0CRC_EN = 0
        self._pc0LenConf = 0
        while True:
            if calc >= 64:
                calc -= 64
                self._pc0WDATA += 64
            elif calc >= 16:
                calc -= 16
                self._pc0PktForm += 16
            elif calc >= 4:
                calc -= 4
                self._pc0CRC_EN += 4
            else:
                self._pc0LenConf = calc
                break

    def Split_MDMCFG4(self):
        self._split_MDMCFG4()
