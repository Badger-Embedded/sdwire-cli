from typing import List
from adafruit_board_toolkit import circuitpython_serial as cpserial
from serial.tools.list_ports_common import ListPortInfo

import constants
from device.sdwire import SDWire


def get_sdwire_devices() -> List[SDWire]:
    ports = cpserial.data_comports()
    # Badgerd SDWire Gen2
    # VID = 0x1209 PID = 0x2404

    print(ports)
    result = []
    for p in ports:
        if p.vid == constants.SDWIRE_GEN2_VID and p.pid == constants.SDWIRE_GEN2_PID:
            result.append(SDWire(p))
    return result
