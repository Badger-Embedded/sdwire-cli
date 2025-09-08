import logging
from typing import Optional
from pyftdi.ftdi import Ftdi
import usb.core
from sdwire.backend.device.usb_device import USBDevice, PortInfo
from sdwire.backend.block_device_utils import (
    map_usb_device_to_block_device,
    find_sibling_storage_device,
)

log = logging.getLogger(__name__)


class SDWireC(USBDevice):
    __block_dev = None

    def __init__(self, port_info: PortInfo):
        super().__init__(port_info)
        self._update_block_device()

    def _update_block_device(self) -> None:
        """Update block device detection for SDWireC."""
        if not self.usb_device:
            self.__block_dev = None
            return

        try:
            storage_device = self.storage_device
            if storage_device is not None:
                self.__block_dev = map_usb_device_to_block_device(storage_device)
                log.debug(f"SDWireC: Found block device: {self.__block_dev}")
            else:
                self.__block_dev = None
        except Exception as e:
            log.debug(f"SDWireC: Block device detection failed: {e}")
            self.__block_dev = None

    def __str__(self) -> str:
        block_dev_str = self.block_dev if self.block_dev is not None else "None"
        return f"{self.serial_string:<30}[{self.product_string}::{self.manufacturer_string}]\t\t{block_dev_str}"

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def block_dev(self) -> Optional[str]:
        return self.__block_dev

    @property
    def storage_device(self) -> Optional[usb.core.Device]:
        """Return the USB device that corresponds to the storage interface.

        For SDWireC, this is a sibling mass storage device under the same hub,
        not the FTDI device we control.

        Returns:
            USB device object for the sibling mass storage device, or None if
            not found
        """
        return find_sibling_storage_device(self.usb_device)

    def switch_ts(self) -> None:
        self._set_sdwire(1)

    def switch_dut(self) -> None:
        self._set_sdwire(0)

    def _set_sdwire(self, target: int) -> None:
        if not self.usb_device:
            log.error("USB device not available")
            import sys

            print("USB device not available")
            sys.exit(1)

        try:
            ftdi = Ftdi()
            ftdi.open_from_device(self.usb_device)
            log.info(f"Set CBUS to 0x{0xF0 | target:02X}")
            ftdi.set_bitmode(0xF0 | target, Ftdi.BitMode.CBUS)
            ftdi.close()
        except Exception as e:
            import sys

            log.debug("error while updating ftdi device: %s", e, exc_info=True)
            print("couldnt switch sdwire device")
            sys.exit(1)
