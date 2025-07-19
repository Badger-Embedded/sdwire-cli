import logging
from typing import Optional
import usb.core
from sdwire.backend.device.usb_device import USBDevice, PortInfo
from sdwire.backend.block_device_utils import map_usb_device_to_block_device

log = logging.getLogger(__name__)

SDWIRE_GENERATION_SDWIRE3 = 2


class SDWire(USBDevice):
    __block_dev = None

    def __init__(self, port_info: PortInfo, generation: int):
        super().__init__(port_info)
        self.generation = generation
        self._update_block_device()

    def switch_ts(self) -> None:
        if not self.usb_device:
            log.error("USB device not available")
            return

        try:
            self.usb_device.attach_kernel_driver(0)
            self.usb_device.reset()
        except Exception as e:
            log.debug(
                "not able to switch to ts mode. Device might be already in ts mode, err: %s",
                e,
            )

    def switch_dut(self) -> None:
        if not self.usb_device:
            log.error("USB device not available")
            return

        try:
            self.usb_device.detach_kernel_driver(0)
            self.usb_device.reset()
        except Exception as e:
            log.debug(
                "not able to switch to dut mode. Device might be already in dut mode, err: %s",
                e,
            )

    def _update_block_device(self) -> None:
        """Update block device detection based on current device state."""
        if not self.usb_device:
            self.__block_dev = None
            return

        try:
            storage_device = self.storage_device
            if storage_device is not None:
                self.__block_dev = map_usb_device_to_block_device(storage_device)
                log.debug(f"SDWire3: Found block device: {self.__block_dev}")
            else:
                self.__block_dev = None
        except Exception as e:
            log.debug(f"SDWire3: Block device detection failed: {e}")
            self.__block_dev = None

    @property
    def block_dev(self) -> Optional[str]:
        return self.__block_dev

    @property
    def storage_device(self) -> Optional[usb.core.Device]:
        """Return the USB device that corresponds to the storage interface.

        For SDWire3, this is the same device we control (direct media controller).

        Returns:
            usb.core.Device: The USB device for storage, or None if not available
        """
        return self.usb_device

    def __str__(self) -> str:
        block_dev_str = self.block_dev if self.block_dev is not None else "None"
        return f"{self.serial_string}\t[{int(self.manufacturer_string):04x}::{int(self.product_string):04x}]\t\t{block_dev_str}"

    def __repr__(self) -> str:
        return self.__str__()
