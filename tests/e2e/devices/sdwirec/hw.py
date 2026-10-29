"""SDWireC on real hardware."""

import glob
import os

from .spec import PRODUCT, SPEC
from e2e.framework.device import CardSide, HwDevice
from e2e.framework.hw import oracle

USB_CLASS_MASS_STORAGE = "08"


def discover() -> list[HwDevice]:
    # the CLI matches on the product string only, so non-Badger ids are found too
    return [
        Device(path)
        for path in sorted(glob.glob(f"{oracle.SYSFS_USB_DEVICES}/*"))
        if ":" not in os.path.basename(path)
        and oracle.read(f"{path}/product") == PRODUCT
    ]


class Device(HwDevice):
    spec = SPEC

    @property
    def serial(self) -> str:
        return self.attr("serial") or ""

    def reader(self) -> str | None:
        """Sysfs path of the card reader on the same hub."""
        hub = os.path.dirname(os.path.realpath(self.syspath))
        for sibling in sorted(glob.glob(f"{hub}/*-*")):
            if ":" in os.path.basename(sibling) or sibling == os.path.realpath(
                self.syspath
            ):
                continue
            classes = {
                oracle.read(i) for i in glob.glob(f"{sibling}/*:*/bInterfaceClass")
            }
            if USB_CLASS_MASS_STORAGE in classes:
                return sibling
        return None

    def card_side(self) -> CardSide:
        # the CBUS state is not readable without claiming the FTDI chip, so
        # the reader reporting a medium is the independent signal
        return "host" if self.block_dev() else "target"

    def block_dev(self) -> str | None:
        reader = self.reader()
        return oracle.usable_block_dev(reader) if reader else None
