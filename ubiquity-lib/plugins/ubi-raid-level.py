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

NAME = 'raid_level'
AFTER = 'raid_disks'
WEIGHT = 200

def run_shell(command):
	result = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True).communicate()[0]
	return result


def labelControl(labelText, control, controlFirst):
	import pygtk
	import gtk

	container = gtk.HBox()
	lab = gtk.Label(labelText)
	if controlFirst == 1:
		container.pack_start(control, False, False, 0)
		container.pack_start(lab, False, False, 1)
	else:
		container.pack_start(lab, False, False, 0)
		container.pack_start(control, False, False, 1)

	container.show()
	lab.show()
	control.show()

	return container

class PageGtk(PluginUI):
	levelRadios = []
	levelNumbers = []
	levelContainer = None
	
	swapControl = None
	fileSystemControl = None
	swapAndFileSystemTable = None

	useEmailCheck = None
	useGmailControl = None
	emailControls = []
	emailTable = None
	emailContainer = None


	currentLevel = "5"
	def __init__(self, controller, *args, **kwargs):
		self.controller = controller
		import pygtk
		import gtk
		useRaid = run_shell('sudo /usr/lib/ubiquity/raid/use-raid.sh 2>&1').rstrip("\r\n")
		if useRaid == "true":
			builder = gtk.Builder()
			builder.add_from_file('/usr/share/ubiquity/gtk/stepRaid.ui')
			#builder.get_object('intro_raid').set_markup("Select Desired RAID Level:")
			self.plugin_widgets = builder.get_object('stepRaid')
	
	def levelRadioCallback(self, widget, data=None):
		import pygtk
		import gtk
		if widget.get_active():
			self.currentLevel = data
	
	def useEmailCallback(self, useEmailCheck):
		import pygtk
		import gtk
		if self.useEmailCheck.get_active():
			self.useGmailControl.set_sensitive(True)
			self.emailTable.set_sensitive(True)
		else:
			self.useGmailControl.set_sensitive(False)
			self.emailTable.set_sensitive(False)
			

	def gmailControlCallback(self, gmailComboBox):
		import pygtk
		import gtk
		self.rebuildEmailTable()


	def setSelectionsFromDisks(self, diskStr):
		import pygtk
		import gtk

		#initialize RAID levels
		diskList = re.split("[\t ]+", diskStr);
		self.levelNumbers = ["5", "0" ] 
		raidDescriptionList = 	[	"RAID Level 5  (Block Striping With Parity)", 
						"RAID Level 0  (Striping)"
					]

		if len(diskList) % 2 == 0:
			currentLevel = "10"
			if len(diskList) > 3 :
				self.levelNumbers = ["10", "6", "5", "1", "0"]
				raidDescriptionList = [	"RAID Level 10 (Mirroring+Striping)",
							"RAID Level 6  (Block Striping With Dual Parity)", 
							"RAID Level 5  (Block Striping With Parity)", 
							"RAID Level 1  (Mirroring)",
							"RAID Level 0  (Striping)"
							]
			else:
				self.levelNumbers = ["10", "5", "1", "0"]
				raidDescriptionList = [	"RAID Level 10 (Mirroring+Striping)",
							"RAID Level 5  (Block Striping With Parity)", 
							"RAID Level 1  (Mirroring)",
							"RAID Level 0  (Striping)"
							]
		
		
		#remove old GUI elements
		while len(self.levelRadios) > 0:
			self.plugin_widgets.remove( self.levelRadios.pop() )

		if self.levelContainer != None:
			self.plugin_widgets.remove( self.levelContainer )

		if self.swapAndFileSystemTable != None:
			self.plugin_widgets.remove( self.swapAndFileSystemTable )
		
		if self.emailContainer != None:
			if self.emailTable != None:
				self.emailContainer.remove(self.emailTable)
				self.emailTable = None
			self.plugin_widgets.remove( self.emailContainer )
			self.emailContainer = None

		#setup level radios
		controlIndex = 0
		self.levelContainer = gtk.VBox()
		levelLabel = gtk.Label("Select Desired RAID Level:")
		levlabContainer = gtk.HBox()
		levlabContainer.pack_start(levelLabel, False,False, 0)

		self.levelContainer.pack_start(levlabContainer, False, False, 0)
		self.plugin_widgets.pack_start(self.levelContainer, True, True, controlIndex)
		controlIndex = controlIndex + 1
		self.levelContainer.show()
		levlabContainer.show()
		levelLabel.show()

		for levindex in range(0,len(self.levelNumbers)):
			group = None
			if len(self.levelRadios) > 0:
				group = self.levelRadios[0]
			radio = gtk.RadioButton(group, raidDescriptionList[levindex],False)
			if len(self.levelRadios) == 0:
				radio.set_active(True)
				self.currentLevel = self.levelNumbers[levindex]
			radio.connect("toggled", self.levelRadioCallback, self.levelNumbers[levindex])
			self.levelRadios.append(radio)
			
			rContainer = gtk.HBox()
			offset = gtk.Label("\t")
			rContainer.pack_start(offset, False, False, 0)
			rContainer.pack_start(radio, False, False, 1)
			self.levelContainer.pack_start(rContainer, False, False, levindex+1)
			rContainer.show()
			offset.show()
			radio.show()
		
		
		#setup swap & file system drop-downs
		self.swapControl = gtk.combo_box_new_text()
		self.swapControl.append_text("4096MB")
		self.swapControl.append_text("3072MB")
		self.swapControl.append_text("2048MB")
		self.swapControl.append_text("1536MB")
		self.swapControl.append_text("1024MB")
		self.swapControl.append_text(" 512MB")
		self.swapControl.append_text(" 256MB")
		self.swapControl.append_text("  None")
		self.swapControl.set_active(2)
		self.swapControl.show()
		
		self.fileSystemControl = gtk.combo_box_new_text()
		self.fileSystemControl.append_text("ext4")
		self.fileSystemControl.append_text("ext3")
		self.fileSystemControl.append_text("xfs")
		self.fileSystemControl.set_active(0)
		self.fileSystemControl.show()

		swapLabelContainer = labelControl("", gtk.Label("Swap Size: "), 1)
		fileSystemLabelContainer = labelControl("", gtk.Label("Root File System: "), 1)

		self.swapAndFileSystemTable = gtk.Table(2,2)
		self.swapAndFileSystemTable.show()
		self.swapAndFileSystemTable.attach(swapLabelContainer,       0, 1, 0, 1, gtk.FILL, gtk.FILL)
		self.swapAndFileSystemTable.attach(self.swapControl,         1, 2, 0, 1, gtk.FILL, gtk.FILL)
		self.swapAndFileSystemTable.attach(fileSystemLabelContainer, 0, 1, 1, 2, gtk.FILL, gtk.FILL)
		self.swapAndFileSystemTable.attach(self.fileSystemControl,   1, 2, 1, 2, gtk.FILL, gtk.FILL)
		self.plugin_widgets.pack_start(self.swapAndFileSystemTable, True, False, controlIndex)
		controlIndex = controlIndex + 1



		#setup notification controls
		self.emailContainer = gtk.VBox()
		self.useEmailCheck = gtk.CheckButton()
		self.useEmailCheck.set_active(True)
		self.useEmailCheck.connect("clicked", self.useEmailCallback)

		useEmailContainer = labelControl("Configure Email Notification on Disk Failure", self.useEmailCheck, 1)
		self.emailContainer.pack_start(useEmailContainer, False,False,0)
		self.emailContainer.show()
	
		self.useGmailControl = gtk.combo_box_new_text()
		self.useGmailControl.append_text("Use Gmail")
		self.useGmailControl.append_text("Use Other SMTP Server")
		self.useGmailControl.set_active(0)
		self.useGmailControl.connect("changed", self.gmailControlCallback)
		useGmailContainer = labelControl("\t", self.useGmailControl, 0)
		self.emailContainer.pack_start(useGmailContainer, False,False,1)

		self.rebuildEmailTable()
		
		self.plugin_widgets.pack_start(self.emailContainer, True, False, controlIndex)


	
	def rebuildEmailTable(self):
	
		import pygtk
		import gtk

		if self.emailTable != None:
			self.emailContainer.remove(self.emailTable)
	
		self.emailControls = []
		gmailSelection = self.useGmailControl.get_active_text()
		
		emailControlLabels = [ "\tEmail Server:", "\tServer User:", "\tServer Password:", "\tServer Port:", "\tFrom Address:", "\tRecipient Addresses:" ]
		self.emailTable = gtk.Table(6,2)
		if gmailSelection == "Use Gmail":
			emailControlLabels = ["\tGmail User:", "\tGmail Password:", "\tRecipient Addresses:" ]
			self.emailTable = gtk.Table(3,2)

		self.emailControls = []	
		tableRowIndex=0
		for labelText in emailControlLabels:
			eControl = gtk.Entry(50)
			eLabelContainer = labelControl("", gtk.Label(labelText), 1)
			eControl.show()
			self.emailTable.attach(eLabelContainer, 0, 1, tableRowIndex, tableRowIndex+1,gtk.FILL, gtk.FILL, 5)
			self.emailTable.attach(eControl, 1, 2, tableRowIndex, tableRowIndex+1,gtk.FILL|gtk.EXPAND, gtk.FILL, 75)
			tableRowIndex = tableRowIndex+1
			self.emailControls.append(eControl)

		self.emailContainer.pack_start(self.emailTable, False, False, 2)
		self.emailTable.show()
	



	def getRaidLevel(self):
		return self.currentLevel

	def getSwapSize(self):
		#convert to bytes
		txt = re.sub("[MB ]+", "", self.swapControl.get_active_text())
		if txt == "None" or txt == "":
			txt="0"
		return str( (int(txt))*1024*1024)


	def getFileSystem(self):
		return self.fileSystemControl.get_active_text()

class Page(Plugin):
	def prepare(self, unfiltered=False):
		diskStr = self.db.get('ubiquity/raid_disks')
		self.ui.setSelectionsFromDisks(diskStr)
		return None

	def ok_handler(self):
		raidLevel = self.ui.getRaidLevel()
		swapSize = self.ui.getSwapSize() 
		fileSystem = self.ui.getFileSystem()
		self.preseed("ubiquity/raid_level", raidLevel)
		self.preseed("ubiquity/raid_swap", swapSize)
		self.preseed("ubiquity/raid_file_system", fileSystem)
		Plugin.ok_handler(self)

