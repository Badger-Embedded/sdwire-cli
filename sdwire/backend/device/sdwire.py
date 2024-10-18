from serial import Serial
from .usb_device import USBDevice, PortInfo


class SDWire(USBDevice):

    def __init__(self, port_info: PortInfo):
        super().__init__(port_info)

    @property
    def serial_string(self) -> str:
        return "sdwire_gen2_101"

    def invoke(self, command: str) -> None:
        with Serial(self.dev_string) as channel:
            channel.timeout = 0.05
            data = command.encode() + b"\n"
            print(f"data={data}")
            channel.write(data)

    def __str__(self):
        return f"{self.serial_string}\t\t[{self.product_string}::{self.manufacturer_string}]"

    def __repr__(self):
        return self.__str__()
