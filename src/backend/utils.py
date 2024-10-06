from backend.device.sdwire import SDWire
from backend import detect


def handle_switch_host_command(ctx):
    pass


def handle_switch_target_command(ctx):
    pass


def handle_switch_off_command(ctx):
    pass


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
        ctx.obj["device"] = devices[0]
    else:
        for device in devices:
            if device.badgerd_serial_string == serial:
                ctx.obj["device"] = device
                break
        else:
            raise click.UsageError(
                f"There is no such sdwire device connected with serial={serial}"
            )

    device: SDWire = ctx.obj["device"]
    import sys

    device.invoke(" ".join(sys.argv[1:]))
