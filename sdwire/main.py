#!/usr/bin/env python
import logging
import click
from .backend import utils
from .backend import detect
from .backend.device.sdwire import SDWire


@click.group()
@click.option("--debug", required=False, is_flag=True, help="Enable debug output")
def main(debug=None):
    if debug:
        logging.basicConfig(level=logging.DEBUG)


@main.command()
def list():
    print(f"Serial\t\t\tProduct Info\t\tBlock Dev")
    for sdwire in detect.get_sdwire_devices():
        print(sdwire)


@main.group()
@click.pass_context
@click.option(
    "-s",
    "--serial",
    required=False,
    help="Serial number of the sdwire device, if there is only one sdwire connected then it will be used by default",
)
def switch(ctx: click.Context, serial=None):
    """
    dut/target => connects the sdcard interface to target device

    ts/host => connects the sdcard interface to host machine

    off => disconnects the sdcard interface from both host and target
    """
    ctx.ensure_object(dict)
    utils.handle_switch_command(ctx, serial)


@switch.command()
@click.pass_context
def ts(ctx: click.Context):
    """
    ts/host => connects the sdcard interface to host machine
    """
    ctx.ensure_object(dict)
    utils.handle_switch_host_command(ctx)


@switch.command()
@click.pass_context
def host(ctx: click.Context):
    """
    ts/host => connects the sdcard interface to host machine
    """
    ctx.ensure_object(dict)
    utils.handle_switch_host_command(ctx)


@switch.command()
@click.pass_context
def dut(ctx: click.Context):
    """
    dut/target => connects the sdcard interface to target device
    """
    ctx.ensure_object(dict)
    utils.handle_switch_target_command(ctx)


@switch.command()
@click.pass_context
def target(ctx: click.Context):
    """
    dut/target => connects the sdcard interface to target device
    """
    ctx.ensure_object(dict)
    utils.handle_switch_target_command(ctx)


@switch.command()
@click.pass_context
def off(ctx: click.Context):
    """
    off => disconnects the sdcard interface from both host and target
    """
    ctx.ensure_object(dict)
    utils.handle_switch_off_command(ctx)


# investigate further to use click in circuitpython
# def invoke():
#     main.main("switch ts".split(), "sdwire", "_SDWIRE_COMPLETE")


if __name__ == "__main__":
    main()
