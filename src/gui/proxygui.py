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
"""
	Proxy GUI module for Egg of P'an Ku.

author: Ryan Karetas
file: proxygui.py
date: 21 Jul 2014
"""

import wx

#Local Imports
from db import proxydb

class CreateCardDialog(wx.Dialog):
	cardTypes = {}
	
	def GetType(self):
		return self.cardTypes[self.cmbType.GetValue()]
	
	def GetStats(self):
		return {
			'type':self.GetType(),
			'name':self.txtName.GetValue(),
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
		card_types = proxdb.get_card_types()
		for card_type in card_types:
			self.cardTypes[card_type[1]] = card_type[0]

		wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Create Card')
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		
		sbsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Card Type'), wx.VERTICAL)
		
		self.cmbType = wx.ComboBox(self, size=(200,-1), style=wx.CB_READONLY)
		for type in self.cardTypes:
			self.cmbType.Append(type)
		self.cmbType.SetValue('Personality')
		sbsizer.Add(self.cmbType, 0, wx.CENTRE|wx.ALL|wx.EXPAND, 5)
		
		sizer.Add(sbsizer, 0, wx.EXPAND | wx.ALL, 5)


		sbsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Card Data'), wx.VERTICAL)
		
		sbsizer.Add(wx.StaticText(self, label='Name:'), 0, wx.ALL, 5)
		self.txtName = wx.TextCtrl(self)
		sbsizer.Add(self.txtName, 0, wx.CENTRE|wx.ALL|wx.EXPAND, 5)
		
		sizer2 = wx.BoxSizer(wx.HORIZONTAL)
		self.txtForce = wx.TextCtrl(self, size=(48, -1))
		sizer2.Add(wx.StaticText(self, label='Force:'), 0, wx.CENTRE|wx.ALL, 5)
		sizer2.Add(self.txtForce, 0, wx.CENTRE|wx.ALL, 5)
		self.txtChi = wx.TextCtrl(self, size=(48, -1))
		sizer2.Add(wx.StaticText(self, label='Chi:'), 0, wx.CENTRE|wx.ALL, 5)
		sizer2.Add(self.txtChi, 0, wx.CENTRE|wx.ALL, 5)
		sbsizer.Add(sizer2, 0, wx.CENTRE|wx.ALL|wx.EXPAND, 0)

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