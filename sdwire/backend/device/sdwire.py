import logging
from serial import Serial
from .usb_device import USBDevice, PortInfo

log = logging.getLogger(__name__)

SDWIRE_GENERATION_SDWIRE3 = 2


class SDWire(USBDevice):

    def __init__(self, port_info: PortInfo, generation: int):
        super().__init__(port_info)
        self.generation = generation

    def switch_ts(self):
        try:
            self.usb_device.attach_kernel_driver(0)
            self.usb_device.reset()
        except Exception as e:
            log.debug(
                "not able to switch to ts mode. Device might be already in ts mode, err: %s",
                e,
            )

    def switch_dut(self):
        try:
            self.usb_device.detach_kernel_driver(0)
            self.usb_device.reset()
        except Exception as e:
            log.debug(
                "not able to switch to dut mode. Device might be already in dut mode, err: %s",
                e,
            )

    def __str__(self):
        return f"{self.serial_string}\t[{int(self.manufacturer_string):04x}::{int(self.product_string):04x}]"

    def __repr__(self):
        return self.__str__()
