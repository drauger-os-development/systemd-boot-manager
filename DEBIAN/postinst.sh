#!/bin/bash
# -*- coding: utf-8 -*-
#
#  postinst.sh
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
fstab=$(grep "^/dev" /etc/fstab)
IFS="
"
for each in $fstab; do
	check=$(echo "$each" | awk '{print $2}' | grep -vE '/[a-z]')
	if [ "$check" == "/" ]; then
		root=$(echo "$each" | awk '{print $1}')
	fi
done
echo "$(blkid -s PARTUUID -o value $root)" > /etc/systemd-boot-manager/UUID.conf

