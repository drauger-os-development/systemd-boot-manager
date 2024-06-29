#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  __init__.py
#
#  Copyright 2024 Thomas Castleman <batcastle@draugeros.org>
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
import subprocess as sp
import json
import distro
import re
from inspect import signature as sig


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
UUID_FILE = CONFIG_DIR + "/UUID.conf"
ROOT_DEVICE_FILE = CONFIG_DIR + "/root_device.conf"

DISTRO = distro.name().replace(" ", "_")

BOOT_DIR = "/boot/"
EFI_DIR = BOOT_DIR + "efi"
SD_LOADER_DIR = EFI_DIR + "/loader"
CLEAN_DIR = SD_LOADER_DIR + "/entries/"
CONF_FILE = [CLEAN_DIR + DISTRO, ".conf"]

# Default Flags
ROOT_FLAGS = "quiet splash"
RECOVERY_FLAGS = "ro recovery nomodeset"


def get_conf_file_contents(root_pointer: str, boot_args: str, state=None) -> str:
    """Get conf file contents"""
    contents = ["title  " + DISTRO,
                "linux   /" + DISTRO + "/vmlinuz",
                "initrd  /" + DISTRO + "/initrd.img",
                "options root=" + root_pointer + " " + boot_args]
    # this is a bit verbose, but None evaluates to False, so we need to be careful
    if state is True:
        return contents
    if state is False:
        return tuple(contents)
    return "\n".join(contents)


def get_new_conf_file_contents(root_pointer: str, boot_args: str, version: str, state=None) -> str:
    """Get conf file contents with new file locations"""
    dirs = os.listdir(EFI_DIR)
    del dirs[dirs.index("EFI")]
    del dirs[dirs.index("loader")]
    del dirs[dirs.index(DISTRO)]
    rand_dir = dirs[0]
    del dirs
    contents = ["title   " + DISTRO,
                "linux   " + rand_dir + "/" + version + "/linux",
                "initrd  " + rand_dir + "/" + version + "/initrd.img-" + version,
                "options root=" + root_pointer + " " + boot_args]
    # this is a bit verbose, but None evaluates to False, so we need to be careful
    if state is True:
        return contents
    if state is False:
        return tuple(contents)
    return "\n".join(contents)


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
    entries = sp.check_output(["bootctl", "list", "--no-pager"]).decode().split("\n")
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


def set_as_default_entry(entry, edit_file=True, verbose=False):
    """Set 'entry' as the default bootloader entry"""
    entries = get_boot_entries(verbose=verbose)
    for each in entries:
        if entries[each]["id"] == entry:
            if entries[each]["default"] is True:
                eprint(BLUE + "Already Default Entry" + CLEAR)
            # Set as default here
            if edit_file:
                update_defaults_file(entry)
            try:
                sp.check_call(["bootctl", "set-default", entry])
            except sp.CalledProcessError as err:
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
    output = sp.check_output(["os-prober"]).decode()
    output = output.split("\n")
    for each in enumerate(output):
        output[each[0]] = output[each[0]].split(":")
    return output


def check_loader(verbose=False):
    """Check to see if loader file exists. If not, make it"""
    if not isinstance(verbose, bool):
        verbose = False
    BOOT_DIR = "/boot/"
    EFI_DIR = BOOT_DIR + "efi"
    SD_LOADER_DIR = EFI_DIR + "/loader"
    if not os.path.exists(SD_LOADER_DIR + "/loader.conf"):
        if verbose:
            print("loader.conf not present. Generating...")
        try:
            with open(f"{CONFIG_DIR}/loader.conf", "r") as file:
                contents = file.read()
        except FileNotFoundError:
            eprint(ERROR, end="")
            eprint(f"loader.conf config file not found in {CONFIG_DIR}")
            eprint(ERROR, end="")
            eprint("please reinstall systemd-boot-manager and try again", end="")
            eprint(CLEAR)
            failure(2)
        if verbose:
            print("Read config file")
        contents = contents.replace("{distro}", DISTRO)
        contents = contents.split("\n")
        for each in range(len(contents) - 1, -1, -1):
            if len(contents[each]) < 1:
                continue
            if contents[each][0] == "#":
                del contents[each]
        contents = "\n".join(contents)
        if verbose:
            print("Parsed config file")
        with open(SD_LOADER_DIR + "/loader.conf", "w") as file:
            file.write(contents)
        if verbose:
            print("New loader file created")


def get_key(device, key_type="uuid", verbose=False):
    """Get the key used to point to a specific device at boot.
    `key_type` can be one of:

    UUID
    PARTUUID
    LABEL
    PATH
    """
    if verbose:
        print("Ensure valid key type...")
    key_type = key_type.lower()
    types = ("uuid", "partuuid", "path", "label")
    if key_type not in types:
        raise ValueError(f"'{ key_type }' not one of: { ', '.join(types) }")
    if verbose:
        print("Ensure valid device...")
    if not os.path.exists(device):
        raise FileNotFoundError(f"'{ device }: path not recognized'")
    if verbose:
        print(f"Getting { key_type } for { device }...")
    output = json.loads(sp.check_output(["lsblk", "--json",
                                                 "--output",
                                                 f"path,{ key_type }",
                                                 device]).decode())
    output = output["blockdevices"]
    for each in output:
        if each["path"] == device:
            return each[key_type]


def get_devices():
    """Get devices from LSBLK"""
    try:
        devices = json.loads(sp.check_output(["lsblk", "--output",
                                                      "PATH,TYPE,MOUNTPOINT,PARTUUID",
                                                      "--json"]).decode().replace("I", "i"))
    except sp.CalledProcessError as err:
        eprint(ERROR + "CANNOT GET ROOT PARTITION UUID. LSBLK FAILED." + CLEAR)
        eprint("The error was: ")
        eprint(err.output)
        sys.exit(err.returncode)
    devices = devices["blockdevices"]
    for each in range(len(devices) - 1, -1, -1):
        if "loop" == devices[each]["type"]:
            del devices[each]
    return devices


def get_root_partition(verbose):
    """Determine the root partition"""
    if verbose:
        print("getting devices . . .")
    devices = get_devices()
    for each in devices:
        if each["mountpoint"] == "/":
            if verbose:
                print(f"Found root partition to be: { each['path'] }")
            return each["path"]


def is_root():
    """Check if we have root"""
    return os.geteuid() == 0


def get_settings(verbose=False):
    """Retreive settings"""
    try:
        if verbose:
            print("Attempting to read settings file...")
        with open(f"{CONFIG_DIR}/general.json", "r") as file:
            if verbose:
                print("Parsing settings file...")
            SETTINGS = json.load(file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        # if the file accidentally gets deleted, or mis-formatted, fall back to this internal setup
        eprint(ERROR + "/etc/systemd-boot-manager/general.json is misformatted or missing. Falling back to internal defaults..." + CLEAR)
        SETTINGS = {
        "no-var": False,
        "standard_boot_args": ROOT_FLAGS,
        "recovery_args": RECOVERY_FLAGS,
        "dual-boot": False,
        "key": "partuuid",
        "compat_mode": False,
        }
    # make sure settings are valid
    if (("standard_boot_args" not in SETTINGS) or (not isinstance(SETTINGS["standard_boot_args"], str))):
        SETTINGS["standard_boot_args"] = ROOT_FLAGS
    if (("recovery_args" not in SETTINGS) or (not isinstance(SETTINGS["recovery_args"], str))):
        SETTINGS["recovery_args"] = RECOVERY_FLAGS
    if "key" not in SETTINGS:
        SETTINGS["key"] = "partuuid"
    if "compat_mode" not in SETTINGS:
        SETTINGS["compat_mode"] = False
    if "dual-boot" not in SETTINGS:
        SETTINGS["dual-boot"] = False
    return SETTINGS


def set_settings(key, value, verbose=False):
    """Set a settings value"""
    settings = get_settings(verbose=verbose)
    if key.lower() in ("no-var", "dual-boot", "compat_mode"):
        value = bool(str(value) in ("1", "True", "enable", "on",
                                    "enabled", True))
    if key.lower() == "key":
        if value.lower() not in ("partuuid", "uuid", "path", "label"):
            raise ValueError(f"{ value }: Not a valid value for keys. Must be one of 'partuuid', 'uuid', 'path', 'label'")
        value = value.lower()
    settings[key.lower()] = value
    try:
        with open("/etc/systemd-boot-manager/general.json", "w+") as file:
            json.dump(settings, file, indent=2)
    except PermissionError:
        eprint(ERROR + "You need to run this program as root to change settings." + CLEAR)


def check_uuid(verbose=False):
    """Check correct UUID is in use"""
    if verbose:
        print("Reading UUID file . . .")
    with open(UUID_FILE, "r") as conf:
        uuid_stored = conf.read()
    if uuid_stored[-1] == "\n":
        uuid_stored = uuid_stored[:-1]
    uuid_generated = get_UUID(verbose)
    if verbose:
        print("Comparing UUID file to UUID in memory . . .")
    return uuid_stored == uuid_generated


def get_UUID(verbose, uuid="partuuid"):
    """Get UUID for the root partition"""
    # Get root partition
    if verbose:
        print("Getting root partition...")
    part = get_root_partition(verbose)
    # get key setting
    uuid = get_key(part, uuid, verbose)
    # we get our key
    return uuid


def generate_loader_entry(boot_args: str, root_pointer: str,
                          kernel="latest", func=get_conf_file_contents):
    """Generate a given bootloader entry"""
    # This flag variable controls whether or not the new method is to be used.
    flag = False
    if "version" in sig(func).parameters:
        flag = True
        if kernel.lower() == "latest":
            contents = func(root_pointer, boot_args, get_kernel_versions()[0], state=True)
        else:
            contents = func(root_pointer, boot_args, kernel, state=True)
    else:
        contents = func(root_pointer, boot_args, state=True)
    if kernel.lower() == "latest":
        with open("".join(CONF_FILE), "w+") as output:
            for each in contents:
                output.write(each + "\n")
    else:
        with open(("-" + kernel).join(CONF_FILE), "w+") as output:
            line = 0
            for each in contents:
                if line == 0:
                    output.write(each + " " + kernel)
                    output.write("\n")
                    line += 1
                    continue
                if not flag:
                    if line in (1, 2):
                        output.write(each + "-" + kernel)
                    else:
                        output.write(each)
                else:
                    output.write(each)
                output.write("\n")
                line += 1


def generate_recovery_loader_entry(boot_args: str, root_pointer: str,
                                   kernel="latest", func=get_conf_file_contents):
    """Generate a given recovery bootloader entry"""
    flag = False
    if "version" in sig(func).parameters:
        flag = True
        if kernel.lower() == "latest":
            contents = func(root_pointer, boot_args, get_kernel_versions()[0], state=True)
        else:
            contents = func(root_pointer, boot_args, kernel, state=True)
    else:
        contents = func(root_pointer, boot_args, state=True)
    if kernel.lower() == "latest":
        with open("_Recovery".join(CONF_FILE), "w+") as output:
            for each in enumerate(contents):
                if each[0] == 0:
                    output.write(each[1] + " Recovery")
                else:
                    output.write(each[1])
                output.write("\n")
    else:
        with open(("-" + kernel + "_Recovery").join(CONF_FILE), "w+") as output:
            line = 0
            for each in contents:
                if line == 0:
                    output.write(each + " " + kernel + " Recovery")
                    output.write("\n")
                    line += 1
                    continue
                if not flag:
                    if line in (1, 2):
                        output.write(each + "-" + kernel)
                    else:
                        output.write(each)
                else:
                    output.write(each)
                output.write("\n")
                line += 1


def get_root_pointer(VERBOSE):
    """Get root pointer

        A root pointer is whatever you pass as `root` to the kernel command line.
        Example:

        root=UUID=<UUID here>

        or

        root=LABEL=ROOT

        The part after `root=` is the root pointer.
        """
    SETTINGS = get_settings(VERBOSE)
    if os.path.exists("/etc/systemd-boot-manager/root_device.conf"):
        # this is the easiest solution for the user, but takes more processing for us
        with open("/etc/systemd-boot-manager/root_device.conf", "r") as file:
            ROOT_POINTER = file.read()
        ROOT_POINTER = ROOT_POINTER.split("\n")[0]
        ROOT_POINTER = get_key(ROOT_POINTER, SETTINGS["key"], verbose=VERBOSE)
        if SETTINGS["key"].lower() != "path":
            ROOT_POINTER = f"{ SETTINGS['key'].upper() }={ ROOT_POINTER }"
    elif os.path.exists("/etc/systemd-boot-manager/UUID.conf"):
        # this takes less processing from us, but we have to figure out if this is a UUID or PARTUUID
        with open("/etc/systemd-boot-manager/UUID.conf", "r") as file:
            ROOT_POINTER = file.read()
        ROOT_POINTER = ROOT_POINTER.split("\n")[0]
        try:
            uuids = json.loads(sp.check_output(["lsblk", "--json",
                                                "--output",
                                                "path,uuid,partuuid,label"]))
        except sp.CalledProcessError:
            try:
                uuids = json.loads(sp.check_output(["lsblk", "--json",
                                                    "--output",
                                                    "path,uuid,partuuid"]))
            except sp.CalledProcessError:
                uuids = json.loads(sp.check_output(["lsblk", "--json",
                                                    "--output",
                                                    "path,uuid"]))
        uuids = uuids["blockdevices"]
        for each in uuids:
            if ROOT_POINTER == each["uuid"]:
                ROOT_POINTER = f"UUID={ ROOT_POINTER }"
                break
            if "partuuid" in each:
                if ROOT_POINTER == each["partuuid"]:
                    ROOT_POINTER = f"PARTUUID={ ROOT_POINTER }"
                    break
            if "label" in each:
                if ROOT_POINTER == each["label"]:
                    ROOT_POINTER = f"LABEL={ ROOT_POINTER }"
                    break
    else:
        # this entire block exists to improve stability and resliancy. In case one of the 2 files we looked for previously don't exist, we still have other options.
        eprint(WARNING + "Could not find settings files that point to root partition. Will attempt to infer..." + CLEAR)
        devices = json.loads(sp.check_output(["lsblk", "--json",
                                                    "--output",
                                                    "mountpoint,partuuid"]))
        devices = devices["blockdevices"]
        root = ""
        for each in devices:
            if each["mountpoint"] == "/":
                root = each["partuuid"]
                break
        if root == "":
            eprint(ERROR + "Could not infer root parition." + CLEAR)
            sys.exit(2)
        ROOT_POINTER = f"PARTUUID={ root }"
    return ROOT_POINTER


def get_kernel_versions():
    """Get all kernel versions"""
    KERNELS = os.listdir(BOOT_DIR)
    # Filter down to just the Kernel Images
    for each in range(len(KERNELS) - 1, -1, -1):
        if "vmlinuz-" not in KERNELS[each]:
            del KERNELS[each]
        # Remove dpkg-tmp images
        elif ".dpkg-tmp" in KERNELS[each][-9:]:
            del KERNELS[each]
    # Check to make sure we have kernels to work with
    if len(KERNELS) < 1:
        error("NO KERNELS FOUND IN /boot")
        failure(1)
    kernel_verts = {}
    for each in KERNELS:
        vert = each.split("-")[1:]
        if len(vert) > 1:
            patch_version = 1
            while f"{ vert[0] }.{ patch_version }" in kernel_verts:
                patch_version += 1
            key = f"{ vert[0] }.{ patch_version }"
        else:
            key = vert[0]
        kernel_verts[key] = "-".join(vert)

    # Sort remaining kernels, get latest
    KERNELS = sorted(list(kernel_verts.keys()), key=LooseVersion)
    output = []
    for each in KERNELS:
        output.append(kernel_verts[each])
    return output


class LooseVersion():
    """Version numbering for anarchists and software realists.
    Implements the standard interface for version number classes as
    described above.  A version number consists of a series of numbers,
    separated by either periods or strings of letters.  When comparing
    version numbers, the numeric components will be compared
    numerically, and the alphabetic components lexically.  The following
    are all valid version numbers, in no particular order:

        1.5.1
        1.5.2b2
        161
        3.10a
        8.02
        3.4j
        1996.07.12
        3.2.pl0
        3.1.1.6
        2g6
        11g
        0.960923
        2.2beta29
        1.13++
        5.5.kw
        2.0b1pl0

    In fact, there is no such thing as an invalid version number under
    this scheme; the rules for comparison are simple and predictable,
    but may not always give the results you want (for some definition
    of "want").

    ---

    This class is stolen ("stolen") from the distutils module in Python 3.10 standard library.
    Here, I have manually merged it with it's super class in order to reduce processing time,
    memory usage, and disk space. The super class wasn't being used for anything else anyways.

    We have done this because we rely on this class for sort()-ing kernel images by version, and with
    the deprecation of distutils in Python 3.12, we need to find a solution sooner rather than later.

    This prevents further technical debt, reduces dependencies, reduces memory footprint, and allows more
    visibility of this code in case something goes wrong. This is legitimately the WORST solution for
    something like this I have EVER come up with. But, unless the setuptools module has something
    that will work for this better than what we have here, I see no better solution.
    """

    component_re = re.compile(r'(\d+ | [a-z]+ | \.)', re.VERBOSE)

    def __init__ (self, vstring=None):
        if vstring:
            self.parse(vstring)

    def __repr__ (self):
        return "%s ('%s')" % (self.__class__.__name__, str(self))

    def __eq__(self, other):
        c = self._cmp(other)
        if c is NotImplemented:
            return c
        return c == 0

    def __lt__(self, other):
        c = self._cmp(other)
        if c is NotImplemented:
            return c
        return c < 0

    def __le__(self, other):
        c = self._cmp(other)
        if c is NotImplemented:
            return c
        return c <= 0

    def __gt__(self, other):
        c = self._cmp(other)
        if c is NotImplemented:
            return c
        return c > 0

    def __ge__(self, other):
        c = self._cmp(other)
        if c is NotImplemented:
            return c
        return c >= 0

    def parse (self, vstring):
        # I've given up on thinking I can reconstruct the version string
        # from the parsed tuple -- so I just store the string here for
        # use by __str__
        self.vstring = vstring
        components = [x for x in self.component_re.split(vstring)
                              if x and x != '.']
        for i, obj in enumerate(components):
            try:
                components[i] = int(obj)
            except ValueError:
                pass

        self.version = components

    def __str__ (self):
        return self.vstring

    def __repr__ (self):
        return "LooseVersion ('%s')" % str(self)

    def _cmp (self, other):
        if isinstance(other, str):
            other = LooseVersion(other)
        if all(isinstance(part, int) for part in self.version) and all(isinstance(part, int) for part in other.version):
            if self.version == other.version:
                return 0
            if self.version < other.version:
                return -1
            if self.version > other.version:
                return 1
        else:
            str_self_version = [str(part) for part in self.version]
            str_other_version = [str(part) for part in other.version]
            if str_self_version == str_other_version:
                return 0
            if str_self_version < str_other_version:
                return -1
            if str_self_version > str_other_version:
                return 1


# end class LooseVersion
