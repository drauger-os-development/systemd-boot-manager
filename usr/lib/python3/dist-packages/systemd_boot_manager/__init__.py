#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  __init__.py
#
#  Copyright 2022 Thomas Castleman <contact@draugeros.org>
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
"""Library for systemd-boot-manager"""
import os
import sys
import subprocess
import distro


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


DISTRO = distro.name().replace(" ", "_")


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
            eprint(f"{ ERROR }{ CONFIG_DIR }/enabled.conf does not exist.{ CLEAR }")
            eprint(f"{ ERROR }This defaults systemd-boot-manager to enabled, but{ CLEAR }")
            eprint(f"{ ERROR }the file cannot be created to allow changing of this setting.{ CLEAR }")
            eprint(f"{ ERROR }Try running `sudo systemd-boot-manager --repair'.{ CLEAR }")
        finally:
            return True
    with open(CONFIG_DIR + "/enabled.conf", "r") as file:
        return bool(file.read())


def update_defaults_file(default_entry, verbose=False):
    """Write default bootloader entry to config file"""
    DEFAULTS_FILE_ADDON = """# This file defines the default boot entry that systemd-boot should be using.
    # It only reads the first line, but these other lines are being commented out like
    # in a shell script because if this file gets renamed and used for other purposes,
    # then this syntax will be honored
    #
    # That first line needs to be the Entry ID you want to be default from
    # `bootctl list`
    #
    # If you don't want systemd-boot-manager changing the default entry, just comment that
    # first line out and it will not do anything."""
    try:
        if verbose:
            print("Writing default boot entry to " + DEFAULTS_FILE + " . . .")
        with open(DEFAULTS_FILE, "w") as conf:
            if default_entry is not None:
                conf.write(default_entry)
            else:
                if verbose:
                    print("No default set, writing dummy value . . .")
                conf.write("# default_entry_here.conf")
            conf.write("\n")
            conf.write(DEFAULTS_FILE_ADDON)
    except (FileNotFoundError, PermissionError) as err:
        eprint(ERROR + "An Unwarrented error has occured. Please try again later." + CLEAR)


def get_boot_entries(verbose=False):
    """Get bootloader entries"""
    if verbose:
        print("Getting boot entry list . . .")
    entries = subprocess.check_output(["bootctl", "list", "--no-pager"]).decode().split("\n")
    output = {}
    name = ""
    if verbose:
        print("Parsing List. . .")
    for each in entries:
        if "title: " in each:
            if "(default)" in each:
                output[" ".join(each.split()[1:])[:-10]] = {"default":True}
                name = " ".join(each.split()[1:])[:-10]
            else:
                output[" ".join(each.split()[1:])] = {"default":False}
                name = " ".join(each.split()[1:])
        elif "id: " in each:
            output[name]["id"] = each.split()[-1]
    return output


def get_default_boot_entry(verbose):
    """Get default bootloader entry"""
    entries = get_boot_entries(verbose=verbose)
    if verbose:
        print("Checking parsed data for 'default' flag . . .")
    for each in entries:
        if entries[each]["default"] is True:
            return entries[each]["id"]


def set_as_default_entry(entry, edit_file=True):
    """Set 'entry' as the default bootloader entry"""
    entries = get_boot_entries()
    for each in entries:
        if entries[each]["id"] == entry:
            if entries[each]["default"] is True:
                eprint(BLUE + "Already Default Entry" + CLEAR)
            # Set as default here
            if edit_file:
                update_defaults_file(entry)
            try:
                subprocess.check_call(["bootctl", "set-default", entry])
            except subprocess.CalledProcessError as err:
                eprint(ERROR + "CANNOT SET INTENDED DEFAULT" + CLEAR)
                eprint("Error was:")
                eprint(err.output)
            print(GREEN + "SUCCESS!" + CLEAR)
    eprint(ERROR + "ID Not found. Please provide a valid ID. IDs can be found using `systemd-boot-manager --list'.")


def read_defaults_file():
    """Read Defaults file and return the default"""
    with open(DEFAULTS_FILE, "r") as conf:
        return conf.read().split()[0]


def check_default_entry(verbose=False):
    """Confirm default boot entry is correct"""
    if verbose:
        print("Reading defaults file . . .")
    intended_default = read_defaults_file()
    default = get_default_boot_entry(verbose)
    if verbose:
        print("Comparing defaults file to defaults in memory . . .")
    if default == intended_default:
        return True
    elif intended_default == "#":
        return True
    else:
        return False

def get_os_prober():
    """Provide the output of `os-prober` in a Python native format"""
    output = subprocess.check_output(["os-prober"]).decode()
    output = output.split("\n")
    for each in enumerate(output):
        output[each[0]] = output[each[0]].split(":")
    return output
