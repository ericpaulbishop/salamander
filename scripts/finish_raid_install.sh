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

#create target email script if necessary
if [ -e "/etc/raid_scripts/mail_alert" ] ; then
	mkdir -p /target/etc/raid_scripts/
	cp /etc/raid_scripts/mail_alert /target/etc/raid_scripts/mail_alert
	chmod -R 700  /target/etc/raid_scripts
	chown -R root /target/etc/raid_scripts
	chgrp -R root /target/etc/raid_scripts
fi

#install raid_repair script
if [ -e /usr/bin/raid_repair ] ; then
	cp /usr/sbin/raid_repair /target/usr/sbin/raid_repair
	chmod 700     /target/usr/sbin/raid_repair
	chown -R root /target/usr/sbin/raid_repair
	chgrp -R root /target/usr/sbin/raid_repair

fi

#chroot to target to update initramfs
ls /target/boot/*initrd* | sed 's/^.*\///g' >/tmp/initrdlist
initrd_img=$(head -n1 /tmp/initrdlist)
chroot /target update-initramfs -u /boot/$initrd_img
