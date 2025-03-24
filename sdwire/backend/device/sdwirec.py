import logging
from pyftdi.ftdi import Ftdi
from serial import Serial
from .usb_device import USBDevice, PortInfo

log = logging.getLogger(__name__)


class SDWireC(USBDevice):
    __block_dev = None

    def __init__(self, port_info: PortInfo):
        super().__init__(port_info)
        for d in self._pyudev_context.list_devices(ID_MODEL="sd-wire"):
            d_serial = d.get("ID_USB_SERIAL_SHORT", None)
            if d_serial is not None and d_serial == self.serial_string:
                for sibling in d.parent.children:
                    if (
                        d.device_path != sibling.device_path
                        and sibling.device_type == "disk"
                    ):
                        self.__block_dev = f"/dev/{sibling.device_path.split("/")[-1]}"
                        break
                break

    def __str__(self):
        return f"{self.serial_string}\t[{self.product_string}::{self.manufacturer_string}]\t{self.block_dev}"

    def __repr__(self):
        return self.__str__()

    @property
    def block_dev(self):
        return self.__block_dev

    def switch_ts(self):
        self._set_sdwire(1)

    def switch_dut(self):
        self._set_sdwire(0)

    def _set_sdwire(self, target):
        try:
            ftdi = Ftdi()
            ftdi.open_from_device(self.usb_device)
            log.info(f"Set CBUS to 0x{0xF0 | target:02X}")
            ftdi.set_bitmode(0xF0 | target, Ftdi.BitMode.CBUS)
            ftdi.close()
        except Exception as e:
            import sys

            log.debug("error while updating ftdi device", exc_info=1)
            print("couldnt switch sdwire device")
            sys.exit(1)
