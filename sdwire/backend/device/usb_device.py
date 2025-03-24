from collections import namedtuple
import pyudev
from serial.tools.list_ports_common import ListPortInfo

PortInfo = namedtuple(
    "PortInfo", ("device", "product", "manufacturer", "serial", "usb_device")
)


class USBDevice:
    __port_info = None
    _pyudev_context = None

    def __init__(self, port_info: PortInfo):
        self.__port_info = port_info
        self._pyudev_context = pyudev.Context()

    @property
    def usb_device(self):
        return self.__port_info.usb_device

    @property
    def dev_string(self) -> str:
        return self.__port_info.device

    @property
    def product_string(self) -> str:
        return self.__port_info.product

    @property
    def manufacturer_string(self) -> str:
        return self.__port_info.manufacturer

    @property
    def serial_string(self) -> str:
        return self.__port_info.serial
