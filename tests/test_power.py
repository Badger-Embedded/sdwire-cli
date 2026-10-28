import pytest

from sdwire.backend.device import power as power_mod
from sdwire.backend.device.power import PowerManagementError, UsbPower
from sdwire.backend.device.sdwire import SDWire
from sdwire.backend.device.usb_device import PortInfo


def make_sysfs(tmp_path, control="on", status="active", delay="2000"):
    pdir = tmp_path / "2-8" / "power"
    pdir.mkdir(parents=True)
    (pdir / "control").write_text(control)
    (pdir / "runtime_status").write_text(status)
    (pdir / "autosuspend_delay_ms").write_text(delay)
    return pdir


def test_enable_autosuspend_writes_sysfs(tmp_path):
    pdir = make_sysfs(tmp_path)
    UsbPower(2, [8], root=str(tmp_path)).enable_autosuspend()
    assert (pdir / "control").read_text() == "auto"
    assert (pdir / "autosuspend_delay_ms").read_text() == "0"


def test_enable_autosuspend_missing_device(tmp_path):
    with pytest.raises(PowerManagementError):
        UsbPower(2, [8], root=str(tmp_path)).enable_autosuspend()


class FakeUsb:
    bus = 2
    port_numbers = (8,)

    def __init__(self, bound=True):
        self.bound = bound
        self.calls = []

    def is_kernel_driver_active(self, _):
        return self.bound

    def detach_kernel_driver(self, _):
        self.bound = False
        self.calls.append("detach")

    def attach_kernel_driver(self, _):
        self.bound = True
        self.calls.append("attach")

    def reset(self):
        self.calls.append("reset")


def make_device(tmp_path, monkeypatch, usb):
    real = power_mod.UsbPower
    monkeypatch.setattr(
        "sdwire.backend.device.sdwire.UsbPower",
        lambda bus, ports: real(bus, ports, root=str(tmp_path)),
    )
    disposed = []
    monkeypatch.setattr(
        "sdwire.backend.device.sdwire.usb.util.dispose_resources", disposed.append
    )
    monkeypatch.setattr(SDWire, "_update_block_device", lambda self: None)
    dev = SDWire(PortInfo(None, 0x316, 0xBDA, "s", usb), generation=2)
    return dev, disposed


def test_switch_dut_fails_when_not_suspended(tmp_path, monkeypatch):
    make_sysfs(tmp_path, status="active")
    monkeypatch.setattr(UsbPower, "wait_for_status", lambda self, e, timeout=5.0: False)
    dev, _ = make_device(tmp_path, monkeypatch, FakeUsb())
    with pytest.raises(PowerManagementError, match="did not runtime-suspend"):
        dev.switch_dut()


def test_switch_dut_detaches_and_releases_handle(tmp_path, monkeypatch):
    pdir = make_sysfs(tmp_path, status="suspended")
    usb = FakeUsb()
    dev, disposed = make_device(tmp_path, monkeypatch, usb)
    dev.switch_dut()
    assert usb.calls == ["detach", "reset"]
    assert disposed == [usb]
    assert (pdir / "control").read_text() == "auto"


def test_switch_dut_nonfatal_without_sysfs(tmp_path, monkeypatch):
    class Unsupported(FakeUsb):
        def is_kernel_driver_active(self, _):
            raise NotImplementedError

    dev, _ = make_device(tmp_path, monkeypatch, Unsupported())
    dev.switch_dut()
