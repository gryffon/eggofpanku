# Egg of P'an Ku -- an unofficial client for Legend of the Five Rings
# Copyright (C) 2008  Peter C O Johansson
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
"""Settings dialog module for Egg of P'an Ku."""

import wx
import string

#Local Import
from db import database, dbimport

from settings.xmlsettings import settings
from settings.xmlsettings import DEFAULT_SETTINGS
from settings.xmlsettings import locationsettings
from settings.xmlsettings import DEFAULT_SETTINGS_DATA_DIR



class GeneralSettings(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		
		psizer = wx.BoxSizer(wx.VERTICAL)
		
		sbsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Player'), wx.VERTICAL)
		
		self.txtName = wx.TextCtrl(self, value=settings.playername)
		
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(self, label='Name:'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		sizer.Add(self.txtName, 1, 0, 0)
		sbsizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 5)

		psizer.Add(sbsizer, 0, wx.CENTRE|wx.EXPAND|wx.ALL, 4)

		#Card Draw settings
		sbsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Game Options'), wx.VERTICAL)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(self, label='Holdings:'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		
		self.chkCEHoldings = wx.CheckBox(self, label='Use CE Holdings')
		self.chkCEHoldings.SetValue(settings.use_celestial_holdings)
		sizer.Add(self.chkCEHoldings , 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		sbsizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 5)
		
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(self, label='Cards:'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		
		self.chkCelestialDraw = wx.CheckBox(self, label='Draw 6 Cards (Celestial/Emperor Rules)')
		self.chkCelestialDraw.SetValue(settings.celestial_card_draw)
		sizer.Add(self.chkCelestialDraw , 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		sbsizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 5)
		
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(self, label='Logging:'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		
		self.chkRecordLog = wx.CheckBox(self, label='Log multiplayer games')
		self.chkRecordLog.SetValue(settings.log_multiplayer_games)
		sizer.Add(self.chkRecordLog , 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		sbsizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 5)

		#self.cmbStartup = wx.ComboBox(self, style=wx.CB_READONLY)
		#self.cmbStartup.Append('Do nothing')
		#self.cmbStartup.Append('Fetch Stronghold only')
		#self.cmbStartup.Append('Fetch Stronghold and fill provinces')
		#self.cmbStartup.SetValue(self.cmbStartup.GetString(settings.start_procedure))
		
		#sizer = wx.BoxSizer(wx.HORIZONTAL)
		#sizer.Add(wx.StaticText(self, label='On game start:'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		#sizer.Add(self.cmbStartup, 0, 0, 0)
		#sbsizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 5)
		
		psizer.Add(sbsizer, 0, wx.CENTRE|wx.EXPAND|wx.ALL, 4)
		
		self.SetSizer(psizer)
	
	def Save(self):
		settings.playername = self.txtName.GetValue()
		settings.log_multiplayer_games = self.chkRecordLog.GetValue();
		settings.celestial_card_draw = self.chkCelestialDraw.GetValue();
		settings.use_celestial_holdings = self.chkCEHoldings.GetValue();
		#settings.start_procedure = self.cmbStartup.GetSelection()
	
class DatabaseSettings(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		
		db = database.get()
		panelsizer = wx.BoxSizer(wx.VERTICAL)
		
		#Database 
		# -------
		sbsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Current Database'), wx.VERTICAL)
		
		sbsizer.Add(wx.StaticText(self, label='%s (%d cards)' % (db.date, len(db))), 0, wx.EXPAND|wx.ALL, 5)
		if settings.cardsource:
			cs = settings.cardsource
		else:
			cs = '(no card source)'
			
		self.lblCardDB = wx.StaticText(self, label=cs)
		sbsizer.Add(self.lblCardDB, 0, wx.EXPAND|wx.ALL, 5)
		
		self.btnReload = wx.Button(self, label='Reload')
		self.Bind(wx.EVT_BUTTON, self.OnReloadDatabase, self.btnReload)
		
		self.btnChangeSource = wx.Button(self, label='Change Database')
		self.Bind(wx.EVT_BUTTON, self.OnChangeDatabase, self.btnChangeSource)
		
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.btnReload, 0, wx.RIGHT, 5)
		sizer.Add(self.btnChangeSource, 0, 0, 0)
		sbsizer.Add(sizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
		
		panelsizer.Add(sbsizer, 0, wx.CENTRE|wx.EXPAND|wx.ALL, 4)
		
		#Image Packs
		# -------
		sbsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Image Packs'), wx.VERTICAL)
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sbsizer.Add(wx.StaticText(self, label='Egg of P\'an Ku will look in the  below directory for card images.'), 0, wx.ALL, 5)
		self.dirImagePacks = wx.TextCtrl(self, value=settings.dir_imagepacks)
		sbsizer.Add(self.dirImagePacks, 0, wx.EXPAND|wx.ALL, 5)
		self.btnDefaultImagesPath = wx.Button(self, label='Default')
		self.btnGetImagesPath = wx.Button(self, label='Browse')
		self.Bind(wx.EVT_BUTTON, self.OnDefaultImagesPath, self.btnDefaultImagesPath)
		self.Bind(wx.EVT_BUTTON, self.OnGetImagesPath, self.btnGetImagesPath)
		sizer.Add(self.btnDefaultImagesPath, 0, wx.RIGHT, 5)
		sizer.Add(self.btnGetImagesPath, 0, wx.RIGHT, 5)
		sbsizer.Add(sizer,0, wx.ALIGN_RIGHT|wx.ALL, 5)
		
		panelsizer.Add(sbsizer, 0, wx.EXPAND|wx.ALL, 4)

		#Data Dir
		# -------
		sbsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Data Directory'), wx.VERTICAL)
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sbsizer.Add(wx.StaticText(self, label='Egg of P\'an Ku will look in the  below directory for it\'s data.'), 0, wx.ALL, 5)
		self.dirData = wx.TextCtrl(self, value=locationsettings.data_dir)
		sbsizer.Add(self.dirData, 0, wx.EXPAND|wx.ALL, 5)
		self.btnDefaultDataDir = wx.Button(self, label='Default')
		self.btnGetDataDir = wx.Button(self, label='Browse')
		#Renable changing data_dir
		self.btnDefaultDataDir.Disable()
		self.btnGetDataDir.Disable()
		self.Bind(wx.EVT_BUTTON, self.OnDefaultDataDir, self.btnDefaultDataDir)
		self.Bind(wx.EVT_BUTTON, self.OnGetDataDir, self.btnGetDataDir)
		sizer.Add(self.btnDefaultDataDir, 0, wx.RIGHT, 5)
		sizer.Add(self.btnGetDataDir, 0, wx.RIGHT, 5)
		sbsizer.Add(sizer,0, wx.ALIGN_RIGHT|wx.ALL, 5)
		
		panelsizer.Add(sbsizer, 0, wx.EXPAND|wx.ALL, 4)

		self.SetSizer(panelsizer)
	
	def Save(self):
		new_dir_imagepacks = self.dirImagePacks.GetValue()
		if new_dir_imagepacks != DEFAULT_SETTINGS['dir_imagepacks']:
			settings.imagepackdir_changed = True
		else:
			settings.imagepackdir_changed = False
		settings.dir_imagepacks = self.dirImagePacks.GetValue()
		locationsettings.data_dir = self.dirData.GetValue()
		
	def Import(self):
		try:
#			importer = database.XMLImporter(settings.cardsource)
#			importer.convert()
			database.reset()
			
		except Exception, e:
			wx.MessageDialog(self, 'There was a problem importing the card database.\n' \
				'Consult the manual for possible ways to address this.\n\n%s: %s\n\n' \
				% (e.__class__.__name__, str(e)), 'Card database import error',
				wx.ICON_ERROR).ShowModal()
			return False
		return True
	
	def OnDefaultImagesPath(self, event):
		self.dirImagePacks.SetValue(DEFAULT_SETTINGS['dir_imagepacks'])


	def OnGetImagesPath(self, event):
		fdlg = wx.DirDialog(None, message='Please select the directory containing the images', \
						    defaultPath=settings.dir_imagepacks, name='Select Images Path')
		if fdlg.ShowModal() == wx.ID_OK:
			self.dirImagePacks.SetValue(fdlg.GetPath() if fdlg.GetPath().endswith('\\') else fdlg.GetPath() + '\\')

	def OnDefaultDataDir(self, event):
		self.dirData.SetValue(DEFAULT_SETTINGS_DATA_DIR['data_dir'])
		


	def OnGetDataDir(self, event):
		fdlg = wx.DirDialog(None, message='Please select the directory containing Egg of P\'an Ku data ', \
						    defaultPath=locationsettings.data_dir, name='Select Data Dir')
		if fdlg.ShowModal() == wx.ID_OK:
			self.dirData.SetValue(fdlg.GetPath() if fdlg.GetPath().endswith('\\') else fdlg.GetPath() + '\\')
			

	def OnChangeDatabase(self, event):
		fdlg = wx.FileDialog(None, wildcard='XML card database (*.xml)|*.xml|All files (*.*)|*.*', style=wx.OPEN|wx.FILE_MUST_EXIST)
		if fdlg.ShowModal() == wx.ID_OK:
			oldsrc = settings.cardsource
			settings.cardsource = fdlg.GetPath()
					
			settings.WriteSettingsFile()
			if self.Import():
#				wx.MessageDialog(self, 'The card database source was changed and re-imported.\n' \
#					'These changes will take effect next time you run Egg of P\'an Ku.', \
#					'Card reload successful', wx.ICON_INFORMATION).ShowModal()
				
				self.lblCardDB.SetLabel(settings.cardsource)				
			else:
				settings.cardsource = oldsrc  # Best to reset it, so it's not invalid.
				settings.WriteSettingsFile()				
		
	def OnReloadDatabase(self, event):
		self.Import()
#			wx.MessageDialog(self, 'The local card database was re-imported from the given\n' \
#				'source XML file. These changes will take effect next time\n' \
#				'you run Egg of P\'an Ku.', 'Card reload successful', wx.ICON_INFORMATION).ShowModal()

class PlayfieldSettings(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		
		psizer = wx.BoxSizer(wx.VERTICAL)
		
		# Canvas category--------------------
		sbsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Canvas'), wx.VERTICAL)
		
		self.cmbCanvas = wx.ComboBox(self, style=wx.CB_READONLY)
		self.cmbCanvas.Append('Solid color')
		self.cmbCanvas.Append('Vertical gradient')
		self.cmbCanvas.Append('Horizontal gradient')
		self.cmbCanvas.SetValue(self.cmbCanvas.GetString(settings.playfield_bg_mode))
		self.clrBackground1 = wx.ColourPickerCtrl(self, wx.ID_ANY, settings.playfield_bg_color1)
		self.clrBackground2 = wx.ColourPickerCtrl(self, wx.ID_ANY, settings.playfield_bg_color2)
		self.Bind(wx.EVT_COMBOBOX, self.OnCanvasChange, self.cmbCanvas)
		
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(self, label='Background:'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		sizer.Add(self.cmbCanvas, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		sizer.Add(wx.StaticText(self, label='Color 1:'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		sizer.Add(self.clrBackground1, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		sizer.Add(wx.StaticText(self, label='Color 2:'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		sizer.Add(self.clrBackground2, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
		sbsizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 5)
		
		self.chkBackgroundImage = wx.CheckBox(self, label='Use background image:')
		self.chkBackgroundImage.SetValue(settings.playfield_bg_image_display)
		self.fileBackgroundImage = wx.FilePickerCtrl(self, path=settings.playfield_bg_image)
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.chkBackgroundImage, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		sizer.Add(self.fileBackgroundImage, 1, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
		sbsizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 5)

		self.spinCardSpacing = wx.SpinCtrl(self, initial=settings.canvas_card_spacing)
		self.spinCardSpacing.SetRange(minVal=1, maxVal=5)
		
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(self, label='Province Spacing:'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		sizer.Add(self.spinCardSpacing, 1, 0, 0)
		sbsizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 5)
				
		psizer.Add(sbsizer, 0, wx.CENTRE|wx.EXPAND|wx.ALL, 4)


		# Attachments --------------------------
		
		sbsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Card Attachments'), wx.VERTICAL)
		sbsizer.Add(wx.StaticText(self, label='Allow cards to be attached to:'), 0, wx.EXPAND|wx.ALL, 5)
		self.attachBoxes = {}
		swin = wx.ScrolledWindow(self, style=wx.VSCROLL|wx.SUNKEN_BORDER, size=(-1, -1))
		swinsizer = wx.BoxSizer(wx.VERTICAL)
		for type in database.cardTypes:
			chk = wx.CheckBox(swin, label=type)
			if type.lower() in settings.attach_ok:
				chk.SetValue(True)
			self.attachBoxes[type.lower()] = chk
			swinsizer.Add(chk, 0, wx.EXPAND|wx.ALL, 2)
		swin.SetSizer(swinsizer)
		swin.SetScrollbars(0, 10, 0, swinsizer.GetMinSize()[1]/10)
		sbsizer.Add(swin, 1, wx.EXPAND|wx.ALL, 5)
		
		psizer.Add(sbsizer, 1, wx.CENTRE|wx.EXPAND|wx.ALL, 4)

		# Done
		self.SetSizer(psizer)

		self.clrBackground2.Enable(settings.playfield_bg_mode != 0)

	
	def OnCanvasChange(self, event):
		self.clrBackground2.Enable(self.cmbCanvas.GetCurrentSelection() != 0)
	
	def Save(self):
		settings.playfield_bg_mode = self.cmbCanvas.GetCurrentSelection()
		settings.playfield_bg_color1 = self.clrBackground1.GetColour().Get()
		settings.playfield_bg_color2 = self.clrBackground2.GetColour().Get()
		settings.playfield_bg_image_display = self.chkBackgroundImage.GetValue()
		settings.playfield_bg_image = self.fileBackgroundImage.GetPath()

		settings.canvas_card_spacing = self.spinCardSpacing.GetValue()
		
		settings.attach_ok = [type for type, ctrl in self.attachBoxes.iteritems() if ctrl.GetValue()]
	

class SettingsDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, title='Preferences', size=(490, 430))
		
		sizer = wx.BoxSizer(wx.VERTICAL)  # Main sizer
		
		# Settings tabs
		self.pages = [
			('General', GeneralSettings),
			('Database/Images', DatabaseSettings),
			('Playfield', PlayfieldSettings),
			]
		
		notebook = wx.Notebook(self, style=wx.NB_TOP)
		self.pages = [(title, page(notebook)) for title, page in self.pages]
		for title, page in self.pages:
			notebook.AddPage(page, title)
			
		# Buttons
		buttonsizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
		
		sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 2)
		sizer.Add(buttonsizer, 0, wx.EXPAND | wx.ALL, 5)
		self.SetSizer(sizer)
		
		#wx.EVT_BUTTON(self, self.GetAffirmativeId(), self.SaveSettings)
		self.Bind(wx.EVT_BUTTON, self.SaveSettings, id=self.GetAffirmativeId())
		
	
	def SaveSettings(self, event):
		for title, page in self.pages:
			page.Save()
		settings.WriteSettingsFile()
		locationsettings.WriteSettingsFile()
		event.Skip()


if __name__ == "__main__":
	try:
		app = wx.PySimpleApp()
		import dbimport
		if dbimport.EnsureExists():
			frame = SettingsDialog(None)
			frame.ShowModal()
	finally:
		del app
