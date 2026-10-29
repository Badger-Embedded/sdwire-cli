"""SDWire3 on real hardware."""

from .spec import SPEC
from e2e.framework.device import CardSide, HwDevice
from e2e.framework.hw import oracle


def discover() -> list[HwDevice]:
    return [Device(path) for path in oracle.usb_devices(SPEC.vid, SPEC.pid)]


class Device(HwDevice):
    spec = SPEC

    @property
    def serial(self) -> str:
        return f"{self.attr('serial')}.{oracle.port_path(self.syspath)}"

    def power(self, name: str) -> str | None:
        return self.attr(f"power/{name}")

    def card_side(self) -> CardSide:
        return "target" if self.power("runtime_status") == "suspended" else "host"

    def block_dev(self) -> str | None:
        return oracle.usable_block_dev(self.syspath)
