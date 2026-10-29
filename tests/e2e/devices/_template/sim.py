"""Simulation model of the template device.

Describe here which states the device has and which USB operations move it
between them, so the model can be checked against the real hardware.
"""

from dataclasses import dataclass

from e2e.framework.device import CardSide, SimDevice
from e2e.framework.sim.block import SimBlockDevice
from e2e.framework.sim.testbed import Testbed
from e2e.framework.sim.usb import USB_CLASS_MASS_STORAGE, Interface, Setup, SimUsbDevice

from .spec import SPEC

STORAGE = Interface(
    USB_CLASS_MASS_STORAGE, 0x06, 0x50,
    endpoints=((0x81, 2, 512), (0x02, 2, 512)), driver="usb-storage",
)  # fmt: skip


class Device(SimDevice):
    spec = SPEC

    @dataclass
    class Faults:
        # knobs that tests pass as rig.add(kind, <knob>=...), with safe defaults
        switch_delay: float = 0.0

    def build(self, testbed: Testbed, parent: str, port: str) -> None:
        self.port = port
        self.host = True
        self.usb = _Controller(self, testbed, parent, port)
        self.usb.create()
        self.disk = SimBlockDevice(testbed, self.usb.interface_syspath(0), self.card)
        self.disk.attach()

    @property
    def serial(self) -> str:
        # exactly what `sdwire list` prints in the serial column
        return f"template-{self.port}"

    @property
    def manufacturer(self) -> str:
        return "Example"

    @property
    def product(self) -> str:
        return "Template"

    def card_side(self) -> CardSide:
        return "host" if self.host else "target"

    def block_dev(self) -> str | None:
        return self.disk.path if self.disk.usable else None


class _Controller(SimUsbDevice):
    def __init__(
        self, sdwire: Device, testbed: Testbed, parent: str, port: str
    ) -> None:
        super().__init__(
            testbed, parent, port, SPEC.vid, SPEC.pid, interfaces=(STORAGE,),
            manufacturer=sdwire.manufacturer, product=sdwire.product,
            serial=sdwire.serial,
        )  # fmt: skip
        self.sdwire = sdwire

    # Override only what the switching mechanism uses:
    #   on_driver_detach / on_driver_attach  libusb detach/attach_kernel_driver
    #   on_reset                             libusb reset_device
    #   on_control_transfer                  vendor requests (e.g. pyftdi)

    def on_control_transfer(self, setup: Setup, data: bytes) -> bytes:
        return super().on_control_transfer(setup, data)
