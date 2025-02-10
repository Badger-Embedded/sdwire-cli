import sys
import logging
import click
from .device.sdwire import SDWire
from .device.sdwirec import SDWireC
from . import detect

log = logging.getLogger(__name__)


def handle_switch_host_command(ctx):
    device = ctx.obj["device"]
    device.switch_ts()


def handle_switch_target_command(ctx):
    device = ctx.obj["device"]
    device.switch_dut()


def handle_switch_off_command(ctx):
    device = ctx.obj["device"]
    if isinstance(device, SDWireC):
        log.info("SDWireC or legacy sdwire devices dont have off functionality")
        print("SDWireC dont have off functionality")
        sys.exit(1)


def handle_switch_command(ctx, serial):
    devices = detect.get_sdwire_devices()

    if serial is None:
        # check the devices
        if len(devices) == 0:
            raise click.UsageError("There is no sdwire device connected!")
        if len(devices) > 1:
            raise click.UsageError(
                "There is more then 1 sdwire device connected, please use --serial|-s to specify!"
            )
        log.info("1 sdwire/sdwirec device detected")
        ctx.obj["device"] = devices[0]
    else:
        for device in devices:
            if device.serial_string == serial:
                ctx.obj["device"] = device
                break
        else:
            raise click.UsageError(
                f"There is no such sdwire device connected with serial={serial}"
            )
