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

#backslash strip, to get rid of \ character introduced before whitespace in debconf
def bs(str):
	str = re.sub("\\\\ ", " ", str)
	return str

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
	gmailControls = []
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


	def setSelectionsFromDisks(self, diskStr, raidLevel, swapSize, fileSystem, emailParameters):
		import pygtk
		import gtk

		#initialize RAID levels
		diskList = re.split("[\t ]+", diskStr);
		levelDict = { "5":0, "0":1 } 
		self.levelNumbers = ["5", "0" ] 
		raidDescriptionList = 	[	"RAID Level 5  (Block Striping With Parity)", 
						"RAID Level 0  (Striping)"
					]

		if len(diskList) % 2 == 0:
			currentLevel = "10"
			if len(diskList) > 3 :
				self.levelNumbers = ["10", "6", "5", "1", "0"]
				levelDict = { "10":0, "6":1, "5":2, "1":3, "0":4 } 
				raidDescriptionList = [	"RAID Level 10 (Mirroring+Striping)",
							"RAID Level 6  (Block Striping With Dual Parity)", 
							"RAID Level 5  (Block Striping With Parity)", 
							"RAID Level 1  (Mirroring)",
							"RAID Level 0  (Striping)"
							]
			else:
				self.levelNumbers = ["10", "5", "1", "0"]
				levelDict = { "10":0, "5":1, "1":2, "0":3 } 
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

		selectedLevelIndex = 0
		if raidLevel != None:
			if raidLevel in levelDict:
				selectedLevelIndex = levelDict[ raidLevel ]

		for levindex in range(0,len(self.levelNumbers)):
			group = None
			if len(self.levelRadios) > 0:
				group = self.levelRadios[0]
			radio = gtk.RadioButton(group, raidDescriptionList[levindex],False)
			if len(self.levelRadios) == selectedLevelIndex:
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
		mb = 1024*1024
		swapDict = { 4096*mb:0, 3072*mb:1, 2048*mb:2, 1536*mb:3, 1024*mb:4, 512*mb:5, 256*mb:6, 0*mb:7}
		swapIndex = 2
		if swapSize != None:
			if swapSize != "":
				if int(swapSize) in swapDict:
					swapIndex = swapDict[ int(swapSize) ]

		fsDict = { "ext4":0, "ext3":1, "xfs":2 }
		fsIndex = 0
		if fileSystem != None:
			if fileSystem in fsDict:
				fsIndex = fsDict[ fileSystem ]

		self.swapControl = gtk.combo_box_new_text()
		self.swapControl.append_text("4096MB")
		self.swapControl.append_text("3072MB")
		self.swapControl.append_text("2048MB")
		self.swapControl.append_text("1536MB")
		self.swapControl.append_text("1024MB")
		self.swapControl.append_text(" 512MB")
		self.swapControl.append_text(" 256MB")
		self.swapControl.append_text("  None")
		self.swapControl.set_active(swapIndex)
		self.swapControl.show()
		
		self.fileSystemControl = gtk.combo_box_new_text()
		self.fileSystemControl.append_text("ext4")
		self.fileSystemControl.append_text("ext3")
		self.fileSystemControl.append_text("xfs")
		self.fileSystemControl.set_active(fsIndex)
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
		
		if emailParameters[1] != None:
			if emailParameters[1] != "":
				if emailParameters[1] != "smtp.gmail.com":
					self.useGmailControl.set_active(1)
					self.rebuildEmailTable()
					for cntlIndex in range(1,len(emailParameters)):
						if emailParameters[cntlIndex] != None:
							if emailParameters[cntlIndex] != "":
								(self.emailControls[cntlIndex-1]).set_text( emailParameters[cntlIndex] )
				else:
					if emailParameters[2] != None:
							if emailParameters[2] != "":
								(self.gmailControls[0]).set_text( emailParameters[2] )
					if emailParameters[3] != None:
							if emailParameters[3] != "":
								(self.gmailControls[1]).set_text( emailParameters[3] )
					if emailParameters[6] != None:
							if emailParameters[6] != "":
								(self.gmailControls[2]).set_text( emailParameters[6] )



		if emailParameters[0] != None:
			if emailParameters[0] == "false":
				self.useEmailCheck.set_active(False)
				self.useEmailCallback(self.useEmailCheck)
		


		self.plugin_widgets.pack_start(self.emailContainer, True, False, controlIndex)


	
	def rebuildEmailTable(self):
	
		import pygtk
		import gtk

		if self.emailTable != None:
			self.emailContainer.remove(self.emailTable)
	
		emailLabels   = [ "\tEmail Server:", "\tServer User:", "\tServer Password:", "\tServer Port:", "\tFrom Address:", "\tRecipient Addresses:" ]
		gmailLabels   = [ "\tGmail User:", "\tGmail Password:", "\tRecipient Addresses:" ]
		emailDefaults = [ "smtp.myserver.com", "my_username", "", "25", "me@myserver.com", "recipient@somewhere.com"]
		gmailDefaults = [ "my_username@gmail.com", "", "recipient@somewhere.com" ]
		
		if len(emailDefaults) != len(self.emailControls):
			self.emailControls = []
			for cntlIndex in range(0,len(emailDefaults)):
				cntl = gtk.Entry(50)
				cntl.set_text( emailDefaults[cntlIndex] )
				if re.search("Password", emailLabels[cntlIndex]):
					cntl.set_invisible_char('*')
					cntl.set_visibility(False)
				self.emailControls.append(cntl)

		if len(gmailDefaults) != len(self.gmailControls):
			self.gmailControls = []
			for cntlIndex in range(0,len(gmailDefaults)):
				cntl = gtk.Entry(50)
				cntl.set_text( gmailDefaults[cntlIndex] )
				if re.search("Password", gmailLabels[cntlIndex]):
					cntl.set_invisible_char('*')
					cntl.set_visibility(False)
				self.gmailControls.append(cntl)

		gmailSelection = self.useGmailControl.get_active_text()
		
		controlLabels = emailLabels
		self.emailTable = gtk.Table(6,2)
		controlList = self.emailControls
		if gmailSelection == "Use Gmail":
			controlLabels = gmailLabels
			controlList = self.gmailControls


		tableRowIndex=0
		for labelText in controlLabels:
			eControl = controlList[tableRowIndex]
			eLabelContainer = labelControl("", gtk.Label(labelText), 1)
			eControl.show()
			self.emailTable.attach(eLabelContainer, 0, 1, tableRowIndex, tableRowIndex+1,gtk.FILL, gtk.FILL, 5)
			self.emailTable.attach(eControl, 1, 2, tableRowIndex, tableRowIndex+1,gtk.FILL|gtk.EXPAND, gtk.FILL, 75)
			tableRowIndex = tableRowIndex+1
			if len(controlList) <= tableRowIndex:
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


	def getEmailParameters(self):
		gmailSelection = self.useGmailControl.get_active_text()
		emailParams = []
		if self.useEmailCheck.get_active():
			emailParams.append("true")
		else:
			emailParams.append("false")

		if gmailSelection == "Use Gmail":
			user = ((self.gmailControls[0]).get_text()).lower()
			if not re.search("gmail.com", user):
				user = user + "@gmail.com"
			useEmail = emailParams[0]
			emailParams = [ useEmail, "smtp.gmail.com", user, (self.gmailControls[1]).get_text(), "587", user, (self.gmailControls[2]).get_text() ]
		else:
			for paramIndex in range(0,len(self.emailControls)):
				emailParams.append( (self.emailControls[paramIndex]).get_text() )
		
		return emailParams



	def getFileSystem(self):
		return self.fileSystemControl.get_active_text()

class Page(Plugin):
	def prepare(self, unfiltered=False):
		diskStr = bs(self.db.get('ubiquity/raid_disks'))
		rl      = bs(self.db.get("ubiquity/raid_level"))
		sw      = bs(self.db.get("ubiquity/raid_swap"))
		fs      = bs(self.db.get("ubiquity/raid_file_system"))
		
		ep      = [ bs(self.db.get("ubiquity/raid_use_email")), bs(self.db.get("ubiquity/raid_email_server")), bs(self.db.get("ubiquity/raid_email_user")), bs(self.db.get("ubiquity/raid_email_password")), bs(self.db.get("ubiquity/raid_email_port")), bs(self.db.get("ubiquity/raid_email_from")), bs(self.db.get("ubiquity/raid_email_to")) ]
		
				
		self.ui.setSelectionsFromDisks(diskStr, rl, sw, fs, ep)
		
		return None

	def ok_handler(self):
		raidLevel = self.ui.getRaidLevel()
		swapSize = self.ui.getSwapSize() 
		fileSystem = self.ui.getFileSystem()
		emailParameters = self.ui.getEmailParameters()

		self.preseed("ubiquity/raid_level",              raidLevel)
		self.preseed("ubiquity/raid_swap",               swapSize)
		self.preseed("ubiquity/raid_file_system",        fileSystem)
		self.preseed("ubiquity/raid_use_email",          emailParameters[0])
		self.preseed("ubiquity/raid_email_server",       emailParameters[1])
		self.preseed("ubiquity/raid_email_user",         emailParameters[2])
		self.preseed("ubiquity/raid_email_password",     emailParameters[3])
		self.preseed("ubiquity/raid_email_port",         emailParameters[4])
		self.preseed("ubiquity/raid_email_from",         emailParameters[5])
		self.preseed("ubiquity/raid_email_to",           emailParameters[6])


		Plugin.ok_handler(self)

