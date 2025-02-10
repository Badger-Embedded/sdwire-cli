import logging
from typing import List
from adafruit_board_toolkit import circuitpython_serial as cpserial
from serial.tools.list_ports_common import ListPortInfo

from sdwire import constants
from .device.sdwire import SDWire
from .device.sdwirec import SDWireC
from .device.usb_device import PortInfo

import usb.core
import usb.util
from usb.core import Device

log = logging.getLogger(__name__)


def get_sdwirec_devices() -> List[SDWireC]:
    devices: List[Device] = usb.core.find(find_all=True)
    if not devices:
        log.info("no usb devices found while searching for SDWireC..")
        return []

    device_list = []
    for device in devices:
        product = None
        serial = None
        manufacturer = None
        try:
            product = device.product
            serial = device.serial_number
            manufacturer = device.manufacturer
        except Exception as e:
            log.debug(
                "not able to get usb product, serial_number and manufacturer information, err: %s",
                e,
            )

        # filter with product string to allow non Badger'd sdwire devices to be detected
        if product == constants.SDWIREC_PRODUCT_STRING:
            device_list.append(
                SDWireC(port_info=PortInfo(None, product, manufacturer, serial, device))
            )

    return device_list


def get_sdwire_devices() -> List[SDWire]:
    ports = cpserial.data_comports()

    # Badgerd SDWire Gen2
    # VID = 0x1209 PID = 0x2404
    # Badgerd SDWireC
    # VID = 0x04e8 PID = 0x6001
    result = []
    for p in ports:
        asdf
        if p.vid == constants.SDWIRE3_VID and p.pid == constants.SDWIRE3_PID:
            result.append(
                SDWire(
                    port_info=PortInfo(
                        p.device, p.product, p.manufacturer, p.serial_number, p
                    )
                )
            )
    # Search for legacy SDWireC devices
    legacy_devices = get_sdwirec_devices()

    return result + legacy_devices
