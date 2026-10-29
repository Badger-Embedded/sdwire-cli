"""SDWire3 model.

Host: usb-storage is bound to interface 0 and the block device exists.
Target: the driver is detached and the device is runtime-suspended, which
only happens with power/control=auto. (The kernel also waits for usbfs
handles to close; umockdev does not report closes, so that is not modelled.)
Attaching the driver and resetting brings the block device back after
`reenumerate_delay`.
"""

import os
from dataclasses import dataclass

from .spec import SPEC
from e2e.framework.device import CardSide, SimDevice
from e2e.framework.sim.block import SimBlockDevice
from e2e.framework.sim.testbed import Testbed
from e2e.framework.sim.usb import USB_CLASS_MASS_STORAGE, Interface, SimUsbDevice

# every RTS5306E reports the same serial, the CLI appends the port path
USB_SERIAL = "20120501030900000"
MANUFACTURER = "Generic"
PRODUCT = "USB3.0-CRW"
STORAGE = Interface(
    USB_CLASS_MASS_STORAGE, 0x06, 0x50,
    endpoints=((0x81, 2, 512), (0x02, 2, 512)), driver="usb-storage",
)  # fmt: skip


class Device(SimDevice):
    spec = SPEC

    @dataclass
    class Faults:
        # the device never runtime-suspends, e.g. something keeps it awake
        never_suspends: bool = False
        # power/* is not writable for the user (udev rule not installed)
        deny_power_write: bool = False
        # time until the block device is back after switching to host
        reenumerate_delay: float = 0.3

    def build(self, testbed: Testbed, parent: str, port: str) -> None:
        self.port = port
        self.usb = _CardReader(self, testbed, parent, port)
        self.usb.create()
        self.disk = SimBlockDevice(testbed, self.usb.interface_syspath(0), self.card)
        self.disk.attach()
        if self.faults.deny_power_write:
            for name in ("control", "autosuspend_delay_ms"):
                os.chmod(testbed.real(f"{self.usb.syspath}/power/{name}"), 0o444)

    @property
    def serial(self) -> str:
        return f"{USB_SERIAL}.{self.port}"

    @property
    def manufacturer(self) -> str:
        return MANUFACTURER

    @property
    def product(self) -> str:
        return PRODUCT

    def power(self, name: str) -> str:
        return self.usb.attr(f"power/{name}")

    def card_side(self) -> CardSide:
        return "target" if self.power("runtime_status") == "suspended" else "host"

    def block_dev(self) -> str | None:
        return self.disk.path if self.disk.usable else None


class _CardReader(SimUsbDevice):
    def __init__(
        self, sdwire: Device, testbed: Testbed, parent: str, port: str
    ) -> None:
        super().__init__(
            testbed, parent, port, SPEC.vid, SPEC.pid, interfaces=(STORAGE,),
            manufacturer=MANUFACTURER, product=PRODUCT, serial=USB_SERIAL,
        )  # fmt: skip
        self.sdwire = sdwire

    def on_driver_detach(self, interface: int) -> None:
        super().on_driver_detach(interface)
        self.sdwire.disk.detach()
        self._maybe_suspend()

    def on_driver_attach(self, interface: int) -> bool:
        self.set_attr("power/runtime_status", "active")
        return super().on_driver_attach(interface)

    def on_reset(self) -> None:
        disk = self.sdwire.disk
        if self.driver(0) and not disk.attached:
            self.testbed.later(self.sdwire.faults.reenumerate_delay, self._reenumerated)

    def _reenumerated(self) -> None:
        if self.driver(0) and not self.sdwire.disk.attached:
            self.sdwire.disk.attach()

    def _maybe_suspend(self) -> None:
        if (
            self.driver(0) is None
            and self.attr("power/control") == "auto"
            and not self.sdwire.faults.never_suspends
        ):
            self.set_attr("power/runtime_status", "suspended")
