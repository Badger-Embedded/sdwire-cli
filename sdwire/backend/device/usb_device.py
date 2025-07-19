from collections import namedtuple
from typing import Optional
import usb.core


PortInfo = namedtuple(
    "PortInfo", ("device", "product", "manufacturer", "serial", "usb_device")
)


class USBDevice:
    __port_info: Optional[PortInfo] = None


    def __init__(self, port_info: PortInfo):
        self.__port_info = port_info


    @property
    def usb_device(self) -> Optional[usb.core.Device]:
        if self.__port_info:
            return self.__port_info.usb_device
        return None

    @property
    def dev_string(self) -> str:
        if self.__port_info and self.__port_info.device:
            return self.__port_info.device
        return ""

    @property
    def product_string(self) -> str:
        if self.__port_info and self.__port_info.product:
            return str(self.__port_info.product)
        return ""

    @property
    def manufacturer_string(self) -> str:
        if self.__port_info and self.__port_info.manufacturer:
            return str(self.__port_info.manufacturer)
        return ""

    @property
    def serial_string(self) -> str:
        if self.__port_info and self.__port_info.serial:
            return str(self.__port_info.serial)
        return ""
