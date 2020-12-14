#!/bin/bash
# -*- coding: utf-8 -*-
#
#  preinst.sh
#  
#  Copyright 2020 Thomas Castleman <contact@draugeros.org>
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
if [ -f /etc/kernel/postinst.d/zz-update-systemd-boot ]; then
	UUID=$(grep "^UUID=" /etc/kernel/postinst.d/zz-update-systemd-boot | sed 's/UUID=//' | sed 's/"//g')
	if [ -f /etc/systemd-boot-manager/UUID.conf ]; then
		if [ "$UUID" != "$(</etc/systemd-boot-manager/UUID.conf)" ]; then
			echo "$UUID" > /etc/systemd-boot-manager/UUID.conf
		fi
	else
		echo "$UUID" > /etc/systemd-boot-manager/UUID.conf
	fi
fi
