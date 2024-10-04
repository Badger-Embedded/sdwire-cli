#!/usr/bin/env python
import click
import detect


@click.group()
def main():
    pass


@main.command()
def list():
    for sdwire in detect.get_sdwire_devices():
        print(
            f"{sdwire.badgerd_serial_string} - [{sdwire.product_string}::{sdwire.manufacturer_string}]"
        )


if __name__ == "__main__":
    main()
