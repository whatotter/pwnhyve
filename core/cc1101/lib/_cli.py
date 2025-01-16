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

import argparse
import logging
import sys
import typing

import cc1101
import cc1101.options

_LOGGER = logging.getLogger(__name__)


def _add_common_args(argparser: argparse.ArgumentParser) -> None:
    argparser.add_argument("-f", "--base-frequency-hertz", type=int)
    argparser.add_argument("-r", "--symbol-rate-baud", type=int)
    argparser.add_argument(
        "-s",
        "--sync-mode",
        type=str,
        choices=[m.name.lower().replace("_", "-") for m in cc1101.options.SyncMode],
    )
    argparser.add_argument(
        "-l",
        "--packet-length-mode",
        type=str,
        choices=[m.name.lower() for m in cc1101.options.PacketLengthMode],
    )
    argparser.add_argument("--disable-checksum", action="store_true")
    argparser.add_argument(
        "-p",
        "--output-power",
        metavar="SETTING",
        dest="output_power_settings",
        type=int,
        nargs="+",
        help="Configures output power levels by setting PATABLE and FREND0.PA_POWER."
        " Up to 8 bytes may be provided."
        # add when making _set_modulation_format() public
        # ' "[PATABLE] provides flexible PA power ramp up and ramp down'
        # " at the start and end of transmission when using 2-FSK, GFSK,"
        # ' 4-FSK, and MSK modulation as well as ASK modulation shaping."'
        " For OOK modulation, exactly 2 bytes must be provided:"
        " 0 to turn off the transmission for logical 0,"
        " and a level > 0 to turn on the transmission for logical 1"
        " (e.g., --output-power 0 198)."
        ' See "Table 39: Optimum PATABLE Settings for Various Output Power Levels [...]"'
        ' and section "24 Output Power Programming".',
    )
    argparser.add_argument("-d", "--debug", action="store_true")


def _init_logging(args: argparse.Namespace) -> None:
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s:%(levelname)s:%(name)s:%(funcName)s:%(message)s"
        if args.debug
        else "%(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )


def _configure_via_args(
    *,
    transceiver: cc1101.CC1101,
    args: argparse.Namespace,
    packet_length_if_fixed: typing.Optional[int],
) -> None:
    if args.base_frequency_hertz:
        transceiver.set_base_frequency_hertz(args.base_frequency_hertz)
    if args.symbol_rate_baud:
        transceiver.set_symbol_rate_baud(args.symbol_rate_baud)
    if args.sync_mode:
        transceiver.set_sync_mode(
            cc1101.options.SyncMode[args.sync_mode.upper().replace("-", "_")]
        )
    if args.packet_length_mode:
        packet_length_mode = cc1101.options.PacketLengthMode[
            args.packet_length_mode.upper()
        ]
        # default: variable length
        transceiver.set_packet_length_mode(packet_length_mode)
        # default: 255 (maximum)
        if (
            packet_length_if_fixed is not None
            and packet_length_mode == cc1101.options.PacketLengthMode.FIXED
        ):
            transceiver.set_packet_length_bytes(packet_length_if_fixed)
    if args.disable_checksum:
        transceiver.disable_checksum()
    if args.output_power_settings:
        transceiver.set_output_power(args.output_power_settings)


def _export_config():
    argparser = argparse.ArgumentParser(
        description="Export values in CC1101's configuration registers"
        " after applying settings specified via command-line arguments & options",
        allow_abbrev=False,
    )
    _add_common_args(argparser)
    argparser.add_argument("--format", choices=["python-list"], default="python-list")
    args = argparser.parse_args()
    _init_logging(args)
    _LOGGER.debug("args=%r", args)
    with cc1101.CC1101(lock_spi_device=True) as transceiver:
        _configure_via_args(
            transceiver=transceiver, args=args, packet_length_if_fixed=None
        )
        _LOGGER.info("%s", transceiver)
        print("[")
        for register_index, (register, value) in enumerate(
            transceiver.get_configuration_register_values().items()
        ):
            assert register_index == register.value
            print(
                "0b{value:08b}, # 0x{value:02x} {register_name}".format(
                    value=value, register_name=register.name
                )
            )
        print("]")
        print(
            # pylint: disable=protected-access; internal function & method
            "# PATABLE = "
            + cc1101._format_patable(transceiver._get_patable(), insert_spaces=True)
        )


def _transmit():
    argparser = argparse.ArgumentParser(
        description="Transmits the payload provided via standard input (stdin)"
        " ASK/OOK-modulated in big-endian bit order.",
        allow_abbrev=False,
    )
    _add_common_args(argparser)
    args = argparser.parse_args()
    _init_logging(args)
    _LOGGER.debug("args=%r", args)
    payload = sys.stdin.buffer.read()
    # configure transceiver after reading from stdin
    # to avoid delay between configuration and transmission if pipe is slow
    with cc1101.CC1101(lock_spi_device=True) as transceiver:
        _configure_via_args(
            transceiver=transceiver, args=args, packet_length_if_fixed=len(payload)
        )
        _LOGGER.info("%s", transceiver)
        transceiver.transmit(payload)
