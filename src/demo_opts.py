
Skip to content
This repository

    Pull requests
    Issues
    Marketplace
    Explore

    @SloMusti

5
33

    14

rm-hull/luma.examples
Code
Issues 6
Pull requests 0
Projects 0
Wiki
Insights
luma.examples/examples/demo_opts.py
a6d5ba7 3 days ago
@rm-hull rm-hull Chmod +x examples
@rm-hull
@thijstriemstra
executable file 58 lines (43 sloc) 1.36 KB
# -*- coding: utf-8 -*-
# Copyright (c) 2014-17 Richard Hull and contributors
# See LICENSE.rst for details.

import sys
import logging

from luma.core import cmdline, error


# logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)-15s - %(message)s'
)
# ignore PIL debug messages
logging.getLogger("PIL").setLevel(logging.ERROR)


def display_settings(args):
    """
    Display a short summary of the settings.
    :rtype: str
    """
    iface = ''
    display_types = cmdline.get_display_types()
    if args.display not in display_types['emulator']:
        iface = 'Interface: {}\n'.format(args.interface)

    return 'Display: {}\n{}Dimensions: {} x {}\n{}'.format(
        args.display, iface, args.width, args.height, '-' * 40)


def get_device(actual_args=None):
    """
    Create device from command-line arguments and return it.
    """
    if actual_args is None:
        actual_args = sys.argv[1:]
    parser = cmdline.create_parser(description='luma.examples arguments')
    args = parser.parse_args(actual_args)

    if args.config:
        # load config from file
        config = cmdline.load_config(args.config)
        args = parser.parse_args(config + actual_args)

    # create device
    try:
        device = cmdline.create_device(args)
    except error.Error as e:
        parser.error(e)

    print(display_settings(args))

    return device

    © 2017 GitHub, Inc.
    Terms
    Privacy
    Security
    Status
    Help

    Contact GitHub
    API
    Training
    Shop
    Blog
    About
