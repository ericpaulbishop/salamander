#
# Copyright (C) 2010 Eric Bishop (ericpaulbishop@gmail.com)
#
# This file is part of the Salamander modification for Ubiquity.
#
# Salamander is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Salamander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Salamander.  If not, see <http://www.gnu.org/licenses/>.


echo success_command_running > /tmp/success_status

#create target mdadm.conf 
mkdir -p /target/etc/mdadm/
cp /etc/mdadm/mdadm.conf /target/etc/mdadm/mdadm.conf

#chroot to target to update initramfs
ls /target/boot/*initrd* | sed 's/^.*\///g' >/tmp/initrdlist
initrd_img=$(head -n1 /tmp/initrdlist)
chroot /target update-initramfs -u /boot/$initrd_img
