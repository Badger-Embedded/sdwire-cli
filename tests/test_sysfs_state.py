import logging

import pytest

from sdwire.backend import detect
from sdwire.backend.device import sdwire as sdwire_mod
from sdwire.backend.device.power import UsbPower
from sdwire.backend.device.sdwire import SDWire
from sdwire.backend.device.usb_device import PortInfo
from sdwire.backend.device.usb_sysfs import UsbSysfs


class NoOpenUsb:
    """Fake usb device that fails the test if libusb would open it."""

    bus = 2
    port_numbers = (8,)

    def is_kernel_driver_active(self, _):
        raise AssertionError("libusb open would wake the device")

    @property
    def serial_number(self):
        raise AssertionError("libusb open would wake the device")

    manufacturer = product = serial_number


def make_usb_sysfs(tmp_path, bound=None, status="suspended", strings=None):
    dev = tmp_path / "2-8"
    (dev / "power").mkdir(parents=True)
    (dev / "power" / "runtime_status").write_text(status)
    (dev / "power" / "control").write_text("auto")
    for name, value in (strings or {}).items():
        (dev / name).write_text(value + "\n")
    if bound is not None:
        intf = dev / "2-8:1.0"
        intf.mkdir()
        if bound:
            (tmp_path / "usb-storage").mkdir()
            (intf / "driver").symlink_to(tmp_path / "usb-storage")
    return dev


def make_device(tmp_path, monkeypatch, usb):
    real_sysfs, real_power = UsbSysfs.for_device, UsbPower
    monkeypatch.setattr(
        sdwire_mod.UsbSysfs,
        "for_device",
        classmethod(lambda cls, d, root=None: real_sysfs(d, root=str(tmp_path))),
    )
    monkeypatch.setattr(
        sdwire_mod, "UsbPower", lambda b, p: real_power(b, p, root=str(tmp_path))
    )
    monkeypatch.setattr(sdwire_mod, "SUSPEND_SETTLE_TIMEOUT", 0)
    monkeypatch.setattr(SDWire, "_update_block_device", lambda self: None)
    return SDWire(PortInfo(None, 0x316, 0xBDA, "s", usb), generation=2)


@pytest.mark.parametrize("bound,expected", [(True, True), (False, False)])
def test_state_from_sysfs_without_libusb(tmp_path, monkeypatch, bound, expected):
    make_usb_sysfs(tmp_path, bound=bound)
    dev = make_device(tmp_path, monkeypatch, NoOpenUsb())
    assert dev.state() is expected


def test_state_falls_back_to_libusb_and_releases_handle(tmp_path, monkeypatch):
    class Usb:
        bus = 2
        port_numbers = (8,)

        def is_kernel_driver_active(self, _):
            return True

    usb = Usb()
    disposed = []
    monkeypatch.setattr(sdwire_mod.usb.util, "dispose_resources", disposed.append)
    dev = make_device(tmp_path, monkeypatch, usb)
    assert dev.state() is True
    assert disposed == [usb]


@pytest.mark.parametrize("status,warns", [("suspended", False), ("active", True)])
def test_target_state_warns_only_when_not_suspended(
    tmp_path, monkeypatch, caplog, status, warns
):
    make_usb_sysfs(tmp_path, bound=False, status=status)
    dev = make_device(tmp_path, monkeypatch, NoOpenUsb())
    with caplog.at_level(logging.WARNING):
        assert dev.state() is False
    assert ("not runtime-suspended" in caplog.text) is warns


def test_interface_driver_unknown_without_interface(tmp_path):
    make_usb_sysfs(tmp_path)
    assert UsbSysfs(2, [8], root=str(tmp_path)).interface_driver_bound(0) is None
    assert UsbSysfs(2, [9], root=str(tmp_path)).interface_driver_bound(0) is None


def test_read_usb_strings_from_sysfs(tmp_path, monkeypatch):
    make_usb_sysfs(
        tmp_path,
        strings={"manufacturer": "SRPOL", "product": "sd-wire", "serial": "x1"},
    )
    real = UsbSysfs.for_device
    monkeypatch.setattr(
        detect.UsbSysfs,
        "for_device",
        classmethod(lambda cls, d, root=None: real(d, root=str(tmp_path))),
    )
    assert detect.read_usb_strings(NoOpenUsb()) == ("SRPOL", "sd-wire", "x1")


def test_read_usb_strings_fallback_releases_handle(tmp_path, monkeypatch):
    class Usb:
        bus = None
        port_numbers = None
        manufacturer, product, serial_number = "m", "p", "s"

    usb = Usb()
    disposed = []
    monkeypatch.setattr(detect.usb.util, "dispose_resources", disposed.append)
    assert detect.read_usb_strings(usb) == ("m", "p", "s")
    assert disposed == [usb]
