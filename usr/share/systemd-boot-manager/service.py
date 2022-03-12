#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  service.py
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
"""Systemd service to check the default boot entry and change it, if enabled"""
import systemd_boot_manager

# If it isn't enabled, don't do anything
if systemd_boot_manager.is_enabled():
    # Default entry does not match. Do something
    if not systemd_boot_manager.check_default_entry():
        systemd_boot_manager.eprint(f"{ systemd_boot_manager.ERROR }UEFI-CONFIGURED DEFAULT BOOT ENTRY DOES NOT MATCH DEFAULT ON FILE{ systemd_boot_manager.CLEAR }")
        systemd_boot_manager.eprint(f"{ systemd_boot_manager.ERROR }CHANGING TO MATCH ENTRY ON FILE{ systemd_boot_manager.CLEAR }")
        systemd_boot_manager.eprint(f"{ systemd_boot_manager.ERROR }DEFAULT WAS: { systemd_boot_manager.get_default_boot_entry(False) }")
        intended_default = systemd_boot_manager.read_defaults_file()
        systemd_boot_manager.set_as_default_entry(intended_default, edit_file=False)
