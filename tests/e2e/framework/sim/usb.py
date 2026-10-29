"""Simulated USB device: sysfs attributes, descriptors and usbdevfs ioctls.

`SimUsbDevice` builds its sysfs entry from plain fields and translates the
usbdevfs ioctls that libusb issues into `on_*` hooks. Subclasses override the
hooks to model a device. Struct layouts assume a 64-bit host.
"""

import errno
import os
import struct
import traceback
from dataclasses import dataclass

from gi.repository import UMockdev

from e2e.framework.sim.testbed import BUS, Testbed

USB_CLASS_MASS_STORAGE = 0x08
USB_CLASS_HUB = 0x09
USB_CLASS_VENDOR = 0xFF


def _ioc(direction: int, nr: int, size: int = 0) -> int:
    return (direction << 30) | (size << 16) | (ord("U") << 8) | nr


_W, _R, _RW = 1, 2, 3
USBDEVFS_SETINTERFACE = _ioc(_R, 4, 8)
USBDEVFS_SETCONFIGURATION = _ioc(_R, 5, 4)
USBDEVFS_GETDRIVER = _ioc(_W, 8, 260)
USBDEVFS_SUBMITURB = _ioc(_R, 10, 56)
USBDEVFS_DISCARDURB = _ioc(0, 11)
USBDEVFS_REAPURB = _ioc(_W, 12, 8)
USBDEVFS_REAPURBNDELAY = _ioc(_W, 13, 8)
USBDEVFS_CLAIMINTERFACE = _ioc(_R, 15, 4)
USBDEVFS_RELEASEINTERFACE = _ioc(_R, 16, 4)
USBDEVFS_IOCTL = _ioc(_RW, 18, 16)
USBDEVFS_RESET = _ioc(0, 20)
USBDEVFS_DISCONNECT = _ioc(0, 22)
USBDEVFS_CONNECT = _ioc(0, 23)
USBDEVFS_URB_TYPE_CONTROL = 2


@dataclass(frozen=True)
class Interface:
    cls: int
    subclass: int = 0
    protocol: int = 0
    # (bEndpointAddress, bmAttributes, wMaxPacketSize)
    endpoints: tuple[tuple[int, int, int], ...] = ()
    # kernel driver bound at plug-in
    driver: str | None = None


HUB_INTERFACE = Interface(USB_CLASS_HUB, endpoints=((0x81, 3, 4),), driver="hub")


@dataclass(frozen=True)
class Setup:
    """USB control transfer setup packet."""

    request_type: int
    request: int
    value: int
    index: int
    length: int

    @property
    def is_in(self) -> bool:
        return bool(self.request_type & 0x80)


class SimUsbDevice:
    def __init__(
        self,
        testbed: Testbed,
        parent: str,
        port: str,
        vid: int,
        pid: int,
        *,
        bcd_device: int = 0x0100,
        device_class: int = 0,
        interfaces: tuple[Interface, ...] = (),
        manufacturer: str | None = None,
        product: str | None = None,
        serial: str | None = None,
    ) -> None:
        self.testbed = testbed
        self.port = port
        self.vid, self.pid = vid, pid
        self.bcd_device = bcd_device
        self.device_class = device_class
        self.interfaces = interfaces
        self.strings = {
            "manufacturer": manufacturer,
            "product": product,
            "serial": serial,
        }
        self.devnum = testbed.next_devnum()
        self.sysname = f"{BUS}-{port}" if port else f"usb{BUS}"
        self.syspath = f"{parent}/{self.sysname}"
        self.devnode = f"/dev/bus/usb/{BUS:03d}/{self.devnum:03d}"

    # ---- building -------------------------------------------------------

    def create(self) -> None:
        self.testbed.add(self._record())
        for number, interface in enumerate(self.interfaces):
            if interface.driver:
                self.bind_driver(number, interface.driver)
        handler = UMockdev.IoctlBase()
        dispatcher = _Usbdevfs(self)
        handler.connect("handle-ioctl", dispatcher.handle)
        self.testbed.attach_ioctl(self.devnode, handler)

    def interface_syspath(self, number: int) -> str:
        return f"{self.syspath}/{self.sysname}:1.{number}"

    def descriptors(self) -> bytes:
        device = struct.pack(
            "<BBHBBBBHHHBBBB", 18, 1, 0x0200, self.device_class, 0, 0, 64,
            self.vid, self.pid, self.bcd_device,
            *(i + 1 if self.strings[k] else 0
              for i, k in enumerate(("manufacturer", "product", "serial"))),
            1,
        )  # fmt: skip
        body = b""
        for number, intf in enumerate(self.interfaces):
            body += struct.pack(
                "<BBBBBBBBB", 9, 4, number, 0, len(intf.endpoints),
                intf.cls, intf.subclass, intf.protocol, 0,
            )  # fmt: skip
            for address, attributes, size in intf.endpoints:
                body += struct.pack("<BBBBHB", 7, 5, address, attributes, size, 0)
        config = struct.pack(
            "<BBHBBBBB", 9, 2, 9 + len(body), len(self.interfaces), 1, 0, 0x80, 50
        )
        return device + config + body

    def _record(self) -> str:
        attrs = {
            "busnum": BUS,
            "devnum": self.devnum,
            "devpath": self.port or "0",
            "idVendor": f"{self.vid:04x}",
            "idProduct": f"{self.pid:04x}",
            "bcdDevice": f"{self.bcd_device:04x}",
            "bDeviceClass": f"{self.device_class:02x}",
            "bConfigurationValue": 1,
            "bNumInterfaces": f"{len(self.interfaces):2d}",
            "speed": 480,
            "dev": f"189:{(BUS - 1) * 128 + self.devnum - 1}",
            "power/control": "on",
            "power/runtime_status": "active",
            "power/autosuspend_delay_ms": 2000,
            **{k: v for k, v in self.strings.items() if v is not None},
        }
        lines = [
            f"P: {self.syspath.removeprefix('/sys')}",
            f"N: {self.devnode.removeprefix('/dev/')}",
            "E: SUBSYSTEM=usb",
            "E: DEVTYPE=usb_device",
            f"E: DEVNAME={self.devnode}",
            f"E: BUSNUM={BUS:03d}",
            f"E: DEVNUM={self.devnum:03d}",
            *(f"A: {k}={v}\\n" for k, v in attrs.items()),
            f"H: descriptors={self.descriptors().hex()}",
            "",
        ]
        for number, intf in enumerate(self.interfaces):
            lines += [
                f"P: {self.interface_syspath(number).removeprefix('/sys')}",
                "E: SUBSYSTEM=usb",
                "E: DEVTYPE=usb_interface",
                f"A: bInterfaceNumber={number:02x}\\n",
                f"A: bInterfaceClass={intf.cls:02x}\\n",
                f"A: bInterfaceSubClass={intf.subclass:02x}\\n",
                f"A: bInterfaceProtocol={intf.protocol:02x}\\n",
                f"A: bNumEndpoints={len(intf.endpoints):02x}\\n",
                "",
            ]
        return "\n".join(lines) + "\n"

    # ---- sysfs helpers --------------------------------------------------

    def attr(self, name: str) -> str:
        return self.testbed.read(f"{self.syspath}/{name}")

    def set_attr(self, name: str, value: str) -> None:
        self.testbed.write(f"{self.syspath}/{name}", value)

    def driver(self, interface: int) -> str | None:
        link = self.testbed.real(f"{self.interface_syspath(interface)}/driver")
        try:
            return os.path.basename(os.readlink(link))
        except OSError:
            return None

    def bind_driver(self, interface: int, name: str) -> None:
        intf = self.interface_syspath(interface)
        target = os.path.relpath(self.testbed.ensure_driver(name), intf)
        os.symlink(target, self.testbed.real(f"{intf}/driver"))

    def unbind_driver(self, interface: int) -> None:
        os.unlink(self.testbed.real(f"{self.interface_syspath(interface)}/driver"))

    # ---- hooks, override to model the device ----------------------------

    def on_driver_detach(self, interface: int) -> None:
        self.unbind_driver(interface)

    def on_driver_attach(self, interface: int) -> bool:
        """Bind the interface's driver, return whether one was bound."""
        name = self.interfaces[interface].driver
        if name:
            self.bind_driver(interface, name)
        return name is not None

    def on_reset(self) -> None:
        pass

    def on_control_transfer(self, setup: Setup, data: bytes) -> bytes:
        """Handle a control transfer, return the IN data. Raise OSError to fail it."""
        raise OSError(errno.EPIPE, "control request not supported")


class _Usbdevfs:
    """Translates usbdevfs ioctls on the device node into SimUsbDevice hooks."""

    def __init__(self, device: SimUsbDevice) -> None:
        self.device = device
        self.completed_urbs: list = []

    def handle(self, _handler, client) -> bool:
        testbed = self.device.testbed
        with testbed.lock:
            try:
                client.complete(
                    self._dispatch(client.get_request(), client.get_arg()), 0
                )
            except OSError as e:
                client.complete(-1, e.errno)
            except Exception:
                testbed.errors.append(traceback.format_exc())
                client.complete(-1, errno.EIO)
        return True

    def _dispatch(self, request: int, arg) -> int:
        dev = self.device
        if request in (
            USBDEVFS_SETCONFIGURATION,
            USBDEVFS_SETINTERFACE,
            USBDEVFS_CLAIMINTERFACE,
            USBDEVFS_RELEASEINTERFACE,
        ):
            return 0
        if request == USBDEVFS_GETDRIVER:
            data = arg.resolve(0, 260)
            (interface,) = struct.unpack_from("<I", bytes(data.retrieve()))
            name = dev.driver(interface)
            if name is None:
                raise OSError(errno.ENODATA, "no driver")
            data.update(4, name.encode() + b"\0")
            return 0
        if request == USBDEVFS_IOCTL:
            interface, code = struct.unpack_from(
                "<ii", bytes(arg.resolve(0, 16).retrieve())
            )
            if code == USBDEVFS_DISCONNECT:
                if dev.driver(interface) is None:
                    raise OSError(errno.ENODATA, "no driver")
                dev.on_driver_detach(interface)
                return 0
            if code == USBDEVFS_CONNECT:
                if dev.driver(interface) is not None:
                    raise OSError(errno.EBUSY, "driver already bound")
                # the kernel returns 1 when a driver got bound
                return int(dev.on_driver_attach(interface))
            raise OSError(errno.ENOTTY, "unsupported usbdevfs ioctl")
        if request == USBDEVFS_RESET:
            dev.on_reset()
            return 0
        if request == USBDEVFS_SUBMITURB:
            return self._submit_urb(arg)
        if request in (USBDEVFS_REAPURB, USBDEVFS_REAPURBNDELAY):
            if not self.completed_urbs:
                raise OSError(errno.EAGAIN, "no completed urb")
            arg.resolve(0, 8).set_ptr(0, self.completed_urbs.pop(0))
            return 0
        if request == USBDEVFS_DISCARDURB:
            # URBs complete at submission, so there is nothing left to cancel
            raise OSError(errno.EINVAL, "urb not pending")
        raise OSError(errno.ENOTTY, "unsupported ioctl")

    def _submit_urb(self, arg) -> int:
        urb = arg.resolve(0, 56)
        urb_type, _, _, _, _, length = struct.unpack_from(
            "<BBxxiIxxxxQi", bytes(urb.retrieve())
        )
        if urb_type != USBDEVFS_URB_TYPE_CONTROL:
            raise OSError(errno.EINVAL, "only control transfers are simulated")
        buffer = urb.resolve(16, length)
        raw = bytes(buffer.retrieve())
        setup = Setup(*struct.unpack_from("<BBHHH", raw))
        result = self.device.on_control_transfer(setup, raw[8 : 8 + setup.length])
        if setup.is_in:
            result = result[: setup.length]
            buffer.update(8, result)
            actual = len(result)
        else:
            actual = setup.length
        urb.update(4, struct.pack("<i", 0))  # status
        urb.update(28, struct.pack("<i", actual))  # actual_length
        self.completed_urbs.append(urb)
        return 0
