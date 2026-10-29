"""The template device on real hardware."""

from e2e.framework.device import CardSide, HwDevice
from e2e.framework.hw import oracle

from .spec import SPEC


def discover() -> list[HwDevice]:
    return [Device(path) for path in oracle.usb_devices(SPEC.vid, SPEC.pid)]


class Device(HwDevice):
    spec = SPEC

    @property
    def serial(self) -> str:
        return self.attr("serial") or ""

    def card_side(self) -> CardSide:
        # read from sysfs, never from the CLI under test
        raise NotImplementedError

    def block_dev(self) -> str | None:
        return oracle.usable_block_dev(self.syspath)
