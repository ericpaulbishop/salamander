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
from ubiquity.plugin import *

NAME = 'raid_disks'
AFTER = 'timezone'
WEIGHT = 9

def run_shell(command):
	result = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True).communicate()[0]
	return result

def parse_parted_size(size):
	if size.find("MB") >= 0:
		size = re.sub("[MB\t ]+", "", size)
		bytes = int(size)*(1000*1000) #parted output assumes exactly 1 Million bytes = 1MB
		tb = 1024*1024*1024*1024
		gb = 1024*1024*1024
		mb = 1024*1024
		kb = 1024
		if bytes > tb:
			size = str( int(10*bytes/tb)/10.0 ) + " TB"
		elif bytes > gb:
			size = str( int(10*bytes/gb)/10.0 ) + " GB"
		elif bytes > mb:
			size = str( int(10*bytes/mb)/10.0 ) + " MB"
		elif bytes > kb:
			size = str( int(10*bytes/kb)/10.0 ) + " KB"
		else:
			size = str( bytes ) + " bytes"
	return size


def get_disk_data():

	#stop md devices if they exist
	os.system("sudo swapoff -a")
	os.system("sudo /etc/init.d/mdadm stop")
	os.system("sudo killall mdadm")

	diskLines = re.split("[\r\n]+", run_shell("sudo fdisk -l 2>/dev/null | grep dev | grep Disk"))
	partedLines = re.split("[\r\n]+", run_shell("sudo parted -l"))
    	
	#print "".join(diskLines)
	
	diskNames = []
	diskText = []
	diskDevs = []
	
	for line in diskLines:
		splitLine = re.split("[\t ]+", line)
       
		diskDev = ""
		if len(splitLine) > 1:
			diskDev = (re.split("[:\t ]+", line))[1]
			if re.search("^md", diskDev):
				diskDev = ""

		
		if len(diskDev) > 1:
			diskSize = parse_parted_size((re.split("[,:]+[\t ]*", line))[1])
			diskNames.append( "Disk " + diskDev + ": " + diskSize )
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
							if pline.find("extended") < 0:
								#diskInfoLines.append(pline)
								num  = parts[1]
								size = parse_parted_size(parts[4])
								type = parts[5]
								fs = ""
								if len(parts) > 6:
									fs   = parts[6]

								diskInfoLines.append( "\t" + diskDev + num + " (" + size + "), " + type + ", " + fs )
							pindex=pindex+1
							pline=partedLines[pindex]
							parts=re.split("[\t ]+", pline);
	                           
				pindex=pindex+1
		if len(diskInfoLines) == 0:
			diskInfoLines.append("\tNo Partitions Exist On This Disk")
		diskText.append(diskInfoLines)
	    

	return [diskNames, diskText, diskDevs]


def offsetControl(control):
	import pygtk
	import gtk

	container = gtk.HBox()
	offset = gtk.Label("\t")
	container.pack_start(offset, False, False, 0)
	container.pack_start(control, False, False, 1)
	container.show()
	offset.show()
	control.show()

	return container



class PageGtk(PluginUI):
	diskContainer = None
	checks = []
	diskData = [ [], [], [] ]
	
	def __init__(self, controller, *args, **kwargs):
		self.controller = controller
		import pygtk
		import gtk
		useRaid = run_shell('sudo /usr/lib/ubiquity/raid/use-raid.sh 2>&1').rstrip("\r\n")
		if useRaid == "true":
			builder = gtk.Builder()
			builder.add_from_file('/usr/share/ubiquity/gtk/stepRaid.ui')
			#builder.get_object('intro_raid').set_markup("Select drives to include in RAID Array:")
			self.plugin_widgets = builder.get_object('stepRaid')
	
	

	def getRaidDisks(self):
		import pygtk
		import gtk
		
		diskStr = ""
		for dindex in range(0, len(self.checks)):
			check = self.checks[dindex]
			if(check.get_active()):
				if len(diskStr) > 0:
					diskStr = diskStr + " "
				diskStr = diskStr + self.diskData[2][dindex]
		return diskStr
	
	def setupDiskList(self, data, usePreselected, diskDict):
		import pygtk
		import gtk
		
		self.diskData = data
		devNames = data[0]
		devParts = data[1]
		devIds   = data[2]
		
		#remove old GUI elements
		while len(self.checks) > 0:
			self.plugin_widgets.remove( self.checks.pop() )
		
		if self.diskContainer != None:
			self.plugin_widgets.remove( self.diskContainer )
	

		#setup disk checks
		lineIndex = 0
		self.diskContainer = gtk.VBox()
		diskLabel = gtk.Label("Select disks to include in RAID Array:")
		dlabContainer = gtk.HBox()
		dlabContainer.pack_start(diskLabel, False,False, 0)
		
		self.diskContainer.pack_start(dlabContainer, False, False, lineIndex)
		self.plugin_widgets.pack_start(self.diskContainer, True, True, 0)
		lineIndex = lineIndex+1
		self.diskContainer.pack_start(gtk.Label("\n\n"), False, False, lineIndex)
		self.diskContainer.show()
		dlabContainer.show()
		diskLabel.show()

		for dindex in range(0,len(devNames)):
			diskName   = devNames[dindex] 
			diskParts = "\n".join(devParts[dindex]) + "\n\n"
			
			check = gtk.CheckButton(diskName)
			self.checks.append(check)
			container = offsetControl(check)
			
			if usePreselected:
				if devIds[dindex] in diskDict:
					check.set_active(True)
				else:
					check.set_active(False)
			else:
				check.set_active(True)
			
			lineIndex = lineIndex+1
			self.diskContainer.pack_start(container, False, False, lineIndex)
			partLines = gtk.Label( diskParts )
			lineIndex = lineIndex+1
			self.diskContainer.pack_start(offsetControl(partLines), False, False, lineIndex)
			check.show()





class Page(Plugin):
	def prepare(self, unfiltered=False):
		data = get_disk_data()

		preselectedDisks = self.db.get("ubiquity/raid_disks")
		if preselectedDisks == None:
			preselectedDisks = ""

		preselectedList = re.split("\\\\?[,\t ]+", preselectedDisks)
		
		preselectedDict = {}
		usePreselected = False
		for disk in preselectedList:
			if disk != "":
				usePreselected = True
				preselectedDict[ disk ] = 1
		

		self.ui.setupDiskList(data, usePreselected, preselectedDict)
		return None

	def ok_handler(self):
		diskStr = self.ui.getRaidDisks()
		self.preseed("ubiquity/raid_disks", diskStr)
		Plugin.ok_handler(self)




