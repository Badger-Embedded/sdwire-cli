import logging
from sdwire.backend.device.usb_device import PortInfo
from sdwire.backend.device.sdwire import SDWire

log = logging.getLogger(__name__)


class SDWire3Pro(SDWire):

    def __init__(self, port_info: PortInfo):
        super().__init__(port_info, 2)
