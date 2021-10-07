#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  __init__.py
#
#  Copyright 2021 Thomas Castleman <contact@draugeros.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
"""Explain what this program does here!!!"""
import os
import sys


GREEN = "\033[92m"
RED = "\033[91m"
CLEAR = "\033[0m"
YELLOW = "\033[93m"
BLUE = '\033[94m'
NAME = GREEN + "systemd-boot-manager" + CLEAR
WARNING = NAME + "\t" + YELLOW + "WARNING: "
ERROR = NAME + "\t" + RED + "ERROR: "
STATUS = NAME + "\t" + BLUE
SUCCESS = NAME + "\t" + GREEN

CONFIG_DIR = "/etc/systemd-boot-manager"
DEFAULTS_FILE = CONFIG_DIR + "/default_entry.conf"


def eprint(*args, **kwargs):
    """Make it easier for us to print to stderr"""
    print(*args, file=sys.stderr, **kwargs)


def is_enabled():
    """Check if systemd-boot-manager is enabled"""
    if not os.path.exists(CONFIG_DIR + "/enabled.conf"):
        try:
            with open(CONFIG_DIR + "/enabled.conf", "w") as file:
                file.write("enabled")
        except PermissionError:
            eprint(f"{ ERROR }{ CONFIG_DIR }/enabled.conf does not exist.")
            eprint(f"{ ERROR }This defaults systemd-boot-manager to enabled, but")
            eprint(f"{ ERROR }the file cannot be created to allow changing of this setting.")
            eprint(f"{ ERROR }Try running `sudo systemd-boot-manager --repair'.")
        finally:
            return True
    with open(CONFIG_DIR + "/enabled.conf", "r") as file:
        return bool(file.read())
