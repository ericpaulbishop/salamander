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


import re
import os
import subprocess
import sys


def run_shell(command):
	result = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True).communicate()[0]
	return result


def get_disk_data():
	diskLines = re.split("[\r\n]+", run_shell("sudo fdisk -l 2>/dev/null | grep dev | grep Disk"))
	partedLines = re.split("[\r\n]+", run_shell("sudo printf \"y\\ny\\ny\\ny\\ny\\n\" | sudo parted -l"))
	
	diskNames = []
	diskText = []
	diskDevs = []
	diskSizes = [];
	
	for line in diskLines:
		splitLine = re.split("[\t ]+", line)
        
		if len(splitLine) > 1:
			diskNames.append( (re.split(",", line))[0] )

			diskSize = (re.split(",", line))[1]
			diskSize = re.sub("bytes", "", diskSize)
			diskSize = re.sub("[\t ]+", "", diskSize)
			diskSize = int(diskSize)
			diskSizes.append(diskSize)


			diskDev = (re.split("[:\t ]+", line))[1]
			diskDevs.append(diskDev)
			diskInfoLines = []
	
	
			pindex=0
			while pindex < len(partedLines):
				pline = partedLines[pindex]
				if pline.find(diskDev) > 0 and pline.find("Error") < 0:
					while pindex < len(partedLines)-1 and pline.find("Number") !=0:
						pindex=pindex+1
						pline=partedLines[pindex]
					
					if pline.find("Number") == 0:
						pindex=pindex+1
						pline=partedLines[pindex]
						parts=re.split("[\t ]+", pline);
						while pline.find(" ") == 0 and len(parts) > 3:
							diskInfoLines.append(pline)
							pindex=pindex+1
							pline=partedLines[pindex]
							parts=re.split("[\t ]+", pline);
	                           
				pindex=pindex+1
		if len(diskInfoLines) == 0:
			diskInfoLines.append("\tNo Partitions Exist On This Disk")
		diskText.append(diskInfoLines)
	    

	return [diskNames, diskText, diskDevs, diskSizes]

def initialize_raid(raidStr, swapSize, raidLevel, fstype, emailParams):
	
	#build index of raid disks
	raidList = re.split("[\t ]+", raidStr)
	raidDict = {}
	for r in raidList:
		raidDict[r] = 1

	# first, wipe all existing partitions and reinitialize partition tables 
	# on all disks in raid array
	diskData = get_disk_data()

	os.system("sudo swapoff -a")
	diskDevs = diskData[2]
	diskSizes = diskData[3]
	raidSize = -1
	for dindex in range(0,len(diskDevs)):
		diskDev = diskDevs[dindex]
		if diskDev in raidDict:
			if raidSize < 0 or diskSizes[dindex] < raidSize:
				raidSize = diskSizes[dindex]
			print "sudo parted -s " + diskDev + " mklabel msdos"
			os.system("sudo parted -s " + diskDev + " mklabel msdos")


	raidSize = raidSize-(1000*1000*10)
	rootSize = raidSize-(1000*1000*10)

	if swapSize > 0 and rootSize-swapSize <= 1024*1024*1024:
		swapSize = rootSize - (1024*1024*1024)
		if swapSize < 0:
			swapSize = 0
		else:
			rootSize = (1024*1024*1024)
	else:
		rootSize = rootSize - swapSize

	#parted takes numbers in MB, where it thinks 1MB is exactly 10^7 bytes
	raidMb = raidSize/(1000.0*1000.0)
	rootMb = rootSize/(1000.0*1000.0)
	swapMb = swapSize/(1000.0*1000.0)
	gapMb = (5*1024*1024)/(1000.0*1000.0)

	rootPartStartEnd = str(gapMb) + " " + str(gapMb+rootMb)
	swapPartStartEnd = str(gapMb+rootMb) + " " + str(gapMb+rootMb+swapMb)

	#create partitions to be included in raid array
	for diskDev in raidList:
		print "sudo parted -s " + diskDev + " mkpart primary " + rootPartStartEnd
		os.system("sudo parted -s " + diskDev + " mkpart primary " + rootPartStartEnd)
		os.system("sudo parted -s " + diskDev + " set 1 raid on")
		if swapMb > 0:
			os.system("sudo parted -s " + diskDev + " mkpart primary " + swapPartStartEnd )
			os.system("sudo parted -s " + diskDev + " set 2 raid on")






	#create raid array
	os.system("sudo killall mdadm >/dev/null 2>&1")
	os.system("sudo killall -9 mdadm >/dev/null 2>&1")
	
	os.system("sudo printf \"y\\ny\\ny\\ny\\ny\\n\" | sudo mdadm --create /dev/md0 --force --level=" + raidLevel + " --raid-devices=" + str(len(raidList)) + " " + "1 ".join(raidList) + "1 >/tmp/create1_out 2>&1" )
	if swapMb > 0: 
		os.system("sudo printf \"y\\ny\\ny\\ny\\ny\\n\" | sudo mdadm --create /dev/md1 --force --level=" + raidLevel + " --raid-devices=" + str(len(raidList)) + " " + "2 ".join(raidList) + "2 >/tmp/create2_out 2>&1" ) 


	#save configuration to config file
	os.system("sudo mdadm --detail --scan > /tmp/mdadm.conf")
	os.system("sudo mkdir -p /etc/mdadm")
	os.system("sudo cp /tmp/mdadm.conf /etc/mdadm/mdadm.conf")

	os.system("echo 'swapMb = " + str(swapMb) + "' > /tmp/swapmb");
	os.system("echo 'swapMb = " + str(rootMb) + "' > /tmp/rootmb");
	


	#format main partition within raid
	if fstype == "xfs":
		os.system("sudo mkfs." + fstype + " -f /dev/md0")
	else:
		os.system("sudo mkfs." + fstype + " /dev/md0")
	os.system("sudo mkdir /target");
	os.system("sudo mount -t " + fstype + " /dev/md0 /target")


	#create fstab
	root_uuid = (run_shell("sudo ls -l /dev/disk/by-uuid | grep \"md0$\" | awk ' { print $8 } '")).rstrip("\r\n")
	fstype_with_spacer = fstype
	while len(fstype_with_spacer) < 8:
		fstype_with_spacer = fstype_with_spacer + " "

        os.system("sudo mkdir /target/etc")
	os.system("sudo chmod 755 /target/etc")

	os.system("sudo echo \"# /etc/fstab: static file system information.\" >/target/etc/fstab")
	os.system("sudo echo \"#\" >> /target/etc/fstab")
	os.system("sudo echo \"# <file system> <mount point>   <type>  <options>       <dump>  <pass>\" >>/target/etc/fstab")
	os.system("sudo echo \"proc            /proc           proc    defaults        0       0\" >>/target/etc/fstab")
	os.system("sudo echo \"# /dev/md0\" >>/target/etc/fstab")
	os.system("sudo echo \"UUID=" + root_uuid + " /               " + fstype_with_spacer + "relatime        0       1\" >>/target/etc/fstab")


	#format swap & add to fstab
	if swapMb > 0:
		swap_uuid = (run_shell("sudo mkswap /dev/md1 2>/dev/null | grep UUID | sed 's/^.*UUID/UUID/g'")).rstrip("\r\n")
		os.system("sudo echo \"# /dev/md1\" >> /target/etc/fstab")
		os.system("sudo echo \"" + swap_uuid + " none            swap    sw              0       0\" >>/target/etc/fstab")
		

	#add final line for cdrom to fstab
	os.system( "if [ -e /dev/scd0 ] ; then sudo echo \"/dev/scd0       /media/cdrom0   udf,iso9660 user,noauto,exec,utf8 0       0\" >> /target/etc/fstab ; fi")


	#setup email script if requested
	if emailParams[0] == "true":
		os.system("sudo mkdir -p /etc/raid_scripts")
		os.system("sudo echo '#!/usr/bin/python'>/etc/raid_scripts/mail_alert")
		os.system("sudo echo ''>>/etc/raid_scripts/mail_alert")
		os.system("sudo echo 'serverName     =\"" + emailParams[1] + "\"'>>/etc/raid_scripts/mail_alert")
		os.system("sudo echo 'serverUserName =\"" + emailParams[2] + "\"'>>/etc/raid_scripts/mail_alert")
		os.system("sudo echo 'serverPassword =\"" + emailParams[3] + "\"'>>/etc/raid_scripts/mail_alert")
		os.system("sudo echo 'serverPort     =\"" + emailParams[4] + "\"'>>/etc/raid_scripts/mail_alert")
		os.system("sudo echo 'mailFrom       =\"" + emailParams[5] + "\"'>>/etc/raid_scripts/mail_alert")
		os.system("sudo echo 'mailTo         =\"" + emailParams[6] + "\"'>>/etc/raid_scripts/mail_alert")
		os.system("sudo cat /cdrom/scripts/raid_mail_template | sudo grep -v \"^#\" >>/etc/raid_scripts/mail_alert")
		os.system("sudo echo 'PROGRAM /etc/raid_scripts'>>/etc/mdadm/mdadm.conf")


def main(argv):
	raidStr=re.sub("\\\\", "", argv[0])
	swapSize=argv[1]
	raidLevel=argv[2]
	fstype=argv[3]

	emailParams = [ argv[4], argv[5], argv[6], argv[7], argv[8], argv[9], argv[10] ]

	initialize_raid(raidStr, int(swapSize), raidLevel, fstype, emailParams)


if __name__ == "__main__":
	main(sys.argv[1:])
