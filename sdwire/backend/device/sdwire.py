import logging

import usb.core
import usb.util

from sdwire.backend.block_device_utils import map_usb_device_to_block_device
from sdwire.backend.device.power import PowerManagementError, UsbPower
from sdwire.backend.device.usb_device import PortInfo, USBDevice

log = logging.getLogger(__name__)

SDWIRE_GENERATION_SDWIRE3 = 2


class SDWire(USBDevice):
    __block_dev = None

    def __init__(self, port_info: PortInfo, generation: int):
        super().__init__(port_info)
        self.generation = generation
        self._update_block_device()

    @property
    def power(self) -> UsbPower:
        return UsbPower(
            getattr(self.usb_device, "bus", None),
            getattr(self.usb_device, "port_numbers", None),
        )

    def query_device_state(self):
        """Return True when in host mode, False when in target mode."""
        if not self.usb_device:
            raise RuntimeError("USB device not available")

        try:
            host_attached = bool(self.usb_device.is_kernel_driver_active(0))
        except NotImplementedError as e:
            raise RuntimeError("state query is not supported on this platform") from e
        power = self.power
        if (
            not host_attached
            and power.available
            and power.runtime_status != "suspended"
        ):
            log.warning(
                "driver is detached but the device is not runtime-suspended "
                "(power/control=%s, runtime_status=%s); the card is not switched to target",
                power.control,
                power.runtime_status,
            )
        return host_attached

    def _release_usb_handle(self) -> None:
        # an open usb handle keeps the device awake and prevents runtime suspend
        usb.util.dispose_resources(self.usb_device)

    def switch_ts(self) -> None:
        if not self.usb_device:
            raise RuntimeError("USB device not available")

        try:
            if self.usb_device.is_kernel_driver_active(0):
                log.debug("already in ts mode")
                return
            self.usb_device.attach_kernel_driver(0)
            self.usb_device.reset()
        except (usb.core.USBError, NotImplementedError) as e:
            if self.power.available:
                raise
            # platforms without sysfs (e.g. macOS) can't verify the switch,
            # keep the previous non-fatal behaviour
            log.warning("not able to switch to ts mode: %s", e)
        self._release_usb_handle()

    def switch_dut(self) -> None:
        if not self.usb_device:
            raise RuntimeError("USB device not available")

        power = self.power
        if power.available:
            power.enable_autosuspend()
        else:
            log.debug("sysfs power control not found, cannot verify the switch")

        try:
            if self.usb_device.is_kernel_driver_active(0):
                self.usb_device.detach_kernel_driver(0)
                self.usb_device.reset()
        except (usb.core.USBError, NotImplementedError) as e:
            if power.available:
                raise
            log.warning("not able to switch to dut mode: %s", e)
        self._release_usb_handle()

        if power.available and not power.wait_for_status("suspended"):
            raise PowerManagementError(
                f"device did not runtime-suspend (power/control={power.control}, "
                f"runtime_status={power.runtime_status}) at {power.path}; "
                "the SD card is not connected to the target"
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
    def block_dev(self) -> str | None:
        return self.__block_dev

    @property
    def storage_device(self) -> usb.core.Device | None:
        """Return the USB device that corresponds to the storage interface.

        For SDWire3, this is the same device we control (direct media controller).

        Returns:
            usb.core.Device: The USB device for storage, or None if not available
        """
        return self.usb_device

    def __str__(self) -> str:
        block_dev_str = self.block_dev if self.block_dev is not None else "None"
        return f"{self.serial_string:<30}[{int(self.manufacturer_string):04x}::{int(self.product_string):04x}]\t\t{block_dev_str}"

    def __repr__(self) -> str:
        return self.__str__()
