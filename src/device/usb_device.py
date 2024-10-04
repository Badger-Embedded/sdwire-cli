from serial.tools.list_ports_common import ListPortInfo


class USBDevice:
    __port_info = None

    def __init__(self, port_info: ListPortInfo):
        self.__port_info = port_info

    @property
    def dev_string(self) -> str:
        return self.__port_info.device

    @property
    def product_string(self) -> str:
        return self.__port_info.product

    @property
    def manufacturer_string(self) -> str:
        return self.__port_info.manufacturer
