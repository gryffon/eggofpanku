# Egg of P'an Ku -- an unofficial client for Legend of the Five Rings
# Copyright (C) 2008  Peter C O Johansson, Paige Watson
# Copyright (C) 2009,2010  Paige Watson
# Copyright (C) 2014  Ryan Karetas
# 
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
"""
	Proxy GUI module for Egg of P'an Ku.

author: Ryan Karetas
file: proxygui.py
date: 21 Jul 2014
"""

import wx

#Use for testing
if __name__ == "__main__":
	import os
	parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	os.sys.path.insert(0,parentdir) 

#Local Imports
from db import proxydb

class quick_create_proxy_dialog(wx.Dialog):
	cardTypes = {}
	
	def get_cardtype(self):
		return self.cardTypes[self.cmbType.GetValue()]
	
	def GetStats(self):
		return {
			'type':self.get_cardtype(),
			'name':self.txtName.GetValue(),
			'force':self.txtForce.GetValue(),
			'chi':self.txtChi.GetValue(),
			'honor_req':self.txtHonor.GetValue(),
			'cost':self.txtCost.GetValue(),
			'personal_honor':self.txtPH.GetValue(),
			'text':self.txtText.GetValue(),
		}
		
	def __init__(self, parent):
		#Open database and populate CardTypes
		proxdb = proxydb.ProxyDB()
		card_types = proxdb.get_all_card_types()
		for card_type in card_types:
			self.cardTypes[card_type.id] = card_type.type

		self.create_gui(parent)

	def create_gui(self, parent):
		#Create Dialog
		wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Create Card')
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		#Card Type Sizer & Combo
		sbsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Card Type'), wx.VERTICAL)
		
		self.cmbType = wx.ComboBox(self, size=(200,-1), style=wx.CB_READONLY)
		for type in self.cardTypes.values():
			self.cmbType.Append(type)
		self.cmbType.SetValue('Personality')
		sbsizer.Add(self.cmbType, 0, wx.CENTRE|wx.ALL|wx.EXPAND, 5)
		
		sizer.Add(sbsizer, 0, wx.EXPAND | wx.ALL, 5)

		#Card Data Sizer
		sbsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Card Data'), wx.VERTICAL)
		
		#Card Name
		sbsizer.Add(wx.StaticText(self, label='Name:'), 0, wx.ALL, 5)
		self.txtName = wx.TextCtrl(self)
		sbsizer.Add(self.txtName, 0, wx.CENTRE|wx.ALL|wx.EXPAND, 5)
		
		#Card Force & Chi
		sizer2 = wx.BoxSizer(wx.HORIZONTAL)
		self.txtForce = wx.TextCtrl(self, size=(48, -1))
		sizer2.Add(wx.StaticText(self, label='Force:'), 0, wx.CENTRE|wx.ALL, 5)
		sizer2.Add(self.txtForce, 0, wx.CENTRE|wx.ALL, 5)
		self.txtChi = wx.TextCtrl(self, size=(48, -1))
		sizer2.Add(wx.StaticText(self, label='Chi:'), 0, wx.CENTRE|wx.ALL, 5)
		sizer2.Add(self.txtChi, 0, wx.CENTRE|wx.ALL, 5)
		sbsizer.Add(sizer2, 0, wx.CENTRE|wx.ALL|wx.EXPAND, 0)

		#Card HR, GC, & PH
		sizer2 = wx.BoxSizer(wx.HORIZONTAL)
		self.txtHonor = wx.TextCtrl(self, size=(48, -1))
		sizer2.Add(wx.StaticText(self, label='HR:'), 0, wx.CENTRE|wx.ALL, 5)
		sizer2.Add(self.txtHonor, 0, wx.CENTRE|wx.ALL, 5)
		self.txtCost = wx.TextCtrl(self, size=(48, -1))
		sizer2.Add(wx.StaticText(self, label='GC:'), 0, wx.CENTRE|wx.ALL, 5)
		sizer2.Add(self.txtCost, 0, wx.CENTRE|wx.ALL, 5)
		self.txtPH = wx.TextCtrl(self, size=(48, -1))
		sizer2.Add(wx.StaticText(self, label='PH:'), 0, wx.CENTRE|wx.ALL, 5)
		sizer2.Add(self.txtPH, 0, wx.CENTRE|wx.ALL, 5)
		sbsizer.Add(sizer2, 0, wx.CENTRE|wx.ALL|wx.EXPAND, 0)
		
		#Card Text
		sbsizer.Add(wx.StaticText(self, label='Card text:'), 0, wx.ALL, 5)
		self.txtText = wx.TextCtrl(self, size=(-1, 100), style=wx.TE_MULTILINE)
		sbsizer.Add(self.txtText, 0, wx.CENTRE|wx.ALL|wx.EXPAND, 5)

		sizer.Add(sbsizer, 0, wx.EXPAND | wx.ALL, 5)

		buttonsizer = wx.StdDialogButtonSizer()
		self.btnSubmit = wx.Button(self, wx.ID_OK, 'Create')
		self.btnSubmit.SetDefault()
		self.btnCancel = wx.Button(self, wx.ID_CANCEL)
		buttonsizer.Add(self.btnSubmit, 1, wx.EXPAND|wx.ALL, 5)
		buttonsizer.Add(self.btnCancel, 1, wx.EXPAND|wx.ALL, 5)
		buttonsizer.Realize()
		
		sizer.Add(buttonsizer, 0, wx.EXPAND | wx.ALL, 0)
		self.SetSizer(sizer)
		sizer.Fit(self)

class full_create_proxy_dialog(wx.Dialog):
	cardTypes = {}
	cardSets = {}

	def __init__(self, parent):
		#Open database and populate CardTypes
		proxdb = proxydb.ProxyDB()
		card_types = proxdb.get_all_card_types()
		for card_type in card_types:
			self.cardTypes[card_type.id] = card_type.type
		card_sets = proxdb.get_all_sets()
		for card_set in card_sets:
			self.cardSets[card_set.id] = card_set.name

		#Load GUI
		self.create_gui(parent)	

	def get_cardtype(self):
		return self.cardTypes[self.cmbType.GetValue()]
	
	def get_set(self):
		return self.cardSets[self.cmbSet.GetValue()]

	def get_stats(self):
		return {
			'type':self.get_cardtype(),
			'set':self.get_set(),
			'name':self.txtName.GetValue(),
			'force':self.txtForce.GetValue(),
			'chi':self.txtChi.GetValue(),
			'honor_req':self.txtHonor.GetValue(),
			'cost':self.txtCost.GetValue(),
			'personal_honor':self.txtPH.GetValue(),
			'text':self.txtText.GetValue(),
			'artist':self.txtArtist.GetValue(),
		}
		
	def create_gui(self, parent):
		#Create Dialog
		wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Create Card')
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		#Card Type Sizer & Combo
		sbsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Card Type'), wx.VERTICAL)
		
		self.cmbType = wx.ComboBox(self, size=(200,-1), style=wx.CB_READONLY)
		for type in self.cardTypes.values():
			self.cmbType.Append(type)
		self.cmbType.SetValue('Personality')
		sbsizer.Add(self.cmbType, 0, wx.CENTRE|wx.ALL|wx.EXPAND, 5)
		
		sizer.Add(sbsizer, 0, wx.EXPAND | wx.ALL, 5)


		#Card Set Sizer & Combo
		sbsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Card Set'), wx.VERTICAL)
		
		self.cmbType = wx.ComboBox(self, size=(200,-1), style=wx.CB_READONLY)
		for set in self.cardSets.values():
			self.cmbType.Append(set)
		sbsizer.Add(self.cmbType, 0, wx.CENTRE|wx.ALL|wx.EXPAND, 5)
		
		sizer.Add(sbsizer, 0, wx.EXPAND | wx.ALL, 5)

		#Card Data Sizer
		sbsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Card Data'), wx.VERTICAL)
		
		#Card Name
		sbsizer.Add(wx.StaticText(self, label='Name:'), 0, wx.ALL, 5)
		self.txtName = wx.TextCtrl(self)
		sbsizer.Add(self.txtName, 0, wx.CENTRE|wx.ALL|wx.EXPAND, 5)
		
		#Card Force & Chi
		sizer2 = wx.BoxSizer(wx.HORIZONTAL)
		self.txtForce = wx.TextCtrl(self, size=(48, -1))
		sizer2.Add(wx.StaticText(self, label='Force:'), 0, wx.CENTRE|wx.ALL, 5)
		sizer2.Add(self.txtForce, 0, wx.CENTRE|wx.ALL, 5)
		self.txtChi = wx.TextCtrl(self, size=(48, -1))
		sizer2.Add(wx.StaticText(self, label='Chi:'), 0, wx.CENTRE|wx.ALL, 5)
		sizer2.Add(self.txtChi, 0, wx.CENTRE|wx.ALL, 5)
		sbsizer.Add(sizer2, 0, wx.CENTRE|wx.ALL|wx.EXPAND, 0)

		#Card HR, GC, & PH
		sizer2 = wx.BoxSizer(wx.HORIZONTAL)
		self.txtHonor = wx.TextCtrl(self, size=(48, -1))
		sizer2.Add(wx.StaticText(self, label='HR:'), 0, wx.CENTRE|wx.ALL, 5)
		sizer2.Add(self.txtHonor, 0, wx.CENTRE|wx.ALL, 5)
		self.txtCost = wx.TextCtrl(self, size=(48, -1))
		sizer2.Add(wx.StaticText(self, label='GC:'), 0, wx.CENTRE|wx.ALL, 5)
		sizer2.Add(self.txtCost, 0, wx.CENTRE|wx.ALL, 5)
		self.txtPH = wx.TextCtrl(self, size=(48, -1))
		sizer2.Add(wx.StaticText(self, label='PH:'), 0, wx.CENTRE|wx.ALL, 5)
		sizer2.Add(self.txtPH, 0, wx.CENTRE|wx.ALL, 5)
		sbsizer.Add(sizer2, 0, wx.CENTRE|wx.ALL|wx.EXPAND, 0)
		
		#Card Text
		sbsizer.Add(wx.StaticText(self, label='Card text:'), 0, wx.ALL, 5)
		self.txtText = wx.TextCtrl(self, size=(-1, 100), style=wx.TE_MULTILINE)
		sbsizer.Add(self.txtText, 0, wx.CENTRE|wx.ALL|wx.EXPAND, 5)

		#Card Artist
		sbsizer.Add(wx.StaticText(self, label='Artist:'), 0, wx.ALL, 5)
		self.txtArtist = wx.TextCtrl(self)
		sbsizer.Add(self.txtArtist, 0, wx.CENTRE|wx.ALL|wx.EXPAND, 5)

		sizer.Add(sbsizer, 0, wx.EXPAND | wx.ALL, 5)

		#TODO: Add file browser for image selection

		buttonsizer = wx.StdDialogButtonSizer()
		self.btnSubmit = wx.Button(self, wx.ID_OK, 'Create')
		self.btnSubmit.SetDefault()
		self.btnCancel = wx.Button(self, wx.ID_CANCEL)
		buttonsizer.Add(self.btnSubmit, 1, wx.EXPAND|wx.ALL, 5)
		buttonsizer.Add(self.btnCancel, 1, wx.EXPAND|wx.ALL, 5)
		buttonsizer.Realize()
		
		sizer.Add(buttonsizer, 0, wx.EXPAND | wx.ALL, 0)
		self.SetSizer(sizer)
		sizer.Fit(self)

#Use for testing
if __name__ == "__main__":
	app = wx.App(False)
	frame = wx.Frame(None)
	frame.Show()
	dlg = full_create_proxy_dialog(frame)
	dlg.ShowModal()
	app.MainLoop()