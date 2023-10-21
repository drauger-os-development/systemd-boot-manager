#!/bin/bash
# -*- coding: utf-8 -*-
#
#  systemd-boot-manager.sh
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
# systemd-boot-manager completions
data=$(systemd-boot-manager --help | tail --lines=+3 | awk '{print $1,$2}' | grep "^-")
line_count=$(echo "$data" | wc -l)
max_line_count=$line_count
output=""
while [[ $line_count -gt 0 ]]; do
	# get line
	line=$(echo "$data" | tail -$line_count | head -1)
	# parse line
	line=${line%[*}
	line=${line%(*}
	line=$(echo "$line" | sed 's/,//g')
	if $(echo "$line" | grep -q '^--'); then
		line=$(echo "$line" | sed 's/ [a-zA-Z]*//g')
	fi
	# add line to completion list
	if [[ "$max_line_count" == "$line_count" ]]; then
		output="$line"
	else
		output="$output $line"
	fi
	# echo "$line"
	# decrement line count to iterate
	line_count=$((line_count - 1))
done
complete -W "$output" systemd-boot-manager

# update-systemd-boot completions
data=$(update-systemd-boot --help |  tail --lines=+5 | head --lines=-2 | awk '{print $1,$2}' | grep "^-")
line_count=$(echo "$data" | wc -l)
max_line_count=$line_count
output=""
while [[ $line_count -gt 0 ]]; do
	# get line
	line=$(echo "$data" | tail -$line_count | head -1)
	# parse line
	line=${line%[*}
	line=${line%(*}
	line=$(echo "$line" | sed 's/,//g')
	if $(echo "$line" | grep -q '^--'); then
		line=$(echo "$line" | sed 's/ [a-zA-Z]*//g')
	fi
	# add line to completion list
	if [[ "$max_line_count" == "$line_count" ]]; then
		output="$line"
	else
		output="$output $line"
	fi
	# echo "$line"
	# decrement line count to iterate
	line_count=$((line_count - 1))
done
complete -W "$output" update-systemd-boot
