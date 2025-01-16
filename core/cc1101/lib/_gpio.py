# python-cc1101 - Python Library to Transmit RF Signals via CC1101 Transceivers
#
# Copyright (C) 2021 Fabian Peter Hammerle <fabian@hammerle.me>
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

import ctypes
import ctypes.util
import datetime
import errno
import functools

# could not find Debian's python3-libgpiod on pypi.org
# https://salsa.debian.org/debian/libgpiod does not provide setup.py or setup.cfg


@functools.lru_cache(maxsize=1)
def _load_libgpiod() -> ctypes.CDLL:
    filename = ctypes.util.find_library("gpiod")
    if not filename:
        raise FileNotFoundError(
            "Failed to find libgpiod."
            "\nOn Debian-based systems, like Raspberry Pi OS / Raspbian,"
            " libgpiod can be installed via"
            "\n\tsudo apt-get install --no-install-recommends libgpiod2"
        )
    return ctypes.CDLL(filename, use_errno=True)


class _c_timespec(ctypes.Structure):
    """
    struct timespec {
        time_t tv_sec;
        long tv_nsec;
    };
    """

    # pylint: disable=too-few-public-methods,invalid-name; struct

    _fields_ = [("tv_sec", ctypes.c_long), ("tv_nsec", ctypes.c_long)]


class GPIOLine:
    def __init__(self, pointer: ctypes.c_void_p) -> None:
        assert pointer != 0
        self._pointer = pointer

    @classmethod
    def find(cls, name: bytes) -> GPIOLine:
        # > If this routine succeeds, the user must manually close the GPIO chip
        # > owning this line to avoid memory leaks.
        pointer: int = _load_libgpiod().gpiod_line_find(name)
        # > If the line could not be found, this functions sets errno to ENOENT.
        if pointer == 0:
            err = ctypes.get_errno()
            if err == errno.EACCES:
                # > [PermissionError] corresponds to errno EACCES and EPERM.
                raise PermissionError(
                    f"Failed to access GPIO line {name.decode()!r}."
                    "\nVerify that the current user has read and write access for /dev/gpiochip*."
                    "\nOn some systems, like Raspberry Pi OS / Raspbian,"
                    "\n\tsudo usermod -a -G gpio $USER"
                    "\nfollowed by a re-login grants sufficient permissions."
                )
            if err == errno.ENOENT:
                # > [FileNotFoundError] corresponds to errno ENOENT.
                # https://docs.python.org/3/library/exceptions.html#FileNotFoundError
                raise FileNotFoundError(
                    f"GPIO line {name.decode()!r} does not exist."
                    "\nRun command `gpioinfo` to get a list of all available GPIO lines."
                )
            raise OSError(
                f"Failed to open GPIO line {name.decode()!r}: {errno.errorcode[err]}"
            )
        return cls(pointer=ctypes.c_void_p(pointer))

    def __del__(self):
        # > Close a GPIO chip owning this line and release all resources.
        # > After this function returns, the line must no longer be used.
        if self._pointer:
            _load_libgpiod().gpiod_line_close_chip(self._pointer)
        # might make debugging easier in case someone calls __del__ twice
        self._pointer = None

    def wait_for_rising_edge(
        self, *, consumer: bytes, timeout: datetime.timedelta
    ) -> bool:
        """
        Return True, if an event occured; False on timeout.
        """
        if (
            _load_libgpiod().gpiod_line_request_rising_edge_events(
                self._pointer, consumer
            )
            != 0
        ):
            err = ctypes.get_errno()
            raise OSError(
                f"Request for rising edge event notifications failed ({errno.errorcode[err]})."
                + ("\nBlocked by another process?" if err == errno.EBUSY else "")
            )
        timeout_timespec = _c_timespec(
            int(timeout.total_seconds()), timeout.microseconds * 1000
        )
        result: int = _load_libgpiod().gpiod_line_event_wait(
            self._pointer, ctypes.pointer(timeout_timespec)
        )
        _load_libgpiod().gpiod_line_release(self._pointer)
        if result == -1:
            raise OSError("Failed to wait for rising edge event notification.")
        return result == 1
