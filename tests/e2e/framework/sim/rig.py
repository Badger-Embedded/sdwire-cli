"""Rig backed by a fresh umockdev testbed per test."""

import itertools

from e2e.framework import registry
from e2e.framework.device import SimDevice
from e2e.framework.rig import Rig
from e2e.framework.sim.block import SimBlockDevice
from e2e.framework.sim.sdcard import SimSdCard
from e2e.framework.sim.testbed import HOST_CONTROLLER, Testbed
from e2e.framework.sim.usb import (
    HUB_INTERFACE,
    USB_CLASS_HUB,
    USB_CLASS_MASS_STORAGE,
    Interface,
    SimUsbDevice,
)


class SimRig(Rig):
    backend = "sim"

    def __init__(self) -> None:
        super().__init__()
        self.testbed = Testbed()
        root_hub = SimUsbDevice(
            self.testbed, HOST_CONTROLLER, "", 0x1D6B, 0x0002,
            device_class=USB_CLASS_HUB, interfaces=(HUB_INTERFACE,),
        )  # fmt: skip
        root_hub.create()
        self.root_hub = root_hub.syspath
        self._ports = itertools.count(1)

    @property
    def env(self) -> dict[str, str]:
        return self.testbed.env

    def add(self, kind: str, **options) -> SimDevice:
        device = registry.backend_module(kind, "sim").Device(**options)
        device.build(self.testbed, self.root_hub, str(next(self._ports)))
        self.devices.append(device)
        return device

    def add_unrelated(self) -> None:
        port = str(next(self._ports))
        hub = SimUsbDevice(
            self.testbed, self.root_hub, port, 0x05E3, 0x0610,
            device_class=USB_CLASS_HUB, interfaces=(HUB_INTERFACE,),
            manufacturer="GenesysLogic", product="USB2.1 Hub",
        )  # fmt: skip
        hub.create()
        storage = Interface(
            USB_CLASS_MASS_STORAGE, 0x06, 0x50,
            endpoints=((0x81, 2, 512), (0x02, 2, 512)), driver="usb-storage",
        )  # fmt: skip
        stick = SimUsbDevice(
            self.testbed, hub.syspath, f"{port}.1", 0x0781, 0x5567,
            interfaces=(storage,), manufacturer="SanDisk", product="Cruzer Blade",
            serial="4C530001230101115284",
        )  # fmt: skip
        stick.create()
        SimBlockDevice(self.testbed, stick.interface_syspath(0), SimSdCard()).attach()

    def require_exact(self) -> None:
        pass

    def close(self) -> None:
        self.testbed.close()
        assert not self.testbed.errors, "simulation errors:\n" + "\n".join(
            self.testbed.errors
        )
