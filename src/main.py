#!/usr/bin/env python
import click


@click.group()
def main():
    print(__file__)


@main.command()
def list():
    raise NotImplementedError("list")


if __name__ == "__main__":
    main()
