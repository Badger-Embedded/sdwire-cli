from serial.tools.list_ports_common import ListPortInfo
from device.usb_device import USBDevice


class SDWire(USBDevice):

    def __init__(self, port_info: ListPortInfo):
        super().__init__(port_info)

    @property
    def badgerd_serial_string(self) -> str:
        return "sdwire_gen2_101"
