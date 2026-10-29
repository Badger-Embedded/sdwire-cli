"""SDWireC model.

A hub with the card reader on port 1 and the FTDI chip on port 2. Bit 0 of the
CBUS value set through SET_BITMODE selects the side: 1 connects the card to
the reader (host), 0 to the target. The reader keeps its block device and
reports a medium (size > 0) only while the card is on the host side.
"""

import errno
from dataclasses import dataclass

from .spec import PRODUCT, SPEC
from e2e.framework.device import DEFAULT_CARD, CardSide, SimDevice
from e2e.framework.sim.block import SimBlockDevice
from e2e.framework.sim.testbed import Testbed
from e2e.framework.sim.usb import (
    HUB_INTERFACE,
    USB_CLASS_HUB,
    USB_CLASS_MASS_STORAGE,
    USB_CLASS_VENDOR,
    Interface,
    Setup,
    SimUsbDevice,
)

SIO_SET_BITMODE = 0x0B
BITMODE_CBUS = 0x20
FT232R_BCD = 0x0600
FTDI_INTERFACE = Interface(USB_CLASS_VENDOR, 0xFF, 0xFF, ((0x81, 2, 64), (0x02, 2, 64)))
STORAGE = Interface(
    USB_CLASS_MASS_STORAGE, 0x06, 0x50,
    endpoints=((0x81, 2, 512), (0x02, 2, 512)), driver="usb-storage",
)  # fmt: skip


class Device(SimDevice):
    spec = SPEC

    @dataclass
    class Faults:
        # every FTDI control transfer fails with EIO
        ftdi_error: bool = False
        # time until the reader reports the medium after switching to host
        medium_delay: float = 0.3

    def __init__(
        self,
        card=DEFAULT_CARD,
        manufacturer: str = "Badgerd Technologies",
        serial: str | None = None,
        **faults,
    ) -> None:
        super().__init__(card, **faults)
        self._manufacturer = manufacturer
        self._serial = serial
        # CBUS values written through SET_BITMODE, in order
        self.cbus_writes: list[int] = []
        self.host = True

    def build(self, testbed: Testbed, parent: str, port: str) -> None:
        self.testbed = testbed
        self._serial = self._serial or f"bdgrd_sdwirec_{port}"
        hub = SimUsbDevice(
            testbed, parent, port, 0x0424, 0x2640,
            device_class=USB_CLASS_HUB, interfaces=(HUB_INTERFACE,),
        )  # fmt: skip
        hub.create()
        reader = SimUsbDevice(
            testbed, hub.syspath, f"{port}.1", 0x0424, 0x4050, interfaces=(STORAGE,),
            manufacturer="Generic", product="Ultra Fast Media Reader",
            serial="000000264001",
        )  # fmt: skip
        reader.create()
        self.disk = SimBlockDevice(testbed, reader.interface_syspath(0), self.card)
        self.disk.attach()
        _Ftdi(self, testbed, hub.syspath, f"{port}.2").create()

    @property
    def serial(self) -> str:
        return self._serial or ""

    @property
    def manufacturer(self) -> str:
        return self._manufacturer

    @property
    def product(self) -> str:
        return PRODUCT

    def card_side(self) -> CardSide:
        return "host" if self.host else "target"

    def block_dev(self) -> str | None:
        return self.disk.path if self.disk.usable else None

    def set_cbus(self, value: int) -> None:
        self.cbus_writes.append(value)
        self.host = bool(value & 1)
        if self.host:
            self.testbed.later(self.faults.medium_delay, self._medium_detected)
        else:
            self.disk.set_medium(False)

    def _medium_detected(self) -> None:
        if self.host:
            self.disk.set_medium(True)


class _Ftdi(SimUsbDevice):
    def __init__(
        self, sdwire: Device, testbed: Testbed, parent: str, port: str
    ) -> None:
        super().__init__(
            testbed, parent, port, SPEC.vid, SPEC.pid, bcd_device=FT232R_BCD,
            interfaces=(FTDI_INTERFACE,), manufacturer=sdwire.manufacturer,
            product=PRODUCT, serial=sdwire.serial,
        )  # fmt: skip
        self.sdwire = sdwire

    def on_control_transfer(self, setup: Setup, data: bytes) -> bytes:
        if self.sdwire.faults.ftdi_error:
            raise OSError(errno.EIO, "simulated FTDI failure")
        mode, value = setup.value >> 8, setup.value & 0xFF
        if setup.request == SIO_SET_BITMODE and mode == BITMODE_CBUS:
            self.sdwire.set_cbus(value)
        # other requests (reset, purge, latency, ...) only need to succeed
        return bytes(setup.length)
