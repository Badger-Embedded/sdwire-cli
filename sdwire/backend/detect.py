"""SDWire device detection module.

This module provides functions to detect and enumerate SDWire devices
connected to the system via USB, including both SDWire3 and SDWireC variants.
"""

import logging
from typing import List, Union

from sdwire import constants
from sdwire.backend.device.sdwire import SDWire, SDWIRE_GENERATION_SDWIRE3
from sdwire.backend.device.sdwirec import SDWireC
from sdwire.backend.device.usb_device import PortInfo

import usb.core
import usb.util

log = logging.getLogger(__name__)


def get_sdwirec_devices() -> List[SDWireC]:
    """Detect and return all connected SDWireC devices.

    Returns:
        List of SDWireC device instances found on the system
    """
    try:
        found_devices = usb.core.find(find_all=True)
        devices = list(found_devices or [])
    except Exception as e:
        log.debug("Error finding USB devices: %s", e)
        return []

    if not devices:
        log.debug("No USB devices found while searching for SDWireC")
        return []

    device_list = []
    for device in devices:
        product = None
        serial = None
        manufacturer = None
        try:
            # Safe attribute access
            product = getattr(device, "product", None)
            serial = getattr(device, "serial_number", None)
            manufacturer = getattr(device, "manufacturer", None)
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


def get_sdwire_devices() -> List[Union[SDWire, SDWireC]]:
    """Detect and return all connected SDWire devices (both SDWire3 and SDWireC).

    This function searches for:
    - SDWire3 devices (VID: 0x0bda, PID: 0x0316)
    - SDWireC devices (VID: 0x04e8, PID: 0x6001)

    Returns:
        List of SDWire device instances (SDWire or SDWireC) found on the system
    """
    result: List[Union[SDWire, SDWireC]] = []
    try:
        found_devices = usb.core.find(
            find_all=True,
            idVendor=constants.SDWIRE3_VID,
            idProduct=constants.SDWIRE3_PID,
        )
        devices = list(found_devices or [])
    except Exception as e:
        log.debug("Error finding SDWire3 devices: %s", e)
        devices = []

    if not devices:
        log.info("no usb devices found while searching for SDWire..")
    else:
        for device in devices:
            product = None
            serial = None
            vendor = None
            bus = None
            address = None
            try:
                # Safe attribute access
                product = getattr(device, "idProduct", None)
                vendor = getattr(device, "idVendor", None)
                bus = getattr(device, "bus", None)
                address = getattr(device, "address", None)
                serial_num = getattr(device, "serial_number", None) or "unknown"
                serial = f"{serial_num}:{bus}.{address}"
            except Exception as e:
                log.debug(
                    "not able to get usb product, serial_number and manufacturer information, err: %s",
                    e,
                )

            if product == constants.SDWIRE3_PID and vendor == constants.SDWIRE3_VID:
                result.append(
                    SDWire(
                        port_info=PortInfo(device, product, vendor, serial, device),
                        generation=SDWIRE_GENERATION_SDWIRE3,
                    )
                )

    # Search for legacy SDWireC devices
    legacy_devices = get_sdwirec_devices()

    return result + legacy_devices
