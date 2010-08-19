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
"""Egg of Pan Ku module."""


from xmlsettings import settings
#from settings import settings

import cPickle
import sys
import os
import webbrowser
import socket
import wx
import logging
import database
import canvas
import playfield
import game
import netcore
import dragdrop
import deck
import preview
import settings_ui
import deckpanel
import deckedit
import dbimport
import subprocess

from guids import *

logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s %(levelname)s %(message)s',
					filename='eopk.log',
					filemode='w')

LinkClickEvent, EVT_LINK_CLICK = wx.lib.newevent.NewEvent()
CreatedCards = []  # A mapping helper for the 'Create card' menu.


class CreateCardDialog(wx.Dialog):
	cardTypes = {
		'Personality':'personality',
		'Follower':'follower',
		'Item':'item',
		'Region':'region',
		'Holding':'holding',
	}
	
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
	
	
class ConnectDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Connect to host')
		
		sbDeck = wx.StaticBox(self, -1, 'Host Address')
		sbsizer = wx.StaticBoxSizer(sbDeck, wx.HORIZONTAL)
		
		self.txtHostname = wx.TextCtrl(self, size=(120,-1))
		self.txtHostname.SetValue(settings.gamehost)
		self.txtHostPort = wx.TextCtrl(self, size=(48,-1))
		self.txtHostPort.SetValue(str(settings.gameport))
		
		sbsizer.Add(wx.StaticText(self, label='Hostname:'), 0, wx.CENTRE|wx.ALL, 5)
		sbsizer.Add(self.txtHostname, 1, wx.CENTRE|wx.ALL, 5)
		sbsizer.Add(wx.StaticText(self, label='Port:'), 0, wx.CENTRE|wx.ALL, 5)
		sbsizer.Add(self.txtHostPort, 0, wx.CENTRE|wx.ALL, 5)
		
		buttonsizer = wx.StdDialogButtonSizer()
		self.btnSubmit = wx.Button(self, wx.ID_OK, 'Connect')
		self.btnSubmit.SetDefault()
		self.btnCancel = wx.Button(self, wx.ID_CANCEL)
		buttonsizer.Add(self.btnSubmit, 1, wx.EXPAND|wx.ALL, 5)
		buttonsizer.Add(self.btnCancel, 1, wx.EXPAND|wx.ALL, 5)
		buttonsizer.Realize()
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(sbsizer, 0, wx.EXPAND | wx.ALL, 5)
		sizer.Add(buttonsizer, 0, wx.EXPAND | wx.ALL, 0)
		self.SetSizer(sizer)
		sizer.Fit(self)

#-----------------------------------
# Added 08-23-2008 by PCW
# This is the Game Match Service Connection Dialog
#-----------------------------------
class GameMatchConnectDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Connect to Game Match Service')
		
		sbDeck = wx.StaticBox(self, -1, 'Game Match Service')
		sbsizer = wx.StaticBoxSizer(sbDeck, wx.HORIZONTAL)
		
		self.txtUserName = wx.TextCtrl(self, size=(120,-1))
		self.txtUserName.SetValue(settings.matchuser)
		self.txtPassword = wx.TextCtrl(self, size=(120,-1))
		self.txtPassword.SetValue(str(settings.matchpassword))
		
		sbsizer.Add(wx.StaticText(self, label='Username:'), 0, wx.CENTRE|wx.ALL, 5)
		sbsizer.Add(self.txtUserName, 1, wx.CENTRE|wx.ALL, 5)
		sbsizer.Add(wx.StaticText(self, label='Password:'), 0, wx.CENTRE|wx.ALL, 5)
		sbsizer.Add(self.txtPassword, 0, wx.CENTRE|wx.ALL, 5)
		
		buttonsizer = wx.StdDialogButtonSizer()
		self.btnSubmit = wx.Button(self, wx.ID_OK, 'Find Game')
		self.btnSubmit.SetDefault()
		self.btnCancel = wx.Button(self, wx.ID_CANCEL)
		buttonsizer.Add(self.btnSubmit, 1, wx.EXPAND|wx.ALL, 5)
		buttonsizer.Add(self.btnCancel, 1, wx.EXPAND|wx.ALL, 5)
		buttonsizer.Realize()
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(sbsizer, 0, wx.EXPAND | wx.ALL, 5)
		sizer.Add(buttonsizer, 0, wx.EXPAND | wx.ALL, 0)
		self.SetSizer(sizer)
		sizer.Fit(self)
		
class AddTokenDialog(wx.Dialog):
	def __init__(self, parent, title='Add Tokens', token=None):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, title, size=(240, 160))
		
		sbDeck = wx.StaticBox(self, -1, 'Tokens')
		sbsizer = wx.StaticBoxSizer(sbDeck, wx.HORIZONTAL)
		
		sbsizer.Add(wx.StaticText(self, label='Token type:'), 0, wx.CENTRE|wx.ALL, 5)
		
		if token is None:
			self.txtTokenType = wx.TextCtrl(self, size=(120, -1))
			sbsizer.Add(self.txtTokenType, 1, wx.CENTRE|wx.ALL, 5)
		else:
			self.token = token
			sbsizer.Add(wx.StaticText(self, label=token), 0, wx.CENTRE|wx.ALL, 5)
		
		self.txtTokenNumber = wx.SpinCtrl(self, size=(48, -1), value='1')
		sbsizer.Add(wx.StaticText(self, label='Number:'), 0, wx.CENTRE|wx.ALL, 5)
		sbsizer.Add(self.txtTokenNumber, 0, wx.CENTRE|wx.ALL, 5)
		
		buttonsizer = wx.StdDialogButtonSizer()
		self.btnSubmit = wx.Button(self, wx.ID_OK)
		self.btnSubmit.SetDefault()
		self.btnCancel = wx.Button(self, wx.ID_CANCEL)
		buttonsizer.Add(self.btnSubmit, 1, wx.EXPAND|wx.ALL, 5)
		buttonsizer.Add(self.btnCancel, 1, wx.EXPAND|wx.ALL, 5)
		buttonsizer.Realize()
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(sbsizer, 0, wx.EXPAND | wx.ALL, 5)
		sizer.Add(buttonsizer, 0, wx.EXPAND | wx.ALL, 0)
		self.SetSizer(sizer)
		sizer.Fit(self)
		
		if token is not None:
			self.txtTokenNumber.SetSelection(0, -1)
	
	def GetToken(self):
		try:
			return self.token
		except AttributeError:
			return self.txtTokenType.GetValue()
	
	def GetNumber(self):
		return int(self.txtTokenNumber.GetValue())
	

class AddMarkerDialog(wx.Dialog):

	MarkerTypes =  {
		'Crab':'crab',
		'Crane':'crane',
		'Dragon':'dragon',
		'Imperial':'imperial',
		'Lion':'lion',
		'Mantis':'mantis',
		'Phoenix':'phoenix',
		'Scorpion':'scorpion',
		'Shadowlands':'shadowlands',
		'Spider':'spider',
		'Unicorn':'unicorn',
		'Unaligned':'imperial',
		'Generic':'generic'
	}		
	
	def __init__(self, parent, title='Add Markers', token=None):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, title, size=(240, 160))
		
		sbDeck = wx.StaticBox(self, -1, 'Markers')
		sbsizer = wx.StaticBoxSizer(sbDeck, wx.HORIZONTAL)
		
		if token is None:
			self.txtMarkerType = wx.TextCtrl(self, size=(120, -1))
			sbsizer.Add(self.txtMarkerType, 1, wx.CENTRE|wx.ALL, 5)

			self.cmbType = wx.ComboBox(self, size=(200,-1), style=wx.CB_READONLY)
			for type in self.MarkerTypes:
				self.cmbType.Append(type)

			self.cmbType.SetValue('Generic')
			sbsizer.Add(self.cmbType, 0, wx.CENTRE|wx.ALL|wx.EXPAND, 5)

		else:
			self.token = token
			sbsizer.Add(wx.StaticText(self, label=token), 0, wx.CENTRE|wx.ALL, 5)
		
		self.txtMarkerNumber = wx.SpinCtrl(self, size=(48, -1), value='1')
		sbsizer.Add(wx.StaticText(self, label='Number:'), 0, wx.CENTRE|wx.ALL, 5)
		sbsizer.Add(self.txtMarkerNumber, 0, wx.CENTRE|wx.ALL, 5)
		
		buttonsizer = wx.StdDialogButtonSizer()
		self.btnSubmit = wx.Button(self, wx.ID_OK)
		self.btnSubmit.SetDefault()
		self.btnCancel = wx.Button(self, wx.ID_CANCEL)
		buttonsizer.Add(self.btnSubmit, 1, wx.EXPAND|wx.ALL, 5)
		buttonsizer.Add(self.btnCancel, 1, wx.EXPAND|wx.ALL, 5)
		buttonsizer.Realize()
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(sbsizer, 0, wx.EXPAND | wx.ALL, 5)
		sizer.Add(buttonsizer, 0, wx.EXPAND | wx.ALL, 0)
		self.SetSizer(sizer)
		sizer.Fit(self)
		
		if token is not None:
			self.txtMarkerNumber.SetSelection(0, -1)
	
	def GetToken(self):
		try:
			return self.token
		except AttributeError:
			return self.txtMarkerType.GetValue()

	def GetTokenImage(self):
		try:
			if self.token is not None:
				return None
			else:
				tokenImage = self.MarkerTypes[self.cmbType.GetValue()]
				imagePath = tokenImage
				return imagePath

		except AttributeError:
				tokenImage = self.MarkerTypes[self.cmbType.GetValue()]
				imagePath = tokenImage
				return imagePath
	
	def GetNumber(self):
		return int(self.txtMarkerNumber.GetValue())

class HelpAboutDialog(wx.Dialog):
	def __init__(self,parent):
		self.getOptionalItems = True
		wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Egg of P\'an Ku Information', size=(400,300))
		sbDeck = wx.StaticBox(self, -1, 'About Egg')
		sbsizer = wx.StaticBoxSizer(sbDeck, wx.VERTICAL)
		aboutData = []
		
		aboutData.append(EOPK_APPNAME)
		aboutData.append('Version: %s\n' % EOPK_VERSION_STRING)
		aboutData.append(EOPK_COPYRIGHT)
		aboutData.append("\n%s %s" % (EOPK_APPNAME,EOPK_WARRANTY_TEXT))
		
		lblHelp = wx.StaticText(self, wx.ID_ANY, '\n'.join(aboutData))
		lblHelp.Wrap(300)
		sbsizer.Add(lblHelp, 0, wx.ALL | wx.ALIGN_CENTRE, 5)
		
	
		buttonsizer = wx.StdDialogButtonSizer()
		self.btnSubmit = wx.Button(self, wx.ID_OK, 'Okay')
		wx.EVT_BUTTON(self, wx.ID_OK, self.OnSubmit)
		self.btnSubmit.SetDefault()
		buttonsizer.Add(self.btnSubmit, 1, wx.EXPAND | wx.ALL | wx.ALIGN_CENTER, 5)
		buttonsizer.Realize()
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(sbsizer, 0, wx.EXPAND | wx.ALL, 5)
		sizer.Add(buttonsizer, 0, wx.EXPAND | wx.ALL | wx.ALIGN_CENTER, 0)
		self.SetSizer(sizer)
		sizer.Fit(self)
		
	def GetOptional(self):
		return self.getOptionalItems
		
	def OnSubmit(self, event):
		self.EndModal(wx.ID_OK)

class UpdateDialog(wx.Dialog):
	def __init__(self,parent):
		self.getOptionalItems = True
		wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Update Egg of P\'an Ku', size=(340,126))
		sbDeck = wx.StaticBox(self, -1, '')
		sbsizer = wx.StaticBoxSizer(sbDeck, wx.VERTICAL)
		lblDeck = wx.StaticText(self, wx.ID_ANY, 'Egg of P\'an Ku will close while the updates are installed. Please make sure you end all current games before running the update')
		lblDeck.Wrap(300)
		sbsizer.Add(lblDeck, 0, wx.ALL | wx.ALIGN_CENTRE, 5)
		
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(self, label='Optional:'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		
		self.chkCEHoldings = wx.CheckBox(self, label='Update optional files (cards.xml, card images, etc)')
		self.chkCEHoldings.SetValue(self.getOptionalItems)
		sizer.Add(self.chkCEHoldings , 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		sbsizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 5)
		
		buttonsizer = wx.StdDialogButtonSizer()
		self.btnCancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')
		self.btnSubmit = wx.Button(self, wx.ID_OK, 'Update')
		wx.EVT_BUTTON(self, wx.ID_OK, self.OnSubmit)
		self.btnSubmit.SetDefault()
		buttonsizer.Add(self.btnSubmit, 1, wx.EXPAND | wx.ALL, 5)
		buttonsizer.Add(self.btnCancel, 1, wx.EXPAND | wx.ALL, 5)
		buttonsizer.Realize()
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(sbsizer, 0, wx.EXPAND | wx.ALL, 5)
		sizer.Add(buttonsizer, 0, wx.EXPAND | wx.ALL, 0)
		self.SetSizer(sizer)
		sizer.Fit(self)
		
	def GetOptional(self):
		return self.getOptionalItems
		
	def OnSubmit(self, event):
		self.EndModal(wx.ID_OK)
		
class SubmitDeckDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Join Game', size=(340,126))
		
		sbDeck = wx.StaticBox(self, -1, 'Deck')
		sbsizer = wx.StaticBoxSizer(sbDeck, wx.VERTICAL)
		lblDeck = wx.StaticText(self, wx.ID_ANY, 'Select the deck you wish to play with. You can change your deck at any time before starting the game.')
		lblDeck.Wrap(300)
		self.fpDeck = wx.FilePickerCtrl(self, wx.ID_ANY, wildcard='L5R deck files (*.l5d)|*.l5d|All files (*.*)|*.*', path=settings.last_deck)
		sbsizer.Add(lblDeck, 0, wx.ALL | wx.ALIGN_CENTRE, 5)
		sbsizer.Add(self.fpDeck, 0, wx.EXPAND | wx.ALL | wx.ALIGN_CENTRE, 5)
		
		buttonsizer = wx.StdDialogButtonSizer()
		self.btnCancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')
		self.btnSubmit = wx.Button(self, wx.ID_OK, 'Submit Deck')
		wx.EVT_BUTTON(self, wx.ID_OK, self.OnSubmit)
		self.btnSubmit.SetDefault()
		buttonsizer.Add(self.btnSubmit, 1, wx.EXPAND | wx.ALL, 5)
		buttonsizer.Add(self.btnCancel, 1, wx.EXPAND | wx.ALL, 5)
		buttonsizer.Realize()
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(sbsizer, 0, wx.EXPAND | wx.ALL, 5)
		sizer.Add(buttonsizer, 0, wx.EXPAND | wx.ALL, 0)
		self.SetSizer(sizer)
		sizer.Fit(self)
	
	def GetDeckPath(self):
		return self.fpDeck.GetPath()
	
	def GetDeck(self):
		return self.deck
		
	def OnSubmit(self, event):
		try:
			self.deck = deck.Deck.load(file(self.GetDeckPath()))
		except deck.InvalidCardError, e:
			wx.MessageDialog(self, 'A card in the deck (%s) was not found in the card database.\n' \
				'This could be because your card database is outdated, missing some cards, or ' \
				'because the deck is invalid somehow.' % e.card, 'Deck Error', wx.ICON_ERROR).ShowModal()
			return
		except IOError:
			wx.MessageDialog(self, 'The specified deck file could not be opened.\nMake sure the path ' \
				'entered exists.', 'Deck Error', wx.ICON_ERROR).ShowModal()
			return

		if self.deck.NumDynasty() != 40 or self.deck.NumFate() != 40:
			if wx.MessageDialog(self, 'The submitted deck is not a standard 40/40 deck. Do you still want to use it?', 'Submit Deck', wx.ICON_QUESTION|wx.YES_NO).ShowModal() == wx.ID_NO:
				return

		self.EndModal(wx.ID_OK)

class ViewCardsDialog(wx.Dialog):
	def __init__(self, parent, id=wx.ID_ANY, title='', gameState=None, allowMove=True):
		wx.Dialog.__init__(self, parent, id, title)
		
		self.gameState = gameState
		self.allowMove = allowMove

		# List
		id = wx.NewId()
		self.lstCards = wx.ListCtrl(self, id=id, size=(230, 400), style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES)
		self.lstCards.InsertColumn(0, "Name", wx.LIST_FORMAT_LEFT, 190)
		wx.EVT_LIST_BEGIN_DRAG(self, id, self.OnListDrag)
		wx.EVT_LIST_ITEM_SELECTED(self, id, self.OnListClick)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.lstCards, 1, wx.EXPAND | wx.ALL, 5)
		self.SetSizer(sizer)
		sizer.Fit(self)
		
	def OnListClick(self, event):
		cgid = event.GetData()
		card = self.gameState.FindCard(cgid)
		try:
			wx.FindWindowById(ID_CARD_PREVIEW).SetCard(card.data.id)
		except AttributeError:
			wx.FindWindowById(ID_CARD_PREVIEW).SetFacedown(card)
		
	def OnListDrag(self, event):
		if self.allowMove:
			faceUp = not wx.GetKeyState(wx.WXK_SHIFT)
			top = not wx.GetKeyState(wx.WXK_ALT)
			
			cgid = event.GetData()
			data = dragdrop.CardDropData(cgid=cgid, x=0, y=0, top=top, faceUp=faceUp)
			src = wx.DropSource(self)
			src.SetData(data)
			result = src.DoDragDrop(True)

class PeekDialog(ViewCardsDialog):
	def __init__(self, parent, id=wx.ID_ANY, title='', gameState=None, cgids=[]):
		ViewCardsDialog.__init__(self, parent, id, title, gameState)


		#added by PCW 1/6/2009
		wx.EVT_LIST_ITEM_RIGHT_CLICK(self, id, self.OnCardRightClick)
		wx.EVT_MENU(self,ID_MNU_FATEDECKPOPUP_DECK_TOP,self.OnMenuCardDeckTop)
		wx.EVT_MENU(self,ID_MNU_FATEDECKPOPUP_DECK_BOTTOM,self.OnMenuCardDeckBottom)
		self.cgid = 0
		self.contextCard = None
		
		self.cards = [gameState.FindCard(cgid) for cgid in cgids]
		for card in self.cards:
			idx = self.lstCards.InsertStringItem(0, card.GetName() + (' (dead)' if card.dead else ''))
			self.lstCards.SetItemData(idx, card.cgid)
		
		netcore.EVT_CLIENT_MOVE_CARD(parent, self.OnCardMove)
		netcore.EVT_CLIENT_ZONE_SHUFFLED(parent, self.OnShuffleZone)
		wx.EVT_CLOSE(self, self.OnClose)

	def OnCardRightClick(self, event):
		"""handler for when a user right clicks a card in the deck preview dialog"""
		self.cgid = event.GetData()
		self.contextCard = self.gameState.FindCard(self.cgid)

		deckname = ''
		if self.contextCard.IsDynasty():
			deckname = 'Dynasty'
		else:
			deckname = 'Fate'

		cardmenu = wx.Menu()
		cardmenu.Append(ID_MNU_FATEDECKPOPUP_DECK_TOP, 'Put on top of %s deck' % (deckname))
		cardmenu.Append(ID_MNU_FATEDECKPOPUP_DECK_BOTTOM, 'Put on bottom of %s deck' % (deckname))
		self.PopupMenu(cardmenu)

	def OnMenuCardDeckTop(self, event):
		"""Puts a card on the top of the appropriate deck"""
		gamezone = None
		if self.contextCard.IsDynasty():
			gamezone = game.ZONE_DECK_DYNASTY
		else:
			gamezone = game.ZONE_DECK_FATE
			
		wx.FindWindowById(ID_MAIN_WINDOW).client.Send(netcore.Msg('move-card', cgid=self.cgid, pid=self.gameState.localPlayer.pid, zid=gamezone, top=True))
		
	def OnMenuCardDeckBottom(self, event):
		"""Puts a card on the bottom of the appropriate deck"""
		gamezone = None
		if self.contextCard.IsDynasty():
			gamezone = game.ZONE_DECK_DYNASTY
		else:
			gamezone = game.ZONE_DECK_FATE

		wx.FindWindowById(ID_MAIN_WINDOW).client.Send(netcore.Msg('move-card', cgid=self.cgid, pid=self.gameState.localPlayer.pid, zid=gamezone, top=False))
		
	def OnClose(self, event):
		self.GetParent().Unbind(netcore.EVT_CLIENT_MOVE_CARD)  # Why does this work!?
		self.GetParent().Unbind(netcore.EVT_CLIENT_ZONE_SHUFFLED)
		self.Destroy()
		
	def OnCardMove(self, event):
		# When a card has moved, we might need to update our list.
		if event.card in self.cards:  # A card has left this view.
			idx = self.lstCards.FindItemData(-1, event.card.cgid)
			self.lstCards.DeleteItem(idx)
		event.Skip()
	
	def OnShuffleZone(self, event):
		# If this zone is ever shuffled, the dialog's contents are invalidated.
		for card in self.cards:
			if card.location is self.gameState.FindZone(event.pid, event.zid):
				self.Close()
				break
		event.Skip()

class ViewFocusPoolDialog(ViewCardsDialog):
	def __init__(self, parent, id=wx.ID_ANY, title='', gameState=None):
		ViewCardsDialog.__init__(self, parent, id, title, gameState)

		wx.EVT_MENU(self, ID_MNU_FOCUSPOPUP_DECK_TOP, self.OnMenuCardDeckTop)
		wx.EVT_MENU(self, ID_MNU_FOCUSPOPUP_DECK_BOTTOM, self.OnMenuCardDeckBottom)

		self.lstCards.SetColumnWidth(0, self.lstCards.GetColumnWidth(0) - 48)
		self.lstCards.InsertColumn(1, "FV", wx.LIST_FORMAT_CENTRE, 48)
		self.lstCards.SetDropTarget(dragdrop.CardDropTarget(self.OnDragData))

		#Added by PCW 1/5/2009
		#Issue 19 - adding right click menu to put card on bottom
		wx.EVT_LIST_ITEM_RIGHT_CLICK(self, id, self.OnFocusCardRightClick)
		
		netcore.EVT_CLIENT_MOVE_CARD(parent, self.OnCardMove)
		wx.EVT_CLOSE(self, self.OnClose)
		self.cgid = 0
		self.contextCard = None

	def OnClose(self, event):
		# Move remaining cards to bottom of fate deck.
		for cgid in self.gameState.MyZone(game.ZONE_FOCUS_POOL):
			wx.FindWindowById(ID_MAIN_WINDOW).client.Send(netcore.Msg('move-card', cgid=cgid, pid=self.gameState.localPlayer.pid, zid=game.ZONE_DECK_FATE, top=False))
		self.GetParent().Unbind(netcore.EVT_CLIENT_MOVE_CARD)  # Why does this work!?
		self.Destroy()
	
	def OnCardMove(self, event):
		# When a card has moved, we might need to update our list.
		if event.oldzone.zid == game.ZONE_FOCUS_POOL:  # A card has left this zone.
			idx = self.lstCards.FindItemData(-1, event.card.cgid)
			if idx != -1:
				self.lstCards.DeleteItem(idx)
		elif event.zone == self.gameState.MyZone(game.ZONE_FOCUS_POOL):  # A card is entering this zone.
			idx = self.lstCards.InsertStringItem(0, event.card.GetName())
			self.lstCards.SetStringItem(idx, 1, str(event.card.data.focus))
			self.lstCards.SetItemData(idx, event.card.cgid)
		event.Skip()

	def OnFocusCardRightClick(self, event):
		#added by PCW 1/5/2009
		self.cgid = event.GetData()
		self.contextCard = self.gameState.FindCard(self.cgid)
		focusmenu = wx.Menu()
		focusmenu.Append(ID_MNU_FOCUSPOPUP_DECK_TOP, 'Put on top of Fate deck')
		focusmenu.Append(ID_MNU_FOCUSPOPUP_DECK_BOTTOM, 'Put on bottom of Fate deck')
		self.PopupMenu(focusmenu)
		
	def OnListDrag(self, event):
		# Different from default; always drag face-down.
		top = not wx.GetKeyState(wx.WXK_ALT)
		cgid = event.GetData()
		data = dragdrop.CardDropData(cgid=cgid, x=0, y=0, faceUp=False, top=top)
		src = wx.DropSource(self)
		src.SetData(data)
		result = src.DoDragDrop(True)

	def OnMenuCardDeckTop(self, event):
		"""Handle moving a card to the top of the fate deck from the focus pool """
		wx.FindWindowById(ID_MAIN_WINDOW).client.Send(netcore.Msg('move-card', cgid=self.cgid, pid=self.gameState.localPlayer.pid, zid=game.ZONE_DECK_FATE, top=True))
		
	def OnMenuCardDeckBottom(self, event):
		"""Handle moving a card to the bottom of the fate deck from the focus pool """
		wx.FindWindowById(ID_MAIN_WINDOW).client.Send(netcore.Msg('move-card', cgid=self.cgid, pid=self.gameState.localPlayer.pid, zid=game.ZONE_DECK_FATE, top=False))

	def OnDragData(self, x, y, dragdata):
		"""Handle a drag-n-drop operation."""
		card = self.gameState.FindCard(dragdata.cgid)
		card.Isolate()
		wx.FindWindowById(ID_MAIN_WINDOW).client.Send(netcore.Msg('move-card', cgid=dragdata.cgid, pid=self.gameState.localPlayer.pid, zid=game.ZONE_FOCUS_POOL, top=True, faceup=dragdata.faceUp))
		self.Refresh()

class ViewDeckDialog(ViewCardsDialog):
	def __init__(self, parent, id=wx.ID_ANY, title='', gameState=None, zone=None, allowMove=True):
		ViewCardsDialog.__init__(self, parent, id, title, gameState, allowMove)
		
		self.zone = zone
		self.skipShuffle = False
		
		for cgid in self.zone:
			card = self.gameState.FindCard(cgid)
			idx = self.lstCards.InsertStringItem(0, self.NameCard(card))
			self.lstCards.SetItemData(idx, cgid)
	
		netcore.EVT_CLIENT_MOVE_CARD(parent, self.OnCardMove)
		netcore.EVT_CLIENT_ZONE_SHUFFLED(parent, self.OnShuffleZone)
		netcore.EVT_CLIENT_SET_CARD_PROPERTY(parent, self.OnPropertyChange)
		wx.EVT_CLOSE(self, self.OnClose)
	
	def NameCard(self, card):
		name = card.GetName()
		if card.dead:
			if card.dishonored:
				name += ' (dead, dishonored)'
			else:
				name += ' (dead)'		
		try:
			if card.data.type == 'holdings' and 'Legacy' in card.data.text:
				name += ' (Legacy Holding)'
		except AttributeError:
			pass
		return name
		
	def OnClose(self, event):
		if not self.skipShuffle:
			wx.FindWindowById(ID_MAIN_WINDOW).client.Send(netcore.Msg('shuffle-zone', zid=self.zone.zid))
		self.GetParent().Unbind(netcore.EVT_CLIENT_MOVE_CARD)  # Why does this work!?
		self.GetParent().Unbind(netcore.EVT_CLIENT_ZONE_SHUFFLED)
		self.GetParent().Unbind(netcore.EVT_CLIENT_SET_CARD_PROPERTY)
		self.Destroy()


	def OnPropertyChange(self, event):
		if event.property == 'dead' or event.property == "dishonored":
			idx = self.lstCards.FindItemData(-1, event.cgid)
			self.lstCards.SetStringItem(idx, 0, self.NameCard(self.gameState.FindCard(event.cgid)))
		event.Skip()
		
	def OnCardMove(self, event):
		# When a card has moved, we might need to update our list.
		if event.oldzone == self.zone:  # A card has left this zone.
			idx = self.lstCards.FindItemData(-1, event.card.cgid)
			self.lstCards.DeleteItem(idx)
		elif event.zone == self.zone:  # A card is entering this zone.
			name = card.GetName()
			if card.dead:
				if card.dishonored:
					name += ' (dead, dishonored)'
			else:
				name += ' (dead)'
			if event.top:
				
				idx = self.lstCards.InsertStringItem(0, name)
				self.lstCards.SetItemData(idx, event.card.cgid)
			else:
				idx = self.lstCards.InsertStringItem(-1, name)
				self.lstCards.SetItemData(idx, event.card.cgid)
		event.Skip()
	
	def OnShuffleZone(self, event):
		# If this zone is ever shuffled, the dialog's contents are invalidated.
		if event.zid == self.zone.zid and event.pid == self.zone.owner.pid:
			self.skipShuffle = True  # Don't need to shuffle again.
			self.Close()
		event.Skip()

class ViewDynastyDiscardDialog(ViewDeckDialog):
	def __init__(self, *args, **kwargs):
		ViewDeckDialog.__init__(self, *args, **kwargs)
		wx.EVT_LIST_ITEM_RIGHT_CLICK(self, self.lstCards.GetId(), self.OnListRightClick)
		wx.EVT_MENU(self, ID_MNU_CARDPOPUP_MARK_DEAD, self.OnMarkDead)
		wx.EVT_MENU(self, ID_MNU_CARDPOPUP_MARK_DISCARDED, self.OnMarkDiscarded)
		wx.EVT_MENU(self, ID_MNU_CARDPOPUP_MARK_REHONOR, self.OnRehonor)
	
	def OnMarkDead(self, evt):
		wx.FindWindowById(ID_MAIN_WINDOW).client.Send(netcore.Msg('set-card-property', cgid=self.card.cgid, property='dead', value=True))
		
	def OnMarkDiscarded(self, evt):
		wx.FindWindowById(ID_MAIN_WINDOW).client.Send(netcore.Msg('set-card-property', cgid=self.card.cgid, property='dead', value=False))

	def OnRehonor(self, evt):
		wx.FindWindowById(ID_MAIN_WINDOW).client.Send(netcore.Msg('set-card-property', cgid=self.card.cgid, property='dishonored', value=False))
		
	def OnListRightClick(self, evt):
		self.card = self.gameState.FindCard(evt.GetData())
		try:
			if self.card.data.type != 'personality':
				return
		except AttributeError:
			return
		
		menu = wx.Menu()
		if self.card.dead:
			menu.Append(ID_MNU_CARDPOPUP_MARK_DISCARDED, 'Mark discarded')
			if self.card.dishonored:
				menu.Append(ID_MNU_CARDPOPUP_MARK_REHONOR, 'Rehonor')
		else:
			menu.Append(ID_MNU_CARDPOPUP_MARK_DEAD, 'Mark dead')
		self.PopupMenu(menu)
	
class ChatCtrl(wx.TextCtrl):
	def __init__(self, parent, id = wx.ID_ANY):
		wx.TextCtrl.__init__(self, parent, id, style=wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_RICH|wx.TE_NOHIDESEL)
		wx.EVT_LEFT_DOWN(self, self.OnClick)
		wx.EVT_MOTION(self, self.OnMotion)
		self._link_attr = wx.TextAttr((0, 128, 0), font=wx.Font(-1, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False))
		self.card_links = []
		self.last_link = None

	def WriteToLogFile(self, text):
		if not settings.log_multiplayer_games:
			return
		if MainWindow.LogFile is None:
			return
		try:
			MainWindow.LogFile.write(text)
		except AttributeError, error:
			print error

	
	def AppendLine(self, text):
		new_links = []
		bits = text.split('#')

		newText = []
		db = database.get()
		while bits:
			# Append the first plain text bit
			tempStr=bits.pop(0)
			newText.append(tempStr)
			self.AppendText(tempStr)
			
			# If we still have bits, then the next one is a link of some sort.
			if bits:
				if bits[0].startswith('card:'):
					key = bits.pop(0)[5:]
					try:
						startpos = self.GetLastPosition()
						newText.append(db[key].name)
						self.AppendText(db[key].name)
						endpos = self.GetLastPosition()
						new_links.append((startpos, endpos, key))
					except KeyError:
						newText.append('<unknown card>')
						self.AppendText('<unknown card>')
				else:
					tempStr=bits.pop(0)
					newText.append('#%s' % tempStr)
					self.AppendText('#%s' % tempStr)
					if bits:  # In case there's a trailing one too; would be swallowed.
						newText.append('#')
						self.AppendText('#')
		
		# Finally, the line break.
		newText.append('\n')
		self.AppendText('\n')

		#And write  to chatbox (and Log)
		outputString = ''.join(newText)
		self.WriteToLogFile(text=outputString);
		
		# Mark up card links.
		if new_links:
			for start, end, key in new_links:
				self.SetStyle(start, end, self._link_attr)
			self.card_links.extend(new_links)
		
	def FindLink(self, position):
		result, column, row = self.HitTest(position)
		if result != wx.TE_HT_UNKNOWN:
			pos = self.XYToPosition(column, row)
			# Most links we're interested in will be near the bottom.
			for start, end, key in reversed(self.card_links):
				if start <= pos <= end:
					return start, end, key
		return None
		
	def OnClick(self, event):
		link = self.FindLink(event.GetPosition())
		if link is not None:
			wx.PostEvent(self, LinkClickEvent(key=link[2]))
			return
		event.Skip()
	
	def OnMotion(self, event):
		if self.FindLink(event.GetPosition()) is not None:
			self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
		else:
			self.SetCursor(wx.NullCursor)
		event.Skip()


class MainWindow(wx.Frame):
	"""Main game window."""
	
	# Client list constants.
	CLI_COLUMN_NAME = 0
	CLI_COLUMN_HONOR = 1
	CLI_COLUMN_HAND = 2
	
	LogFile = None
	
	def __init__(self, parent, id=wx.ID_ANY, title=None):
		# Basic initialization
		style = wx.DEFAULT_FRAME_STYLE
		if settings.maximize:
			style |= wx.MAXIMIZE
		wx.Frame.__init__(self, parent, id, title, size=settings.mainwindow_size, style=style)
		
		#set server and client attributes
		self.server = None
		self.client = None
		
		# Splitter hand/playfield
		splitterHorzMid = wx.SplitterWindow(self, -1, style=wx.CLIP_CHILDREN|wx.SP_3D)
		
		# Left side
		splitterLeft = wx.SplitterWindow(splitterHorzMid, -1, style=wx.CLIP_CHILDREN|wx.SP_3D)
		panelDecksHand = wx.Panel(splitterLeft)
		
		self.lstFateHand = wx.ListCtrl(panelDecksHand, ID_LIST_HAND, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES)
		self.lstFateHand.InsertColumn(0, 'Name', wx.LIST_FORMAT_LEFT, 120)
		self.lstFateHand.InsertColumn(1, 'GC', wx.LIST_FORMAT_CENTRE, 32)
		self.lstFateHand.InsertColumn(2, 'FV', wx.LIST_FORMAT_CENTRE, 32)
		wx.EVT_LIST_BEGIN_DRAG(self, ID_LIST_HAND, self.OnFateHandDrag)
		wx.EVT_LIST_ITEM_RIGHT_CLICK(self, ID_LIST_HAND, self.OnFateHandRightClick)
		wx.EVT_LIST_ITEM_SELECTED(self, ID_LIST_HAND, self.OnFateHandClick)
		self.lstFateHand.SetDropTarget(dragdrop.CardDropTarget(self.OnFateDragToHand))
		
		# Decks
		self.deckDynasty = deckpanel.DynastyDeckPanel(panelDecksHand)
		deckpanel.EVT_DECK_DROP_CARD(self.deckDynasty, self.OnDragDynastyDeck)
		wx.EVT_MENU(self.deckDynasty, ID_MNU_PILEPOPUP_SEARCH, self.OnMenuDynastySearch)
		wx.EVT_MENU(self.deckDynasty, ID_MNU_PILEPOPUP_SHUFFLE, self.OnMenuDynastyShuffle)
		
		self.discardDynasty = deckpanel.DynastyDiscardPanel(panelDecksHand)
		deckpanel.EVT_DECK_DROP_CARD(self.discardDynasty, self.OnDragDynastyDiscard)
		wx.EVT_MENU(self.discardDynasty, ID_MNU_PILEPOPUP_SEARCH, self.OnMenuDynastyDiscardSearch)
		
		self.deckFate = deckpanel.FateDeckPanel(panelDecksHand)
		deckpanel.EVT_DECK_DROP_CARD(self.deckFate, self.OnDragFateDeck)
		wx.EVT_MENU(self.deckFate, ID_MNU_PILEPOPUP_SEARCH, self.OnMenuFateSearch)
		wx.EVT_MENU(self.deckFate, ID_MNU_PILEPOPUP_SHUFFLE, self.OnMenuFateShuffle)
		
		self.discardFate = deckpanel.FateDiscardPanel(panelDecksHand)
		deckpanel.EVT_DECK_DROP_CARD(self.discardFate, self.OnDragFateDiscard)
		wx.EVT_MENU(self.discardFate, ID_MNU_PILEPOPUP_SEARCH, self.OnMenuFateDiscardSearch)

		self.rfgZone = deckpanel.RemovedFromGamePanel(panelDecksHand)
		deckpanel.EVT_DECK_DROP_CARD(self.rfgZone, self.OnDragRFG)
		wx.EVT_MENU(self.rfgZone, ID_MNU_PILEPOPUP_SEARCH, self.OnMenuRemovedSearch)

		deckSizer = wx.BoxSizer(wx.HORIZONTAL)
		deckSizer.Add(self.rfgZone, 0, wx.ALL, 2)
		deckSizer.Add(self.discardDynasty, 0, wx.ALL, 2)
		deckSizer.Add(self.deckDynasty, 0, wx.ALL, 2)
		deckSizer.Add(self.deckFate, 0, wx.ALL, 2)
		deckSizer.Add(self.discardFate, 0, wx.ALL, 2)
		
		leftSizer = wx.BoxSizer(wx.VERTICAL)
		leftSizer.Add(deckSizer, 0, wx.CENTRE|wx.ALL, 0)
		leftSizer.Add(self.lstFateHand, 1, wx.EXPAND|wx.ALL, 0)
		panelDecksHand.SetSizer(leftSizer)
		
		# Preview pane
		self.cardPreview = preview.CardPreviewWindow(splitterLeft, id=ID_CARD_PREVIEW)
		
		# Right side
		splitterChat = wx.SplitterWindow(splitterHorzMid, style=wx.CLIP_CHILDREN|wx.SP_3D)
		
		# Chat box
		splitterClients = wx.SplitterWindow(splitterChat, style=wx.CLIP_CHILDREN|wx.SP_3D)
		
		panelChat = wx.Panel(splitterClients)
		self.txtChat = ChatCtrl(panelChat)
		self.txtChatInput = wx.TextCtrl(panelChat, ID_IRC_CHAT_ENTRY, style=wx.TE_PROCESS_ENTER)
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.txtChat, 1, wx.EXPAND | wx.ALL, 1)
		sizer.Add(self.txtChatInput, 0, wx.EXPAND | wx.ALL, 1)
		panelChat.SetSizer(sizer)
		EVT_LINK_CLICK(self.txtChat, self.OnChatClickLink)
		
		# Clients list
		iglL5R = wx.ImageList(16, 16)
		iglL5R.AddWithColourMask(wx.Bitmap('images/icosm_family_honor.png'), (255, 255, 255))
		iglL5R.AddWithColourMask(wx.Bitmap('images/icosm_hand.png'), (255, 255, 255))
		iglL5R.AddWithColourMask(wx.Bitmap('images/icosm_fate.png'), (255, 255, 255))
		iglL5R.AddWithColourMask(wx.Bitmap('images/icosm_favor.png'), (255, 255, 255))
		
		self.lstClients = wx.ListCtrl(splitterClients, ID_CLIENT_LIST, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES)
		self.lstClients.AssignImageList(iglL5R, wx.IMAGE_LIST_SMALL)
		self.lstClients.InsertColumn(self.CLI_COLUMN_NAME, "Name", wx.LIST_FORMAT_LEFT, 120)
		honorColumn = wx.ListItem()
		honorColumn.SetImage(0)
		honorColumn.SetWidth(32)
		honorColumn.SetAlign(wx.LIST_FORMAT_CENTRE)
		self.lstClients.InsertColumnItem(self.CLI_COLUMN_HONOR, honorColumn)
		handSizeColumn = wx.ListItem()
		handSizeColumn.SetImage(1)
		handSizeColumn.SetWidth(32)
		handSizeColumn.SetAlign(wx.LIST_FORMAT_CENTRE)
		self.lstClients.InsertColumnItem(self.CLI_COLUMN_HAND, handSizeColumn)
		wx.EVT_LIST_ITEM_RIGHT_CLICK(self, self.lstClients.GetId(), self.OnClientRightClick)

		# Main display, which is an OGL context.
		self.gameTable = playfield.Table(splitterChat, -1)
		playfield.EVT_PLAYFIELD_DOUBLE_CLICK_CARD(self.gameTable, self.OnDoubleClickCard)
		playfield.EVT_PLAYFIELD_WHEEL_CLICK_CARD(self.gameTable, self.OnWheelClickCard)
		playfield.EVT_PLAYFIELD_RIGHT_CLICK_CARD(self.gameTable, self.OnRightClickCard)
		playfield.EVT_PLAYFIELD_CARD_DROP(self.gameTable, self.OnCardDragToPlay)
		playfield.EVT_PLAYFIELD_CARD_HOVER(self.gameTable, self.OnCardHover)
		playfield.EVT_PLAYFIELD_CARD_ATTACH(self.gameTable, self.OnCardAttach)
		playfield.EVT_SEARCH_PILE(self.gameTable, self.SearchOtherPile)
		
		# Splitter, cont'd
		splitterChat.SplitHorizontally(self.gameTable, splitterClients, -120)
		splitterLeft.SplitHorizontally(self.cardPreview, panelDecksHand, -200)
		splitterHorzMid.SplitVertically(splitterLeft, splitterChat, 200)
		splitterClients.SplitVertically(panelChat, self.lstClients, -220)
		splitterChat.SetSashGravity(0.8)
		splitterHorzMid.SetMinimumPaneSize(168)
		splitterLeft.SetMinimumPaneSize(200)
		splitterLeft.SetSashGravity(0.5)
		splitterClients.SetMinimumPaneSize(64)
		splitterClients.SetSashGravity(1.0)
		
		self.CreateStatusBar()
		self.SetupToolbars()
		self.SetupMenus()
		
		# Create menu.
		# Icon. If running py2exe'd on windows, we should try that first.
		if hasattr(sys, 'frozen'):
			try:
				import win32api
				self.SetIcon(wx.Icon(win32api.GetModuleFileName(win32api.GetModuleHandle(None)), wx.BITMAP_TYPE_ICO))
			except ImportError:
				self.SetIcon(wx.Icon('icon.ico', wx.BITMAP_TYPE_ICO))
		else:
			self.SetIcon(wx.Icon('icon.ico', wx.BITMAP_TYPE_ICO))
		
		# Server/client callbacks.
		netcore.EVT_CLIENT_REJECTED(self, self.OnClientRejected)
		netcore.EVT_CLIENT_CHAT(self, self.OnClientChat)
		netcore.EVT_CLIENT_DISCONNECTED(self, self.OnClientDisconnect)
		netcore.EVT_CLIENT_CLIENT_QUIT(self, self.OnClientQuit)
		netcore.EVT_CLIENT_CLIENT_NAMES(self, self.OnClientNames)
		netcore.EVT_CLIENT_NAME(self, self.OnClientNameChanged)
		netcore.EVT_CLIENT_DECK_SUBMITTED(self, self.OnClientDeckSubmit)
		netcore.EVT_CLIENT_DECK_UNSUBMITTED(self, self.OnClientDeckUnsubmit)
		netcore.EVT_CLIENT_GAME_SETUP(self, self.OnClientGameSetup)
		netcore.EVT_CLIENT_GAME_START(self, self.OnClientGameBegin)
		netcore.EVT_CLIENT_MOVE_CARD(self, self.OnClientCardMove)
		netcore.EVT_CLIENT_SET_CARD_PROPERTY(self, self.OnClientCardPropertyChanged)
		netcore.EVT_CLIENT_ZONE_SHUFFLED(self, self.OnClientZoneShuffled)
		netcore.EVT_CLIENT_VIEW_ZONE(self, self.OnClientViewZone)
		netcore.EVT_CLIENT_SET_FAMILY_HONOR(self, self.OnClientFamilyHonor)
		netcore.EVT_CLIENT_SET_TOKENS(self, self.OnClientSetTokens)
		#Added by PCW 10-04-2008
		netcore.EVT_CLIENT_SET_MARKERS(self, self.OnClientSetMarkers)
		netcore.EVT_CLIENT_CREATE_CARD(self, self.OnClientCreateCard)
		netcore.EVT_CLIENT_NEW_CARD(self, self.OnClientNewCard)
		
		netcore.EVT_CLIENT_PEEK_OPPONENT_CARD(self, self.OnClientPeekOpponentCard)
		netcore.EVT_CLIENT_PEEK_CARD(self, self.OnClientPeekCard)
		
		netcore.EVT_CLIENT_FLIP_COIN(self, self.OnClientFlipCoin)
		netcore.EVT_CLIENT_ROLL_DIE(self, self.OnClientRollDie)
		netcore.EVT_CLIENT_FAVOR(self, self.OnClientFavor)
		netcore.EVT_CLIENT_SHOW_ZONE(self, self.OnClientShowZone)

		netcore.EVT_GAMEMATCH_NO_OPPONENT(self, self.OnGameMatchNoOpponent)
		netcore.EVT_GAMEMATCH_OPPONENT_FOUND(self, self.OnGameMatchOpponentFound)
		netcore.EVT_GAMEMATCH_LOGGED_IN(self, self.OnGameMatchLoggedIn)
		
		# Show ourselves
		self.CenterOnScreen()
		self.Show(True)
		
		#
		db = database.get()
		self.PrintToChat("%s %s \nVersion %s" \
			"\n\n%s\n" % (EOPK_APPNAME,EOPK_UNOFFICIAL_TEXT, EOPK_VERSION_STRING,  EOPK_COPYRIGHT ))
		self.PrintToChat("%s %s" % (EOPK_APPNAME, EOPK_WARRANTY_TEXT))
		self.PrintToChat("Database %s, containing %d cards." % (db.date, len(db)))
		self.PrintToChat("----------")
		


	def CheckForUpdates(self, updateOptional):
		updatePath = "eggupdater.exe -wait -startegg"
		if updateOptional:
			updatePath = updatePath + ' -optional'
			
		p = subprocess.Popen(updatePath, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		self.Close()

	def SetupToolbars(self):
		toolbar = self.CreateToolBar()
		
		# System tools
		toolbar.AddSeparator()
		toolbar.AddLabelTool(ID_MNU_HOST, 'Host table', wx.Bitmap('images/tlb_icon_host.png'),
			shortHelp='Host table', longHelp='Host a game table.')
		self.Bind(wx.EVT_TOOL, self.OnMenuHost, id=ID_MNU_HOST)
		
		toolbar.AddLabelTool(ID_MNU_CONNECT, 'Connect', wx.Bitmap('images/tlb_icon_connect.png'),
			shortHelp='Connect', longHelp='Connect to a host to play a game.')
		self.Bind(wx.EVT_TOOL, self.OnMenuConnect, id=ID_MNU_CONNECT)
		
		toolbar.AddLabelTool(ID_MNU_DISCONNECT, 'Disconnect', wx.Bitmap('images/tlb_icon_disconnect.png'),
			shortHelp='Disconnect', longHelp='Disconnect from the current host.')
		self.Bind(wx.EVT_TOOL, self.OnMenuDisconnect, id=ID_MNU_DISCONNECT)
		
		toolbar.AddSeparator()
		toolbar.AddLabelTool(ID_MNU_JOIN_GAME, 'Join game', wx.Bitmap('images/tlb_icon_join_game.png'),
			shortHelp='Join game', longHelp='Submit a deck and play in the next game.')
		self.Bind(wx.EVT_TOOL, self.OnMenuSubmitDeck, id=ID_MNU_JOIN_GAME)
		
		toolbar.AddLabelTool(ID_MNU_LEAVE_GAME, 'Leave game', wx.Bitmap('images/tlb_icon_leave_game.png'),
			shortHelp='Leave game', longHelp='Retract your current deck, leaving the next game.')
		self.Bind(wx.EVT_TOOL, self.OnMenuLeaveGame, id=ID_MNU_LEAVE_GAME)
		
		toolbar.AddLabelTool(ID_MNU_START_GAME, 'Start game', wx.Bitmap('images/tlb_icon_start.png'),
			shortHelp='Start game', longHelp='Start the game.')
		self.Bind(wx.EVT_TOOL, self.OnMenuStartGame, id=ID_MNU_START_GAME)
		
		# Game tools
		toolbar.AddSeparator()
		toolbar.AddLabelTool(ID_MNU_STRAIGHTEN_ALL, 'Straighten all', wx.Bitmap('images/tlb_icon_straighten_all.png'),
			shortHelp='Straighten all', longHelp='Straighten all cards you control in play.')
		self.Bind(wx.EVT_TOOL, self.OnMenuStraightenAll, id=ID_MNU_STRAIGHTEN_ALL)

		#Toolbar Icon for Remove all Markers
		#Added by PCW 10/10/2008
		toolbar.AddLabelTool(ID_MNU_REMOVE_MARKERS, 'Remove all markers', wx.Bitmap('images/tlb_icon_remove_markers.png'),
			shortHelp='Remove All Markers', longHelp='Remove all the markers from cards.')
		self.Bind(wx.EVT_TOOL, self.OnMenuRemoveAllMarkers, id=ID_MNU_REMOVE_MARKERS)
		
		toolbar.AddSeparator()
		toolbar.AddLabelTool(ID_MNU_FAMILY_HONOR_SET, 'Set family honor', wx.Bitmap('images/tlb_icon_honor.png'),
			shortHelp='Set family honor', longHelp='Set your family honor to some value.')
		self.Bind(wx.EVT_TOOL, self.OnMenuSetHonor, id=ID_MNU_FAMILY_HONOR_SET)
		
		toolbar.AddLabelTool(ID_MNU_FAMILY_HONOR_INC, 'Increase family honor', wx.Bitmap('images/tlb_icon_honor_add.png'),
			shortHelp='Increase family honor', longHelp='Increase your family honor by 1.')
		self.Bind(wx.EVT_TOOL, self.OnMenuIncHonor, id=ID_MNU_FAMILY_HONOR_INC)
		
		toolbar.AddLabelTool(ID_MNU_FAMILY_HONOR_DEC, 'Decrease family honor', wx.Bitmap('images/tlb_icon_honor_sub.png'),
			shortHelp='Decrease family honor', longHelp='Decrease your family honor by 1.')
		self.Bind(wx.EVT_TOOL, self.OnMenuDecHonor, id=ID_MNU_FAMILY_HONOR_DEC)
		
		toolbar.AddSeparator()
		toolbar.AddLabelTool(ID_MNU_TAKE_FAVOR, 'Take Imperial Favor', wx.Bitmap('images/tlb_icon_favor.png'),
			shortHelp='Take Imperial Favor', longHelp='Take the Imperial Favor.')
		self.Bind(wx.EVT_TOOL, self.OnMenuTakeFavor, id=ID_MNU_TAKE_FAVOR)
		
		toolbar.AddLabelTool(ID_MNU_DISCARD_FAVOR, 'Discard Imperial Favor', wx.Bitmap('images/tlb_icon_favor_dis.png'),
			shortHelp='Discard Imperial Favor', longHelp='Discard the Imperial Favor.')
		self.Bind(wx.EVT_TOOL, self.OnMenuDiscardFavor, id=ID_MNU_DISCARD_FAVOR)
		
		toolbar.AddSeparator()
		toolbar.AddLabelTool(ID_MNU_FATE_DRAW, 'Draw Fate card', wx.Bitmap('images/tlb_icon_fate_draw.png'),
			shortHelp='Draw Fate card', longHelp='Draw the top card of your fate deck.')
		self.Bind(wx.EVT_TOOL, self.OnMenuFateDraw, id=ID_MNU_FATE_DRAW)
		
		toolbar.AddLabelTool(ID_MNU_FATE_DRAW_X, 'Draw several Fate cards', wx.Bitmap('images/tlb_icon_fate_draw_x.png'),
			shortHelp='Draw several Fate cards', longHelp='Draw several cards from your fate deck.')
		self.Bind(wx.EVT_TOOL, self.OnMenuFateDrawX, id=ID_MNU_FATE_DRAW_X)
		
		toolbar.AddLabelTool(ID_MNU_HAND_REVEAL_X_RANDOM, 'Reveal random cards', wx.Bitmap('images/tlb_icon_fate_reveal_random.png'),
			shortHelp='Reveal random cards', longHelp='Reveal a number of cards from your hand at random.')
		self.Bind(wx.EVT_TOOL, self.OnMenuHandRevealRandomX, id=ID_MNU_HAND_REVEAL_X_RANDOM)
		
		toolbar.AddLabelTool(ID_MNU_HAND_REVEAL, 'Reveal hand', wx.Bitmap('images/tlb_icon_fate_reveal.png'),
			shortHelp='Reveal hand', longHelp='Reveal your hand to the other players.')
		self.Bind(wx.EVT_TOOL, self.OnMenuHandReveal, id=ID_MNU_HAND_REVEAL)
		
		toolbar.AddSeparator()
		toolbar.AddLabelTool(ID_MNU_COIN_FLIP, 'Flip coin', wx.Bitmap('images/tlb_icon_flip_coin.png'),
			shortHelp='Flip coin', longHelp='Flip a coin and announce the result.')
		self.Bind(wx.EVT_TOOL, self.OnMenuFlipCoin, id=ID_MNU_COIN_FLIP)
		
		toolbar.AddLabelTool(ID_MNU_ROLL_DICE, 'Roll die', wx.Bitmap('images/tlb_icon_roll_die.png'),
			shortHelp='Roll die', longHelp='Roll an n-sided die and announce the result.')
		self.Bind(wx.EVT_TOOL, self.OnMenuRollDie, id=ID_MNU_ROLL_DICE)
		
		toolbar.AddSeparator()
		toolbar.AddLabelTool(ID_MNU_FOCUS_CREATE, 'Create focus pool', wx.Bitmap('images/tlb_icon_focuspool.png'),
			shortHelp='Create focus pool', longHelp='Create a focus pool from the top three cards of your fate deck.')
		self.Bind(wx.EVT_TOOL, self.OnMenuCreateFocusPool, id=ID_MNU_FOCUS_CREATE)
		
		toolbar.Realize()
	
	def SetupMenus(self):
		mnuFile = wx.Menu()
		self.mnuFile = mnuFile
		mnuFile.Append(ID_MNU_HOST, "&Host Table\tCtrl+K",  "Host a new game table that other players can connect to.")

		#Added 8/23/08 PCW
		#Removed until I get the GameMatch Server working 10/04/2008 PCW
		#mnuFile.Append(ID_MNU_FIND_GAME_MATCH, "&Game Matcher\t",  "Use the online game matching service to find another player.")

		mnuFile.Append(ID_MNU_CONNECT, "&Connect to Table...",  "Connect to game table hosted elsewhere.")
		mnuFile.Append(ID_MNU_DISCONNECT, "&Disconnect",  "Disconnect from the current game.")
		mnuFile.AppendSeparator()
		mnuFile.Append(ID_MNU_JOIN_GAME, "&Join Game...\tCtrl+J",  "Sit down to play with a deck.")
		#mnuFile.Append(ID_MNU_CHANGE_DECK, "Change &Deck...",  "Switch your deck for another one.")
		mnuFile.Append(ID_MNU_LEAVE_GAME, "&Leave Game",  "Leave the current game.")
		mnuFile.Append(ID_MNU_START_GAME, "Start &Game\tCtrl+S",  "Start the game session.")
		mnuFile.AppendSeparator()
		mnuFile.Append(ID_MNU_PREFERENCES, "&Preferences...",  "Change application settings.")
		mnuFile.AppendSeparator()
		mnuFile.Append(ID_MNU_DECK_EDIT, "Launch Deck &Editor",  "Open the deck editor where you can build or edit decks.")
		mnuFile.AppendSeparator()
		mnuFile.Append(ID_MNU_LAUNCH_EGGUPDATER, "Check for updates",  "Launch EggUpdater to check for application updates.")
		mnuFile.AppendSeparator()
		mnuFile.Append(ID_MNU_EXIT, "E&xit", "")
		
		mnuGame = wx.Menu()
		self.mnuGame = mnuGame
		mnuGame.Append(ID_MNU_STRAIGHTEN_ALL, "&Straighten All\tCtrl+U", "Straighten all your cards in play.")
		mnuGame.Append(ID_MNU_REMOVE_MARKERS, "Remove All &Markers\tCtrl+M", "Remove all the markers your cards.")
		mnuGame.AppendSeparator()
		mnuGame.Append(ID_MNU_FAMILY_HONOR_SET, "Set Family &Honor...\tCtrl+H", "Set your current family honor directly to some value.")
		mnuGame.Append(ID_MNU_FAMILY_HONOR_INC, "Increase Family Honor\tCtrl+Up", "Increase your current family honor by 1.")
		mnuGame.Append(ID_MNU_FAMILY_HONOR_DEC, "Decrease Family Honor\tCtrl+Down", "Decrease your current family honor by 1.")
		mnuGame.AppendSeparator()
		mnuGame.Append(ID_MNU_TAKE_FAVOR, "Take the Imperial Fa&vor", "Take the Imperial Favor.")
		mnuGame.Append(ID_MNU_DISCARD_FAVOR, "&Discard the Imperial Fa&vor", "Discard the Imperial Favor.")
		mnuGame.AppendSeparator()
		mnuGame.Append(ID_MNU_COIN_FLIP, "&Flip Coin\tCtrl+F", "Flips a coin and announces the result.")
		mnuGame.Append(ID_MNU_ROLL_DICE, "&Roll Die\tCtrl+R", "Rolls an N-sided die and announces the result.")
		mnuGame.AppendSeparator()
		
		self.mnuCreateCard = wx.Menu()
		self.mnuCreateCard.Append(ID_MNU_CREATE_CARD_CUSTOM, 'New...', 'Create a new kind of card and put it into play.')
		
		mnuGame.AppendMenu(ID_MNU_CREATE_CARD, "Create Card", self.mnuCreateCard, "Create a card to be put into play.")
		
		mnuDynasty = wx.Menu()
		self.mnuDynasty = mnuDynasty
		mnuDynasty.Append(ID_MNU_DYN_SHUFFLE, "Shuffle", "Shuffle your dynasty deck.")
		mnuDynasty.AppendSeparator()
		mnuDynasty.Append(ID_MNU_DYN_SEARCH, "Search...", "Look through your dynasty deck.")
		mnuDynasty.AppendSeparator()
		mnuDynasty.Append(ID_MNU_DYN_LOOK_TOP, "Look at top cards...", "Look at the top N cards of your dynasty deck.")
		mnuDynasty.Append(ID_MNU_DYN_LOOK_BOTTOM, "Look at bottom cards...", "Look at the bottom N cards of your dynasty deck.")
		
		mnuFate = wx.Menu()
		self.mnuFate = mnuFate
		mnuFate.Append(ID_MNU_FATE_DRAW, "&Draw\tCtrl+D", "Draw the top card of your fate deck.")
		mnuFate.Append(ID_MNU_FATE_DRAW_X, "D&raw several...\tCtrl+Shift+D", "Draw several cards from your fate deck.")
		mnuFate.AppendSeparator()
		mnuFate.Append(ID_MNU_FATE_SHUFFLE, "&Shuffle", "Shuffle your fate deck.")
		mnuFate.AppendSeparator()
		mnuFate.Append(ID_MNU_FATE_SEARCH, "S&earch...", "Look through your fate deck.")
		mnuFate.AppendSeparator()
		mnuFate.Append(ID_MNU_FATE_LOOK_TOP, "Look at &top cards...", "Look at the top N cards of your fate deck.")
		mnuFate.Append(ID_MNU_FATE_LOOK_BOTTOM, "Look at &bottom cards...", "Look at the bottom N cards of your fate deck.")
		mnuFate.AppendSeparator()
		mnuFate.Append(ID_MNU_FOCUS_CREATE, 'Create focus &pool...\tCtrl+P', 'Create a focus pool from the top 3 cards of your fate deck.')
		
		mnuFateHand = wx.Menu()
		self.mnuFateHand = mnuFateHand
		mnuFateHand.Append(ID_MNU_HAND_REVEAL, "Reveal", "Reveal your fate hand.")
		mnuFateHand.Append(ID_MNU_HAND_REVEAL_RANDOM, "Reveal random card", "Reveal a random card from your fate hand.")
		mnuFateHand.Append(ID_MNU_HAND_REVEAL_X_RANDOM, "Reveal several random cards...", "Reveal several random cards from your fate hand.")
		mnuFateHand.AppendSeparator()
		mnuFateHand.Append(ID_MNU_HAND_DISCARD, "Discard", "Discard your entire fate hand.")
		mnuFateHand.Append(ID_MNU_HAND_DISCARD_RANDOM, "Discard random card", "Discard a random card from your fate hand.")
		
		mnuHelp = wx.Menu()
		self.mnuHelp = mnuHelp
		mnuHelp.Append(ID_MNU_HELP_ABOUT,"About", "Information about Egg of P'an Ku")
		mnuHelp.Append(ID_MNU_HELP_WEB,"Web Site", "Go to the Egg of P'an Ku website")
		mnuHelp.AppendSeparator()
		mnuHelp.Append(ID_MNU_HELP_DONATE,"Donate", "Donate via PayPal to the Egg of P'an Ku project")
		
		menuBar = wx.MenuBar()
		menuBar.Append(mnuFile, "&File")
		menuBar.Append(mnuGame, "&Game")
		menuBar.Append(mnuDynasty, "&Dynasty Deck")
		menuBar.Append(mnuFate, "F&ate Deck")
		menuBar.Append(mnuFateHand, "Fate &Hand")
		menuBar.Append(mnuHelp, "&Help")
		self.SetMenuBar(menuBar)
		
		# Disable Game, Dynasty, Fate, and Hand until we start a game.
		self.EnableGameMenus(False)
		
		# Disable irrelevant options in the File menu.
		menuBar.Enable(ID_MNU_DISCONNECT, False)
		menuBar.Enable(ID_MNU_JOIN_GAME, False)
		menuBar.Enable(ID_MNU_LEAVE_GAME, False)
		menuBar.Enable(ID_MNU_START_GAME, False)
		self.GetToolBar().EnableTool(ID_MNU_DISCONNECT, False)
		self.GetToolBar().EnableTool(ID_MNU_JOIN_GAME, False)
		self.GetToolBar().EnableTool(ID_MNU_LEAVE_GAME, False)
		self.GetToolBar().EnableTool(ID_MNU_START_GAME, False)
		
		# Set up menu callbacks.
		wx.EVT_MENU(self, ID_MNU_HOST, self.OnMenuHost)


		wx.EVT_MENU(self, ID_MNU_CONNECT, self.OnMenuConnect)

		#Added 8/23/08 PCW
		#Commented 10/04/08 until I get the server running
		#wx.EVT_MENU(self, ID_MNU_FIND_GAME_MATCH, self.OnMenuGameMatch)

		wx.EVT_MENU(self, ID_MNU_DISCONNECT, self.OnMenuDisconnect)
		wx.EVT_MENU(self, ID_MNU_CONNECT, self.OnMenuConnect)
		wx.EVT_MENU(self, ID_MNU_JOIN_GAME, self.OnMenuSubmitDeck)
		wx.EVT_MENU(self, ID_MNU_LEAVE_GAME, self.OnMenuLeaveGame)
		wx.EVT_MENU(self, ID_MNU_START_GAME, self.OnMenuStartGame)
		wx.EVT_MENU(self, ID_MNU_PREFERENCES, self.OnMenuPreferences)
		wx.EVT_MENU(self, ID_MNU_DECK_EDIT, self.OnMenuDeckEditor)
		wx.EVT_MENU(self, ID_MNU_LAUNCH_EGGUPDATER, self.OnMenuUpdateEgg)
		
		wx.EVT_MENU(self, ID_MNU_EXIT, self.OnMenuExit)
		
		wx.EVT_MENU(self, ID_MNU_FAMILY_HONOR_SET, self.OnMenuSetHonor)
		wx.EVT_MENU(self, ID_MNU_FAMILY_HONOR_INC, self.OnMenuIncHonor)
		wx.EVT_MENU(self, ID_MNU_FAMILY_HONOR_DEC, self.OnMenuDecHonor)
		wx.EVT_MENU(self, ID_MNU_TAKE_FAVOR, self.OnMenuTakeFavor)
		wx.EVT_MENU(self, ID_MNU_DISCARD_FAVOR, self.OnMenuDiscardFavor)
		wx.EVT_MENU(self, ID_MNU_STRAIGHTEN_ALL, self.OnMenuStraightenAll)
		wx.EVT_MENU(self, ID_MNU_CREATE_CARD_CUSTOM, self.OnMenuCreateCard)
		wx.EVT_MENU_RANGE(self, ID_MNU_CREATE_CARD_CUSTOM + 1, ID_MNU_CREATE_CARD_CUSTOM + 99, self.OnMenuCreateExistingCard)
		wx.EVT_MENU(self, ID_MNU_COIN_FLIP, self.OnMenuFlipCoin)
		wx.EVT_MENU(self, ID_MNU_ROLL_DICE, self.OnMenuRollDie)
		
		wx.EVT_MENU(self, ID_MNU_FATE_DRAW, self.OnMenuFateDraw)
		wx.EVT_MENU(self, ID_MNU_FATE_DRAW_X, self.OnMenuFateDrawX)
		wx.EVT_MENU(self, ID_MNU_FATE_SHUFFLE, self.OnMenuFateShuffle)
		wx.EVT_MENU(self, ID_MNU_FATE_LOOK_TOP, self.OnMenuFateLook)
		wx.EVT_MENU(self, ID_MNU_FATE_LOOK_BOTTOM, self.OnMenuFateLook)
		
		wx.EVT_MENU(self, ID_MNU_HAND_REVEAL, self.OnMenuHandReveal)
		wx.EVT_MENU(self, ID_MNU_HAND_REVEAL_RANDOM, self.OnMenuHandRevealRandom)
		wx.EVT_MENU(self, ID_MNU_HAND_REVEAL_X_RANDOM, self.OnMenuHandRevealRandomX)
		wx.EVT_MENU(self, ID_MNU_HAND_DISCARD, self.OnMenuHandDiscard)
		wx.EVT_MENU(self, ID_MNU_HAND_DISCARD_RANDOM, self.OnMenuHandDiscardRandom)
		
		wx.EVT_MENU(self, ID_MNU_DYN_SHUFFLE, self.OnMenuDynastyShuffle)
		wx.EVT_MENU(self, ID_MNU_DYN_SEARCH, self.OnMenuDynastySearch)
		wx.EVT_MENU(self, ID_MNU_DYN_LOOK_TOP, self.OnMenuDynastyLook)
		wx.EVT_MENU(self, ID_MNU_DYN_LOOK_BOTTOM, self.OnMenuDynastyLook)
		
		wx.EVT_MENU(self, ID_MNU_FOCUS_CREATE, self.OnMenuCreateFocusPool)
		
		wx.EVT_MENU(self,ID_MNU_HELP_ABOUT, self.OnMenuShowHelpAbout)
		wx.EVT_MENU(self,ID_MNU_HELP_WEB, self.OnMenuHelpWebSite)
		wx.EVT_MENU(self,ID_MNU_HELP_DONATE, self.OnMenuHelpDonate)
		
		wx.EVT_MENU(self, ID_MNU_CARDPOPUP_TAP, self.OnMenuCardTap)
		wx.EVT_MENU(self, ID_MNU_CARDPOPUP_FLIP, self.OnMenuCardFlip)
		wx.EVT_MENU(self, ID_MNU_CARDPOPUP_DISCARD, self.OnMenuCardDiscard)
		wx.EVT_MENU(self, ID_MNU_CARDPOPUP_KILL_DISCARD, self.OnMenuCardKillDiscard)
		wx.EVT_MENU(self, ID_MNU_CARDPOPUP_DECK_TOP, self.OnMenuCardDeckTop)
		wx.EVT_MENU(self, ID_MNU_CARDPOPUP_DECK_BOTTOM, self.OnMenuCardDeckBottom)
		
		wx.EVT_MENU(self, ID_MNU_CARDPOPUP_TOKEN_ADD_CUSTOM, self.OnMenuCardAddCustomToken)
		wx.EVT_MENU_RANGE(self, ID_MNU_CARDPOPUP_TOKEN_ADD, ID_MNU_CARDPOPUP_TOKEN_ADD + 99, self.OnMenuCardAddToken)
		wx.EVT_MENU_RANGE(self, ID_MNU_CARDPOPUP_TOKEN_REMOVE, ID_MNU_CARDPOPUP_TOKEN_REMOVE + 99, self.OnMenuCardRemoveToken)

		#Added by PCW 08/23/2008
		wx.EVT_MENU(self, ID_MNU_CARDPOPUP_MARKER_ADD_CUSTOM, self.OnMenuCardAddCustomMarker)
		wx.EVT_MENU_RANGE(self, ID_MNU_CARDPOPUP_MARKER_ADD, ID_MNU_CARDPOPUP_MARKER_ADD + 49, self.OnMenuCardAddMarker)
		wx.EVT_MENU_RANGE(self, ID_MNU_CARDPOPUP_MARKER_REMOVE, ID_MNU_CARDPOPUP_MARKER_REMOVE + 49, self.OnMenuCardRemoveMarker)

		wx.EVT_MENU_RANGE(self, ID_MNU_CARDPOPUP_CONTROL, ID_MNU_CARDPOPUP_CONTROL+49, self.OnMenuCardChangeControl)

		#Added by PCW 01/06/2009
		wx.EVT_MENU(self, ID_MNU_CARDPOPUP_PEEK_OPPONENT, self.OnMenuCardOpponentPeek)
		
		wx.EVT_MENU(self, ID_MNU_CARDPOPUP_PEEK, self.OnMenuCardPeek)
		wx.EVT_MENU(self, ID_MNU_CARDPOPUP_DISHONOR, self.OnMenuCardDishonor)
		wx.EVT_MENU(self, ID_MNU_CARDPOPUP_MOVE_TOP, self.OnMenuCardMoveTop)
		wx.EVT_MENU(self, ID_MNU_CARDPOPUP_MOVE_BOTTOM, self.OnMenuCardMoveBottom)
		
		wx.EVT_TEXT_ENTER(self, ID_IRC_CHAT_ENTRY, self.OnChatEntry)
		wx.EVT_CLOSE(self, self.OnClose)
		
	
	def PrintToChat(self, msg):
		#self.txtChat.AppendText(msg + "\n")
		self.txtChat.AppendLine(msg)
		
	def EnableGameMenus(self, enable=True):
		"""Enable or disable game functions that are only relevant in-game."""
		menuBar = self.GetMenuBar()
		for x in xrange(1, 5):
			menuBar.EnableTop(x, enable)
		
		# Tools too.
		self.GetToolBar().EnableTool(ID_MNU_STRAIGHTEN_ALL, enable)
		#added by PCW, 10/10/2008
		self.GetToolBar().EnableTool(ID_MNU_REMOVE_MARKERS,enable)
		self.GetToolBar().EnableTool(ID_MNU_FAMILY_HONOR_SET, enable)
		self.GetToolBar().EnableTool(ID_MNU_FAMILY_HONOR_INC, enable)
		self.GetToolBar().EnableTool(ID_MNU_FAMILY_HONOR_DEC, enable)
		self.GetToolBar().EnableTool(ID_MNU_TAKE_FAVOR, enable)
		self.GetToolBar().EnableTool(ID_MNU_DISCARD_FAVOR, enable)
		self.GetToolBar().EnableTool(ID_MNU_DISCARD_FAVOR, enable)
		self.GetToolBar().EnableTool(ID_MNU_FATE_DRAW, enable)
		self.GetToolBar().EnableTool(ID_MNU_FATE_DRAW_X, enable)
		self.GetToolBar().EnableTool(ID_MNU_HAND_REVEAL_X_RANDOM, enable)
		self.GetToolBar().EnableTool(ID_MNU_HAND_REVEAL, enable)
		self.GetToolBar().EnableTool(ID_MNU_ROLL_DICE, enable)
		self.GetToolBar().EnableTool(ID_MNU_COIN_FLIP, enable)
		self.GetToolBar().EnableTool(ID_MNU_FOCUS_CREATE, enable)
	
	def UpdateDecks(self):
		self.deckDynasty.UpdateTooltip()
		self.discardDynasty.UpdateTooltip()
		self.deckFate.UpdateTooltip()
		self.discardFate.UpdateTooltip()
		self.rfgZone.UpdateTooltip()
	
	#------------------------------------------------------------------------------------------------------------------------------------------------------------
	#
	# UI events.
	#
	#------------------------------------------------------------------------------------------------------------------------------------------------------------
	def OnClose(self, event):
		self.StopClient()
		self.StopServer()
		self.Destroy()
		settings.maximize = self.IsMaximized()
		if not settings.maximize:
			settings.mainwindow_size = self.GetSize().Get()
		
		settings.WriteSettingsFile()
		event.Skip()
	
	def OnMenuShowHelpAbout(self,event):
		dlg = HelpAboutDialog(self)
		dlg.ShowModal()
	
	def OnMenuHelpWebSite(self,event):
		webbrowser.open_new(EOPK_WEBSITE_URL)
	
	def OnMenuHelpDonate(self,event):
		webbrowser.open_new(EOPK_DONATE_URL)
	
	def OnMenuExit(self, event):
		self.Close()
	
	def OnMenuPreferences(self, event):
		settings_ui.SettingsDialog(self).ShowModal()
		
	def OnMenuDeckEditor(self, event):
		win = deckedit.MainWindow()

	def OnMenuUpdateEgg(self,event):
		dlg = UpdateDialog(self)
		if dlg.ShowModal() == wx.ID_OK:
			updateOptional = dlg.GetOptional
			self.CheckForUpdates(updateOptional)
	
	def OnMenuSetHonor(self, event):
		if self.client and self.client.Playing():
			dlg = wx.TextEntryDialog(self, 'What do you want to set your family honor to?', 'Set family honor', str(self.client.localPlayer.familyHonor))
			if dlg.ShowModal() == wx.ID_OK:
				self.client.Send(netcore.Msg('set-family-honor', honor=int(dlg.GetValue())))
		
	def OnMenuIncHonor(self, event):
		if self.client and self.client.Playing():
			self.client.Send(netcore.Msg('set-family-honor', honor=self.client.localPlayer.familyHonor + 1))
	
	def OnMenuDecHonor(self, event):
		if self.client and self.client.Playing():
			self.client.Send(netcore.Msg('set-family-honor', honor=self.client.localPlayer.familyHonor - 1))
	
	def OnMenuTakeFavor(self, event):
		if self.client and self.client.Playing():
			self.client.Send(netcore.Msg('take-favor'))
	
	def OnMenuDiscardFavor(self, event):
		if self.client and self.client.Playing():
			self.client.Send(netcore.Msg('discard-favor'))
		
	def OnMenuFlipCoin(self, event):
		if self.client and self.client.Playing():
			self.client.Send(netcore.Msg('flip-coin'))
	
	def OnMenuRollDie(self, event):
		if self.client and self.client.Playing():
			dlg = wx.TextEntryDialog(self, 'What size die should be rolled?', 'Roll die', '20')
			if dlg.ShowModal() == wx.ID_OK:
				self.client.Send(netcore.Msg('roll-die', size=int(dlg.GetValue())))
	
	def OnMenuStraightenAll(self, event):
		if self.client and self.client.Playing():
			zone = self.client.localPlayer.zones[game.ZONE_PLAY]
			for cgid in zone:
				card = self.client.gameState.FindCard(cgid)
				self.client.Send(netcore.Msg('set-card-property', cgid=card.cgid, property='tapped', value=False))
				for token in card.markers:
					marker = game.FindMarkerTemplate(game, token)
					self.client.Send(netcore.Msg('set-markers', cgid=card.cgid, token=marker.name, number=0, image=marker.image))
	
	def OnMenuCreateCard(self, event):
		if self.client and self.client.Playing():
			dlg = CreateCardDialog(self)
			if dlg.ShowModal() == wx.ID_OK:
				self.client.Send(netcore.Msg('create-card', **dlg.GetStats()))
	
	def OnMenuCreateExistingCard(self, event):
		if self.client and self.client.Playing():
			idx = event.GetId() - ID_MNU_CREATE_CARD_CUSTOM - 1
			self.client.Send(netcore.Msg('create-card', id=CreatedCards[idx]))
		
	def OnMenuFateDraw(self, event):
		if self.client and self.client.Playing():
			zone = self.client.localPlayer.zones[game.ZONE_DECK_FATE]
			if len(zone) > 0:
				self.client.Send(netcore.Msg('move-card', cgid=zone.TopCard(), pid=self.client.localPlayer.pid, zid=game.ZONE_HAND, top=True))
			else:
				self.PrintToChat('Your fate deck is empty.')
	
	def OnMenuFateDrawX(self, event):
		if self.client and self.client.Playing():
			dlg = wx.TextEntryDialog(self, 'How many cards do you want to draw?', 'Draw X cards', '1')
			if dlg.ShowModal() == wx.ID_OK:
				num = int(dlg.GetValue())
				if num <= 0:
					return
				zone = self.client.localPlayer.zones[game.ZONE_DECK_FATE]
				for cgid in reversed(zone.TopCards(num)):
					self.client.Send(netcore.Msg('move-card', cgid=cgid, pid=self.client.localPlayer.pid, zid=game.ZONE_HAND, top=True))
	
	def OnMenuFateShuffle(self, event):
		if self.client and self.client.Playing():
			self.client.Send(netcore.Msg('shuffle-zone', zid=game.ZONE_DECK_FATE))
	
	def OnMenuDynastyShuffle(self, event):
		if self.client:
			self.client.Send(netcore.Msg('shuffle-zone', zid=game.ZONE_DECK_DYNASTY))
	
	def OnClientRightClick(self, event):
		#mnu = wx.Menu()
		#mnu.Append(ID_MNU_CLIENT_IGNORE, 'Ignore')
		#self.lstClients.PopupMenu(mnu)
		pass
	
	def OnMenuHost(self, event):
		if self.client:
			dlg = wx.MessageDialog(self, 'You are already connected to a host.\nAre you sure you want to host a new game?', 'Host', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			if dlg.ShowModal() == wx.ID_NO:
				return
		
		self.StopClient()
		self.StopServer()
		self.StartServer()
		if not self.StartClient('localhost'):
			self.StopServer()
	
	def OnMenuConnect(self, event):
		if self.client:
			dlg = wx.MessageDialog(self, 'You are already connected to a host.\nAre you sure you want to connect to someone else?', 'Connect', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			if dlg.ShowModal() == wx.ID_NO:
				return
		
		dlg = ConnectDialog(self)
		if dlg.ShowModal() == wx.ID_OK:
			settings.gamehost = dlg.txtHostname.GetValue()
			try:
				port = int(dlg.txtHostPort.GetValue())
				
			except ValueError:
				port = netcore.DEFAULT_PORT
				
			settings.gameport=port
			settings.WriteSettingsFile()
			self.StopClient()
			self.StopServer()
			self.StartClient(settings.gamehost, settings.gameport)
	
	#---------------------------------------
	# Added 08-23-2008 by PCW
	# This is the menu event handler for connecting to the Game Match Service
	#---------------------------------------
	def OnMenuGameMatch(self,event):
		if self.client:
			dlg = wx.MessageDialog(self, 'You are already connected to a game via the Game Matching Service.\nAre you sure you want to connect to another?', 'Connect', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			if dlg.ShowModal() == wx.ID_NO:
				return

		#dlg= GameMatchConnectDialog(self)
		#if dlg.ShowModal() == wx.ID_OK:
		#settings.matchuser = dlg.txtUserName.GetValue()
		#settings.matchpassword = dlg.txtPassword.GetValue()
		self.StopClient()
		self.StopServer()
		self.StartGameMatchService()
		
	#--------------------------------------
	# End of Changes
	#--------------------------------------
	
	def OnMenuDisconnect(self, event):
		dlg = wx.MessageDialog(self, 'Disconnecting will terminate your current game.\nAre you sure you want to disconnect?', 'Disconnect', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		if dlg.ShowModal() == wx.ID_NO:
			return

		self.StopClient()
		self.StopServer()
		
	def OnMenuSubmitDeck(self, event):
		dlg = SubmitDeckDialog(self)
		if dlg.ShowModal() == wx.ID_OK:
			settings.last_deck = dlg.GetDeckPath()
			settings.WriteSettingsFile()
			self.client.SubmitDeck(dlg.GetDeck())
			self.GetMenuBar().Enable(ID_MNU_LEAVE_GAME, True)
			self.GetToolBar().EnableTool(ID_MNU_LEAVE_GAME, True)
	
	def OnMenuLeaveGame(self, event):
		self.client.UnsubmitDeck()
		self.GetMenuBar().Enable(ID_MNU_LEAVE_GAME, False)
		self.GetToolBar().EnableTool(ID_MNU_LEAVE_GAME, False)
		
	def OnMenuStartGame(self, event):	
		if not self.server:  # Only if we are the server
			return
		
		# Confirm dialog
		if self.server.gameState is not None and wx.MessageDialog(self, 'A game is already running. Do you want to start a new one?', \
			'Start Game', wx.ICON_QUESTION|wx.YES_NO).ShowModal() == wx.ID_NO:
			return

		if not any(client for client in self.server.clients if client.HasDeck()):
			wx.MessageDialog(self, 'There are no players ready to play. The game cannot start.', 'Start Game', wx.ICON_ERROR).ShowModal()
			return

		self.client.Send(netcore.Msg('discard-favor'))		
		self.server.RequestStartGame()
	
	def OnChatEntry(self, evt):
		intext = self.txtChatInput.GetValue()
		self.txtChatInput.SetValue('')
		
		if len(intext) == 0:
			pass
		elif intext[0] == '/':
			bits = intext.split(' ')
			if bits[0] == '/connect':
				if len(bits) == 2:
					self.StopClient()
					self.StopServer()
					self.StartClient(bits[1])
				else:
					self.PrintToChat('Usage: /connect <host>')
			elif bits[0] == '/host':
				if len(bits) == 1:
					self.StopClient()
					self.StopServer()
					self.StartServer()
					self.StartClient('localhost')
				else:
					self.PrintToChat('Usage: /host')
			elif bits[0] in ('/nick', '/name'):
				if not self.client:
					self.PrintToChat('Not connected.')
				elif len(bits) == 2:
					self.client.Send(netcore.Msg('name', value=bits[1]))
					settings.playername = bits[1]
					settings.WriteSettingsFile()
				else:
					self.PrintToChat('Usage: /nick <name>')
			else:
				self.PrintToChat('Unrecognized slash command \'' + bits[0][1:] + '\'')
		else:
			if self.client:
				self.client.Send(('chat', {'msg':intext}))
			else:
				self.PrintToChat('Not connected.')
	
	def OnFateHandDrag(self, evt):
		# TODO: Drag multiple cards.
		faceUp = not wx.GetKeyState(wx.WXK_SHIFT)
		top = not wx.GetKeyState(wx.WXK_ALT)
		
		cgid = evt.GetData()
		data = dragdrop.CardDropData(cgid=cgid, x=0, y=0, top=top, faceUp=faceUp)
		src = wx.DropSource(self)
		src.SetData(data)
		result = src.DoDragDrop(True)
	
	def OnFateHandClick(self, evt):
		"""React to the user clicking on a card in his hand."""
		idx = self.lstFateHand.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
		if idx == -1:
			print 'FAIL'
			return
		cgid = self.lstFateHand.GetItemData(idx)
		card = self.client.gameState.FindCard(cgid)
		try:
			self.cardPreview.SetCard(card.data.id)
		except AttributeError:
			pass
	
	def OnFateHandRightClick(self, evt):
		cgid = evt.GetData()
		self.contextCard = self.client.gameState.FindCard(cgid)
		cardmenu = wx.Menu()
		cardmenu.Append(ID_MNU_CARDPOPUP_DISCARD, 'Discard')
		cardmenu.AppendSeparator()
		cardmenu.Append(ID_MNU_CARDPOPUP_DECK_TOP, 'Put on top of deck')
		cardmenu.Append(ID_MNU_CARDPOPUP_DECK_BOTTOM, 'Put on bottom of deck')
		self.PopupMenu(cardmenu)
	
	def OnCardDragToPlay(self, event):
		"""React to a card being dragged into play from somewhere."""
		card = self.client.gameState.FindCard(event.cgid)
		
		params = {
			'cgid':event.cgid,
			'pid':self.client.localPlayer.pid,
			'zid':game.ZONE_PLAY,
			'x':event.x,
			'y':event.y,
			'top':True,
		}
		
		if card.location.zid == game.ZONE_PLAY:
			# If it didn't really move, don't make it move; it just causes trouble with Z-order.
			if event.x == card.x and event.y == card.y:
				return
			
			# Move all attached cards first.
			card.Detach()
			for idx, acard in enumerate(reversed(card.attached_cards)):
				self.client.Send(netcore.Msg('move-card', cgid=acard.cgid, pid=self.client.localPlayer.pid, \
					zid=game.ZONE_PLAY, x=event.x, y=event.y - 5 * (len(card.attached_cards) - idx), top=True))
		else:
			params['faceup'] = event.faceUp  # Respect drag status.
		
		self.client.Send(netcore.Msg('move-card', **params))
	
	def OnCardAttach(self, event):
		"""Card attachment handler."""
		# Unattach the card first.
		event.card.Detach()
		
		# Attach it to where it needs to go.
		event.card.attached_to = event.target
		event.target.attached_cards.append(event.card)
		
		# Finally, decide where it needs to be moved.
		self.client.Send(netcore.Msg('move-card', cgid=event.card.cgid, pid=self.client.localPlayer.pid, \
			zid=game.ZONE_PLAY, x=event.target.x, y=event.target.y - 5 * len(event.target.attached_cards), \
			top=False, faceup=event.faceUp))
		
	def OnFateDragToHand(self, x, y, dragdata):
		"""React to a card being dragged into the user's hand from somewhere."""
		card = self.client.gameState.FindCard(dragdata.cgid)
		
		if not card.IsFate():  # Make sure it's a fate card.
			return wx.DragNone
		
		card.Isolate()
		
		params = {}
		params['cgid'] = dragdata.cgid
		params['pid'] = self.client.localPlayer.pid
		params['zid'] = game.ZONE_HAND
		params['top'] = True
		self.client.Send(('move-card', params))
	
	def OnDragDynastyDeck(self, event):
		self.client.gameState.FindCard(event.cgid).Isolate()
		self.client.Send(netcore.Msg('move-card', cgid=event.cgid, pid=self.client.localPlayer.pid, zid=event.zid, top=event.top))
		
	def OnDragDynastyDiscard(self, event):
		self.client.gameState.FindCard(event.cgid).Isolate()
		self.client.Send(netcore.Msg('move-card', cgid=event.cgid, pid=self.client.localPlayer.pid, zid=event.zid, top=event.top))

	def OnDragFateDeck(self, event):
		self.client.gameState.FindCard(event.cgid).Isolate()
		self.client.Send(netcore.Msg('move-card', cgid=event.cgid, pid=self.client.localPlayer.pid, zid=event.zid, top=event.top))

	def OnDragFateDiscard(self, event):
		self.client.gameState.FindCard(event.cgid).Isolate()
		self.client.Send(netcore.Msg('move-card', cgid=event.cgid, pid=self.client.localPlayer.pid, zid=event.zid, top=event.top))

	def OnDragRFG(self, event):
		self.client.gameState.FindCard(event.cgid).Isolate()
		self.client.Send(netcore.Msg('move-card', cgid=event.cgid, pid=self.client.localPlayer.pid, zid=event.zid, top=event.top))

	def OnMenuDynastySearch(self, evt):
		"""React to the user wanting to search their dynasty deck."""
		self.client.Send(netcore.Msg('view-zone', pid=self.client.localPlayer.pid, zid=game.ZONE_DECK_DYNASTY))
		
	def OnMenuDynastyDiscardSearch(self, evt):
		"""React to the user wanting to search their dynasty discard."""
		dialog = ViewDynastyDiscardDialog(self,
			title='Your %s' % game.zoneNames[game.ZONE_DISCARD_DYNASTY], gameState = self.client.gameState,
			zone=self.client.gameState.FindZone(self.client.localPlayer.pid, game.ZONE_DISCARD_DYNASTY))
		dialog.Show()
		
	def OnMenuFateSearch(self, evt):
		"""React to the user wanting to search their fate deck."""
		self.client.Send(netcore.Msg('view-zone', pid=self.client.localPlayer.pid, zid=game.ZONE_DECK_FATE))

	def OnMenuFateDiscardSearch(self, evt):
		"""React to the user wanting to search their fate discard."""
		dialog = ViewDeckDialog(self,
			title='Your %s' % game.zoneNames[game.ZONE_DISCARD_FATE], gameState = self.client.gameState,
			zone=self.client.gameState.FindZone(self.client.localPlayer.pid, game.ZONE_DISCARD_FATE))
		dialog.Show()
		
	def SearchOtherPile(self, evt):
		"""Used when searching someone else's discards."""
		dialog = ViewDeckDialog(self,
			title='%s\'s %s' % (evt.player.name, game.zoneNames[evt.zid]), gameState = self.client.gameState,
			zone=self.client.gameState.FindZone(evt.player.pid, evt.zid), allowMove=False)
		dialog.Show()

	def OnMenuFateLook(self, event):
		if self.client and self.client.Playing():
			if event.GetId() == ID_MNU_FATE_LOOK_TOP:
				top = 'top'
			else:
				top = 'bottom'
			
			zone = self.client.gameState.MyZone(game.ZONE_DECK_FATE)
				
			dlg = wx.TextEntryDialog(self, 'How many cards do you want to look at?', 'Look at %s cards' % top, '1')
			if dlg.ShowModal() != wx.ID_OK:
				return
			
			numCards = min(len(zone), int(dlg.GetValue()))
			self.client.Send(netcore.Msg('view-zone', pid=self.client.localPlayer.pid, zid=game.ZONE_DECK_FATE, \
				number=numCards if event.GetId() == ID_MNU_FATE_LOOK_TOP else -numCards))
	
	def OnMenuDynastyLook(self, event):
		if self.client and self.client.Playing():
			if event.GetId() == ID_MNU_DYN_LOOK_TOP:
				top = 'top'
			else:
				top = 'bottom'
			
			zone = self.client.gameState.MyZone(game.ZONE_DECK_DYNASTY)
				
			dlg = wx.TextEntryDialog(self, 'How many cards do you want to look at?', 'Look at %s cards' % top, '1')
			if dlg.ShowModal() != wx.ID_OK:
				return
			
			numCards = min(len(zone), int(dlg.GetValue()))
			self.client.Send(netcore.Msg('view-zone', pid=self.client.localPlayer.pid, zid=game.ZONE_DECK_DYNASTY, \
				number=numCards if event.GetId() == ID_MNU_DYN_LOOK_TOP else -numCards))
	
	def OnMenuCreateFocusPool(self, event):
		# Move top cards into focus pool.
		if self.client and self.client.Playing():
			for cgid in self.client.gameState.MyZone(game.ZONE_DECK_FATE).TopCards(3):
				self.client.Send(netcore.Msg('move-card', cgid=cgid, pid=self.client.localPlayer.pid, zid=game.ZONE_FOCUS_POOL, top=True))
		ViewFocusPoolDialog(self, title='Focus Pool', gameState=self.client.gameState).Show()
		
	def OnMenuRemovedSearch(self, evt):
		"""React to the user wanting to search their RFG zone."""
		self.client.Send(netcore.Msg('view-zone', pid=self.client.localPlayer.pid, zid=game.ZONE_REMOVED))

	def OnCardHover(self, evt):
		"""React to a card on the playfield being hovered over."""
		if evt.card.faceUp:
			try:
				self.cardPreview.SetCard(evt.card.data.id)
			except AttributeError:
				pass
		else:
			self.cardPreview.SetFacedown(evt.card)
		
	def OnChatClickLink(self, event):
		self.cardPreview.SetCard(event.key)
	
	def OnDoubleClickCard(self, evt):
		"""Process a double click on a card on the playfield canvas."""
		if evt.card.faceUp == False:
			self.client.Send(netcore.Msg('set-card-property', cgid=evt.card.cgid, property='faceUp', value=True))
		else:
			self.client.Send(netcore.Msg('set-card-property', cgid=evt.card.cgid, property='tapped', value=not evt.card.tapped))

	def OnWheelClickCard(self, evt):
		self.client.Send(netcore.Msg('set-card-property', cgid=evt.card.cgid, property='faceUp', value=not evt.card.faceUp))
		
	def OnRightClickCard(self, evt):
		"""Process a right-click on a card on the playfield canvas."""
		self.contextCard = evt.card
		cardMenu = wx.Menu()
		cardMenu.Append(ID_MNU_CARDPOPUP_FLIP, 'Flip face-down' if evt.card.faceUp else 'Flip face-up', 'Flip this card over.')
		cardMenu.Append(ID_MNU_CARDPOPUP_TAP, 'Straighten' if evt.card.tapped else 'Bow', 'Change this card\'s bowed status.')
		if not evt.card.faceUp:
			cardMenu.Append(ID_MNU_CARDPOPUP_PEEK, 'Peek', 'Peek at this card.')
			#PCW added 1/6/2009
			#if there's more than one player offer the Show to Opponent menu
			if len(self.client.gameState.players) > 1:
				cardMenu.Append(ID_MNU_CARDPOPUP_PEEK_OPPONENT, 'Show to Opponent', 'Show this card to your opponent.')
				
		cardMenu.Append(ID_MNU_CARDPOPUP_DISHONOR, 'Rehonor' if evt.card.dishonored else 'Dishonor', 'Change this card\'s honorable status.')
		cardMenu.AppendSeparator()
		cardMenu.Append(ID_MNU_CARDPOPUP_DISCARD, 'Discard')
		try:
			if evt.card.data.type == 'personality':
				cardMenu.Append(ID_MNU_CARDPOPUP_KILL_DISCARD, 'Destroy and discard', 'Mark this personality dead and then discard him.')
		except AttributeError:
			pass
		cardMenu.AppendSeparator()

		# Changed 1/5/09 by PCW
		# this is for issue 14/19

		#check to see if you can move the card to a deck
		if self.contextCard.IsDynasty() or self.contextCard.IsFate():
			deckname = ''
			if self.contextCard.IsDynasty():
				deckname = 'Dynasty'
			else:
				deckname = 'Fate'
			
			cardMenu.Append(ID_MNU_CARDPOPUP_DECK_TOP, 'Put on %s deck top' % deckname)
			cardMenu.Append(ID_MNU_CARDPOPUP_DECK_BOTTOM, 'Put on %s deck bottom' % deckname)
			cardMenu.AppendSeparator()
		#End Changes 14/19 PCW
		
		# Change control
		if len(self.client.gameState.players) > 1:
			mnuControl = wx.Menu()
			for pid, player in self.client.gameState.players.iteritems():
				if pid != self.client.localPlayer.pid:
					mnuControl.Append(ID_MNU_CARDPOPUP_CONTROL + player.pid, player.name, 'Give control of this card to %s.' % player.name)
			cardMenu.AppendMenu(wx.ID_ANY, 'Give control', mnuControl, 'Give control of this card to another player')
			cardMenu.AppendSeparator()

	#--------------------
	# Added 10-04-2008 by PCW
	# This is the card marker functions
	#--------------------
		# Markers
		markerMenu = wx.Menu()
		markerMenu.Append(ID_MNU_CARDPOPUP_MARKER_ADD_CUSTOM, 'Custom marker...')
		if game.MarkerTemplates:
			markerMenu.AppendSeparator()
			for idx, token in enumerate(game.MarkerTemplates):
				markerMenu.Append(ID_MNU_CARDPOPUP_MARKER_ADD + idx, '%s markers...' % token.name)
		cardMenu.AppendMenu(wx.ID_ANY, 'Add new markers', markerMenu, 'Add one or more markers of any type to this card.')
		
		# Markers types already on it
		for type, amount in evt.card.markers.iteritems():
			markerMenu = wx.Menu()
			markerMenu.Append(ID_MNU_CARDPOPUP_MARKER_ADD + game.MarkerNames[type], 'Add...', 'Add one or more %s markers from this card.' % type)
			markerMenu.Append(ID_MNU_CARDPOPUP_MARKER_REMOVE + game.MarkerNames[type], 'Remove...', 'Remove one or more %s markers from this card.' % type)
			cardMenu.AppendMenu(wx.ID_ANY, '%s markers (%d)'  % (type, evt.card.NumMarkers(type)), markerMenu, 'Manipulate %s markers on this card.' % type)
		
	#--------------------
	# End of additions
	#--------------------
		
		# Tokens
		tokenMenu = wx.Menu()
		tokenMenu.Append(ID_MNU_CARDPOPUP_TOKEN_ADD_CUSTOM, 'Custom token...')
		if game.TokenTemplates:
			tokenMenu.AppendSeparator()
			for idx, token in enumerate(game.TokenTemplates):
				tokenMenu.Append(ID_MNU_CARDPOPUP_TOKEN_ADD + idx, '%s tokens...' % token.name)
		cardMenu.AppendMenu(wx.ID_ANY, 'Add new tokens', tokenMenu, 'Add one or more tokens of any type to this card.')
		
		# Token types already on it
		for type, amount in evt.card.tokens.iteritems():
			tokenMenu = wx.Menu()
			tokenMenu.Append(ID_MNU_CARDPOPUP_TOKEN_ADD + game.TokenNames[type], 'Add...', 'Add one or more %s tokens from this card.' % type)
			tokenMenu.Append(ID_MNU_CARDPOPUP_TOKEN_REMOVE + game.TokenNames[type], 'Remove...', 'Remove one or more %s tokens from this card.' % type)
			cardMenu.AppendMenu(wx.ID_ANY, '%s tokens (%d)'  % (type, evt.card.NumTokens(type)), tokenMenu, 'Manipulate %s tokens on this card.' % type)

		self.PopupMenu(cardMenu)


	def OnMenuCardTap(self, evt):
		self.client.Send(netcore.Msg('set-card-property', cgid=self.contextCard.cgid, property='tapped', value=not self.contextCard.tapped))
	
	def OnMenuCardFlip(self, evt):
		self.client.Send(netcore.Msg('set-card-property', cgid=self.contextCard.cgid, property='faceUp', value=not self.contextCard.faceUp))

	def OnMenuCardDiscard(self, evt):
		if not self.contextCard:
			return
		self.contextCard.Isolate()
		if self.contextCard.IsDynasty():
			self.client.Send(netcore.Msg('move-card', cgid=self.contextCard.cgid, top=True, pid=self.client.localPlayer.pid, zid=game.ZONE_DISCARD_DYNASTY))
		else:
			self.client.Send(netcore.Msg('move-card', cgid=self.contextCard.cgid, top=True, pid=self.client.localPlayer.pid, zid=game.ZONE_DISCARD_FATE))
	
	def OnMenuCardKillDiscard(self, evt):
		if not self.contextCard:
			return

		self.contextCard.Isolate()
		self.client.Send(netcore.Msg('set-card-property', cgid=self.contextCard.cgid, property='dead', value=True))
		if self.contextCard.IsDynasty():
			self.client.Send(netcore.Msg('move-card', cgid=self.contextCard.cgid, top=True, pid=self.client.localPlayer.pid, zid=game.ZONE_DISCARD_DYNASTY))
		else:
			self.client.Send(netcore.Msg('move-card', cgid=self.contextCard.cgid, top=True, pid=self.client.localPlayer.pid, zid=game.ZONE_DISCARD_FATE))
		
	def OnMenuCardDeckTop(self, evt):
		if not self.contextCard:
			return
		self.contextCard.Isolate()
		if self.contextCard.IsDynasty():
			self.client.Send(netcore.Msg('move-card', cgid=self.contextCard.cgid, top=True, pid=self.client.localPlayer.pid, zid=game.ZONE_DECK_DYNASTY))
		else:
			self.client.Send(netcore.Msg('move-card', cgid=self.contextCard.cgid, top=True, pid=self.client.localPlayer.pid, zid=game.ZONE_DECK_FATE))

	def OnMenuCardDeckBottom(self, evt):
		if not self.contextCard:
			return
		self.contextCard.Isolate()
		if self.contextCard.IsDynasty():
			self.client.Send(netcore.Msg('move-card', cgid=self.contextCard.cgid, top=False, pid=self.client.localPlayer.pid, zid=game.ZONE_DECK_DYNASTY))
		else:
			self.client.Send(netcore.Msg('move-card', cgid=self.contextCard.cgid, top=False, pid=self.client.localPlayer.pid, zid=game.ZONE_DECK_FATE))

	def OnMenuCardOpponentPeek(self, evt):
		cardID = self.contextCard.cgid
		card = self.client.gameState.FindCard(cardID)
		self.client.Send(netcore.Msg('peek-opponent', cgid=self.contextCard.cgid, pid=self.client.localPlayer.pid))
		
	def OnMenuCardPeek(self, evt):
		self.client.Send(netcore.Msg('peek-card', cgid=self.contextCard.cgid))

	def OnMenuCardDishonor(self, evt):
		self.client.Send(netcore.Msg('set-card-property', cgid=self.contextCard.cgid, property='dishonored', value=not self.contextCard.dishonored))

	def OnMenuCardMoveTop(self, evt):
		self.contextCard.Isolate()
		self.client.Send(netcore.Msg('move-card', cgid=self.contextCard.cgid, top=True, pid=self.client.localPlayer.pid, zid=game.ZONE_PLAY))

	def OnMenuCardMoveBottom(self, evt):
		self.contextCard.Isolate()
		self.client.Send(netcore.Msg('move-card', cgid=self.contextCard.cgid, top=False, pid=self.client.localPlayer.pid, zid=game.ZONE_PLAY))

	def OnMenuCardAddCustomToken(self, evt):
		dlg = AddTokenDialog(self)
		if dlg.ShowModal() == wx.ID_OK:
			numTokens = self.contextCard.NumTokens(dlg.GetToken()) + int(dlg.GetNumber())
			self.client.Send(netcore.Msg('set-tokens', cgid=self.contextCard.cgid, token=dlg.GetToken(), number=numTokens))
		
	def OnMenuCardAddToken(self, evt):
		# Figure out what kind of token.
		tokenIdx = evt.GetId() - ID_MNU_CARDPOPUP_TOKEN_ADD
		token = game.TokenTemplates[tokenIdx]
		
		# How many tokens?
		dlg = AddTokenDialog(self, token=token.name)
		if dlg.ShowModal() == wx.ID_OK:
			numTokens = self.contextCard.NumTokens(token.name) + int(dlg.GetNumber())
			self.client.Send(netcore.Msg('set-tokens', cgid=self.contextCard.cgid, token=token.name, number=numTokens))

	def OnMenuCardRemoveToken(self, evt):
		# Figure out what kind of token.
		tokenIdx = evt.GetId() - ID_MNU_CARDPOPUP_TOKEN_REMOVE
		token = game.TokenTemplates[tokenIdx]
		
		# How many tokens?
		dlg = AddTokenDialog(self, title='Remove tokens', token=token.name)
		if dlg.ShowModal() == wx.ID_OK:
			numTokens = self.contextCard.NumTokens(token.name) - int(dlg.GetNumber())
			self.client.Send(netcore.Msg('set-tokens', cgid=self.contextCard.cgid, token=token.name, number=numTokens))

	#--------------------------
	# Added 08-23-2008 by PCW
	# These are the handlers for adding custom markers to the cards
	# Markers will be removed at the end of every turn.
	#--------------------------
	def OnMenuCardAddCustomMarker(self, evt):
		dlg = AddMarkerDialog(self)
		if dlg.ShowModal() == wx.ID_OK:
			numMarkers = self.contextCard.NumMarkers(dlg.GetToken()) + int(dlg.GetNumber())
			customImage = dlg.GetTokenImage()
			markerName = dlg.GetToken()
			game.AddMarkerTemplate(markerName, customImage)
			self.client.Send(netcore.Msg('set-markers', cgid=self.contextCard.cgid, token= markerName, number=numMarkers, image=customImage))
		
	def OnMenuCardAddMarker(self, evt):
		# Figure out what kind of token.
		tokenIdx = evt.GetId() - ID_MNU_CARDPOPUP_MARKER_ADD
		token = game.MarkerTemplates[tokenIdx]
		
		# How many tokens?
		dlg = AddMarkerDialog(self, token=token.name)
		if dlg.ShowModal() == wx.ID_OK:
			numMarkers = self.contextCard.NumMarkers(token.name) + int(dlg.GetNumber())
			self.client.Send(netcore.Msg('set-markers', cgid=self.contextCard.cgid, token=token.name, number=numMarkers, image=token.image))

	def OnMenuCardRemoveMarker(self, evt):
		# Figure out what kind of token.
		tokenIdx = evt.GetId() - ID_MNU_CARDPOPUP_MARKER_REMOVE
		token = game.MarkerTemplates[tokenIdx]
		
		# How many tokens?
		dlg = AddMarkerDialog(self, title='Remove markers', token=token.name)
		if dlg.ShowModal() == wx.ID_OK:
			numMarkers = self.contextCard.NumMarkers(token.name) - int(dlg.GetNumber())
			self.client.Send(netcore.Msg('set-markers', cgid=self.contextCard.cgid, token=token.name, number=numMarkers, image=token.image))

	def OnMenuRemoveAllMarkers(self, evt):
		#check to make sure you're paying a game
		if self.client and self.client.Playing():
			zone = self.client.localPlayer.zones[game.ZONE_PLAY]
			#get for each card, get the markers and send a 'set-markers' number=0
			for cgid in zone:
				card = self.client.gameState.FindCard(cgid)
				for token in card.markers:
					marker = game.FindMarkerTemplate(game, token)
					self.client.Send(netcore.Msg('set-markers', cgid=card.cgid, token=marker.name, number=0, image=marker.image))

	#--------------------------
	# end of changes
	#--------------------------
	
	def OnMenuCardChangeControl(self, evt):
		pid = evt.GetId() - ID_MNU_CARDPOPUP_CONTROL
		self.contextCard.Isolate()  # Okay, this is a bit of a hack. Optimally we want to give control of the whole unit.
		self.client.Send(netcore.Msg('move-card', cgid=self.contextCard.cgid, pid=pid, 
			x=-self.contextCard.x, y=self.contextCard.y, zid=self.contextCard.location.zid))
	
	def OnMenuHandReveal(self, event):
		if self.client and self.client.Playing():
			self.client.Send(netcore.Msg('show-zone', zid=game.ZONE_HAND))
			
	def OnMenuHandRevealRandom(self, event):
		if self.client and self.client.Playing():
			self.client.Send(netcore.Msg('show-zone-random', zid=game.ZONE_HAND, num=1))

	def OnMenuHandRevealRandomX(self, event):
		if self.client and self.client.Playing():
			dlg = wx.TextEntryDialog(self, 'How many cards do you want to reveal?', 'Reveal cards from hand', '1')
			if dlg.ShowModal() == wx.ID_OK:
				try:
					num = int(dlg.GetValue())
					if num > 0:
						self.client.Send(netcore.Msg('show-zone-random', zid=game.ZONE_HAND, num=num))
				except ValueError:
					pass

	def OnMenuHandDiscard(self, event):
		for cgid in self.client.gameState.MyZone(game.ZONE_HAND):
			self.client.Send(netcore.Msg('move-card', cgid=cgid, top=True, pid=self.client.localPlayer.pid, zid=game.ZONE_DISCARD_FATE))

	def OnMenuHandDiscardRandom(self, event):
		self.client.Send(netcore.Msg('move-random', fromzid=game.ZONE_HAND, pid=self.client.localPlayer.pid, zid=game.ZONE_DISCARD_FATE))
	
	
	def StopServer(self):
		if self.server:
			self.PrintToChat('Stopping server...')
			self.server.Stop()
			if self.server.isAlive(): self.server.join()
		self.server = None
		self.GetMenuBar().Enable(ID_MNU_LAUNCH_EGGUPDATER, True)
		self.GetMenuBar().Enable(ID_MNU_START_GAME, False)
		self.GetToolBar().EnableTool(ID_MNU_START_GAME, False)
	
	def StartServer(self):
		self.server = netcore.Server(database.get())
		self.server.Setup()
		self.PrintToChat('Server started (%s).' % self.server.localaddress)
		self.server.start()  # Thread
		self.GetMenuBar().Enable(ID_MNU_LAUNCH_EGGUPDATER, False)
		self.GetMenuBar().Enable(ID_MNU_START_GAME, True)
		self.GetToolBar().EnableTool(ID_MNU_START_GAME, True)
	
	def StopClient(self):
		if self.client:
			self.PrintToChat('Stopping client...')
			self.client.Stop()
			if self.client.isAlive(): self.client.join()
		self.gameTable.Shutdown()
		self.client = None
		self.GetMenuBar().Enable(ID_MNU_DISCONNECT, False)
		self.GetMenuBar().Enable(ID_MNU_JOIN_GAME, False)
		self.GetToolBar().EnableTool(ID_MNU_DISCONNECT, False)
		self.GetToolBar().EnableTool(ID_MNU_JOIN_GAME, False)
		self.EnableGameMenus(False)
		self.lstClients.DeleteAllItems()
		self.Refresh()

			
	#-----------------
	# Added 08-23-2008 by PCW
	# This is the call to the GAME Matching Service
	#-----------------
	def StopGameMatchService(self):
		if self.gamematchserver:
			self.PrintToChat('Stopping GameMatch Service.')
			self.gamematchserver.Disconnect()
			self.gamematchserver = None

	def StartGameMatchService(self):
		"""Contacts the GameMatch Service to get an opponents IP and Port"""

		self.gamematchserver = netcore.GameMatchServer('10.2.2.35',1023,self)
		self.PrintToChat('Contacting the GameMatch Service.')
		try:
			self.gamematchserver.Connect()
		except socket.error, (code, msg):
			self.PrintToChat('Failed.')
			self.gamematchserver = None
			dlg = wx.MessageDialog(self, 'Connection failed: %s (%d)' % (msg, code), 'Failed', wx.ICON_ERROR)
			dlg.ShowModal()
			return

		self.gamematchserver.start() #thread
		self.PrintToChat(self.gamematchserver.errorString)

	def OnGameMatchLoggedIn(self, address):
		self.PrintToChat('Now logged into GameMatch Service.')
		self.PrintToChat('Getting next opponent.')
		self.gamematchserver.GetOpponentAddress()
		
	def OnGameMatchNoOpponent(self, text):
		self.PrintToChat('No Opponents are currently available.')
		self.StopGameMatchService()

	def	OnGameMatchOpponentFound(self, oip, oport):
		self.PrintToChat('Found opponent at \'%s\'' % (oip,':',oport))
		settings.gamehost = oip
		try:
			port = int(oport)
		except ValueError:
			port = netcore.DEFAULT_PORT
		settings.gameport = oport
		settings.WriteSettingsFile()
		self.StopClient()
		self.StopServer()
		self.StartClient(settings.gamehost, settings.gameport)
		
		
	def StartClient(self, host, port=netcore.DEFAULT_PORT):
		self.client = netcore.Client(database.get(), settings.playername, self)
		
		self.PrintToChat('Connecting to %s...' % (host))
		try:
			self.client.Connect(host, port)
		except socket.error, (code, msg):
			self.PrintToChat('Failed.')
			self.client = None
			dlg = wx.MessageDialog(self, 'Connection failed: %s (%d)' % (msg, code), 'Failed', wx.ICON_ERROR)
			dlg.ShowModal()
			return False
		
		self.client.start()
		self.PrintToChat('Connected.')
		self.GetMenuBar().Enable(ID_MNU_DISCONNECT, True)
		self.GetMenuBar().Enable(ID_MNU_JOIN_GAME, True)
		self.GetToolBar().EnableTool(ID_MNU_DISCONNECT, True)
		self.GetToolBar().EnableTool(ID_MNU_JOIN_GAME, True)
		return True
	
	#------------------------------------------------------------------------------------------------------------------------------------------------------------
	#
	# Client callbacks.
	#
	#------------------------------------------------------------------------------------------------------------------------------------------------------------
	def OnClientNames(self, event):
		"Callback for when the client receives a list of already-connected clients."
		if len(event.names) > 0:
			# If there's someone here besides ourselves
			self.PrintToChat('People at the table: ' + ', '.join((name for clid, name in event.names)))
		else:
			self.PrintToChat('The table is empty.')
		
		self.lstClients.DeleteAllItems()
		for clid, name in event.names:
			idx = self.lstClients.InsertStringItem(0, name)
			self.lstClients.SetItemData(idx, clid)
		
		# Add ourselves, too.
		idx = self.lstClients.InsertStringItem(0, self.client.localName)
		self.lstClients.SetItemData(idx, self.client.localClid)
		
	def OnClientNameChanged(self, event):
		"Callback for a client changing his/her name."
		if event.clid == self.client.localClid:
			self.PrintToChat('You are now known as %s.' % event.name)
			idx = self.lstClients.FindItemData(-1, event.clid)
			self.lstClients.SetStringItem(idx, 0, event.name)
		else:
			if event.oldname == None:
				# Slight bit of a hack, but it works! The first time we see someone get a name, assume they just joined.
				self.PrintToChat('%s has joined the table.' % event.name)
				idx = self.lstClients.InsertStringItem(0, event.name)
				self.lstClients.SetItemData(idx, event.clid)
			else:
				self.PrintToChat('%s changed name to %s.' % (event.oldname, event.name))
				idx = self.lstClients.FindItemData(-1, event.clid)
				self.lstClients.SetStringItem(idx, 0, event.name)
	
	def OnClientRejected(self, event):
		wx.MessageDialog(self, 'Connection was refused by the server:\n%s' % event.msg, 'Connection refused', wx.ICON_ERROR).ShowModal()
		#self.StopClient()
		
	def OnClientChat(self, event):
		self.PrintToChat('<%s> %s' % (self.client.GetClientName(event.clid), event.msg))
		if not self.IsActive():
			self.RequestUserAttention()
	
	def OnClientDisconnect(self, event):
		"Callback for when the client is forcibly disconnected."
		if not MainWindow.LogFile is None:
			MainWindow.LogFile.close()

		self.StopClient()
		self.StopServer()
		self.PrintToChat('Disconnected.')
	
	def OnClientQuit(self, event):
		if not MainWindow.LogFile is None:
			MainWindow.LogFile.close()
		idx = self.lstClients.FindItemData(-1, event.clid)
		self.lstClients.DeleteItem(idx)
		self.PrintToChat('%s has disconnected.' % self.client.clientNames[event.clid])
		
	def OnClientDeckSubmit(self, event):
		if event.clid == self.client.localClid:
			self.PrintToChat('You\'ve submitted a deck and are ready to play in the next game.')
		else:
			self.PrintToChat('%s has submitted a deck and is ready to play in the next game.' % self.client.GetClientName(event.clid))
		
		# Update their icon in the list.
		idx = self.lstClients.FindItemData(-1, event.clid)
		self.lstClients.SetItemImage(idx, 2)
		#self.lstClients.SetStringItem(idx, 3, '', 3)
	
	def OnClientDeckUnsubmit(self, event):
		if event.clid == self.client.localClid:
			self.PrintToChat('You\'ve retracted your deck and will not play in the next game.')
		else:
			self.PrintToChat('%s has retracted their deck and will not play in the next game.' % self.client.GetClientName(event.clid))
		idx = self.lstClients.FindItemData(-1, event.clid)
		self.lstClients.SetItemImage(idx, -1)
		
	def OnClientGameSetup(self, event):
		self.lstFateHand.DeleteAllItems()
		
		
	def OnClientGameBegin(self, event):
		if self.client.Playing():  # Only if we're participating.
			self.gameTable.Setup(self.client.gameState, self.client.localPlayer)
			self.deckDynasty.SetGameState(self.client.gameState)
			self.discardDynasty.SetGameState(self.client.gameState)
			self.deckFate.SetGameState(self.client.gameState)
			self.discardFate.SetGameState(self.client.gameState)
			self.rfgZone.SetGameState(self.client.gameState)
			self.EnableGameMenus(True)
		else:
			self.CreatedCards = []
			self.gameTable.Setup(self.client.gameState, None)
			self.deckDynasty.SetGameState(None)
			self.discardDynasty.SetGameState(None)
			self.deckFate.SetGameState(None)
			self.discardFate.SetGameState(None)
			self.rfgZone.SetGameState(None)
			self.EnableGameMenus(False)

		logFilename = ''
		try:
			if settings.log_multiplayer_games == True and self.LogFile is None:
				if len(self.client.gameState.players) > 1:
					logFilename = "_".join([self.client.GetClientName(clid - 1) for clid in self.client.gameState.players]) + '.txt'
					currentdir = os.curdir
					logdir = os.path.join(currentdir, "logs")
					if not os.path.exists(logdir):
						os.makedirs(logdir)
					MainWindow.LogFile = open(logdir +'\\' + logFilename,'w')

		except AttributeError, error:
			print error
			
		self.client.Send(netcore.Msg('discard-favor'))
		self.PrintToChat('A new game round is starting.')
		self.PrintToChat('Players: ' + ', '.join(p.name for (pid,p) in self.client.gameState.players.iteritems()))
	
	def OnClientCardMove(self, event):
		szone = event.oldzone  # Source zone
		mover = self.client.gameState.GetPlayer(event.mover)  # Person requesting the move
		msgs = None
		
		def TopBottom(size, idx):
			if idx == size - 1:
				return 'the top of '
			elif idx == 0:
				return 'the bottom of '
			else:
				return '%d cards down in ' % (size - idx)
		
		if event.zone.zid == game.ZONE_HAND and szone.zid == game.ZONE_DECK_FATE and szone.owner == event.zone.owner and event.zone.owner == mover:
			# Moving a card from your own deck to your own hand: Drawing... sometimes.
			if event.oldzonepos == event.oldzonesize - 1:
				msgs = ('You draw %s.' % event.card.GetStyledName(),
					'%s draws a card.' % mover.name)
			elif event.oldzonepos == 0:
				msgs = ('You draw %s from the bottom of your deck.' % event.card.GetStyledName(),
					'%s draws a card from the bottom of their deck.' % mover.name)
			else:
				msgs = ('You put %s from %syour deck into your hand.' % (event.card.GetStyledName(), TopBottom(event.oldzonesize, event.oldzonepos)),
					'%s puts a card from %stheir deck into their hand.' % (mover.name, TopBottom(event.oldzonesize, event.oldzonepos)))
		elif event.zone.zid == game.ZONE_DISCARD_FATE and szone.zid == game.ZONE_HAND and szone.owner == event.zone.owner and event.zone.owner == mover:
			# Moving a card from your own hand to your own discard pile: Discarding.
			msgs = ('You %sdiscard %s.' % ('randomly ' if event.random else '', event.card.GetStyledName()),
				'%s %sdiscards %s.' % (mover.name, 'randomly ' if event.random else '', event.card.GetStyledName()))
		elif event.zone.zid == game.ZONE_PLAY and szone.zid == game.ZONE_FOCUS_POOL:
			msgs = ('You focus %s.' % event.card.GetStyledName(),
				'%s focuses a card.' % mover.name)
		elif event.zone.zid == game.ZONE_PLAY and szone.zid == game.ZONE_PLAY:
			# Cards moving around in play shouldn't have printed messages, unless...
			if event.zone.owner.pid != szone.owner.pid:
				# ... we are changing controllers.
				msgs = ('You give control of %s to %s.' % (event.card.GetStyledName(), event.zone.owner.name),
					'%s gives control of %s to %s.' % (szone.owner.name, event.card.GetStyledName(), event.zone.owner.name))
		else:
			# Generic message.
			# Card name
			msgCardName = event.card.GetStyledName()
			if (event.zone.zid == game.ZONE_PLAY and not event.faceUp) or (szone.zid == game.ZONE_PLAY and not event.card.faceUp) : # Moving facedown cards in or out of play
				msgCardName = 'a face-down card'
			
			# Source
			msgSource = ''
			if szone.zid == game.ZONE_DECK_FATE or szone.zid == game.ZONE_DECK_DYNASTY:  # Top/bottom is relevant for decks.
				msgSource = TopBottom(event.oldzonesize, event.oldzonepos)
			
			if szone.zid != game.ZONE_PLAY:
				if self.client.IsLocalPlayer(szone.owner.pid):
					msgSource += 'your '
				else:
					msgSource += szone.owner.name + '\'s '  # Owner's name
			msgSource += game.zoneNames[szone.zid]
			
			# Destination
			msgDest = ''
			if event.zone.zid == game.ZONE_DECK_FATE or event.zone.zid == game.ZONE_DECK_DYNASTY:  # Top/bottom is relevant for decks.
				if event.zonepos == 0:
					msgDest = 'on the bottom of '
				elif event.zonepos == len(event.zone.cards) - 1:
					msgDest = 'on top of '
				else:
					msgDest = 'into '
			else:
				msgDest = 'into '
			
			if event.zone.zid != game.ZONE_PLAY:
				if self.client.IsLocalPlayer(event.zone.owner.pid):
					msgDest += 'your '
				else:
					msgDest += event.zone.owner.name + '\'s '  # Owner's name
			msgDest += game.zoneNames[event.zone.zid]
			
			# Adjust the message slightly for discard piles.
			if event.zone.zid == game.ZONE_DISCARD_FATE or event.zone.zid == game.ZONE_DISCARD_DYNASTY:
				msgs = ['You discard %s from %s.' % (msgCardName, msgSource),
					'%s discards %s from %s.' % (mover.name, msgCardName, msgSource)]
			else:
				msgs = ['You put %s from %s %s.' % (msgCardName, msgSource, msgDest),
					'%s puts %s from %s %s.' % (mover.name, msgCardName, msgSource, msgDest)]
		
		# Print any messages we decided we wanted.
		if msgs:
			self.PrintToChat(msgs[0 if self.client.IsLocalPlayer(mover.pid) else 1])
			
		# Moving from hand. Needs to be removed from the list.
		if szone.zid == game.ZONE_HAND:
			idx = -1
			while True:
				idx = self.lstFateHand.GetNextItem(idx, wx.LIST_NEXT_ALL)
				if idx == -1:
					break
				if self.lstFateHand.GetItemData(idx) == event.card.cgid:
					self.lstFateHand.DeleteItem(idx)
					break
		elif szone.zid == game.ZONE_PLAY:
			self.gameTable.Refresh()

		# ---
		if event.zone.zid == game.ZONE_PLAY:
			self.gameTable.Refresh()
		elif event.zone.zid == game.ZONE_HAND:
			if event.zone.owner == self.client.localPlayer:
				idx = self.lstFateHand.InsertStringItem(0, event.card.GetName())
				try:
					self.lstFateHand.SetStringItem(idx, 1, event.card.data.cost)
					self.lstFateHand.SetStringItem(idx, 2, event.card.data.focus)
				except AttributeError:
					pass
				self.lstFateHand.SetItemData(idx, event.card.cgid)
		
		self.UpdateDecks()  # Update deck widgets too.
		
		# Update the client widget with hand sizes if applicable.
		for player in self.client.gameState.players.itervalues():
			handSize = len(player.FindZone(game.ZONE_HAND))
			idx = self.lstClients.FindItemData(-1, player.clid)
			self.lstClients.SetStringItem(idx, 2, str(handSize))
		
		event.Skip()

	def OnClientPeekOpponentCard(self, event):
		"""Let your Opponent peek at one of your face down cards"""
		#Added 1/6/09 by PCW
		card = self.client.gameState.FindCard(event.cgid)
		player = self.client.gameState.GetPlayer(event.pid)

##		if not self.client.IsLocalPlayer(event.pid):
##			self.PrintToChat('%s peeks at your facedown card.' % (player.name))		
##		else:
##			self.PrintToChat('%s shows you a face down card: %s.' % (player.name, card.GetStyledName()))
	
		if self.client.IsLocalPlayer(event.pid):
			self.PrintToChat('%s peeks at your facedown card.' % (player.name))		
		else:
			self.PrintToChat('%s shows you a face down card: %s.' % (player.name, card.GetStyledName()))
			#wx.FindWindowById(ID_CARD_PREVIEW).SetCard()
	
	def OnClientPeekCard(self, event):

		card = self.client.gameState.FindCard(event.cgid)

		if self.client.IsLocalPlayer(event.pid):
			self.PrintToChat('You peek at %s.' % card.GetStyledName())
			wx.FindWindowById(ID_CARD_PREVIEW).SetCard(card.data.id)
		else:
			self.PrintToChat('%s peeks at %s.' % (self.client.gameState.FindPlayer(event.pid).name, card.GetStyledName()))
		
	def OnClientCardPropertyChanged(self, event):
		"""Process a property of a card being updated."""
		card = self.client.gameState.FindCard(event.cgid)
		player = self.client.gameState.GetPlayer(event.pid)
		if event.property == 'tapped':  # Bowed status has changed.
			if self.client.IsLocalPlayer(player.pid):
				msg = 'You %s %s.' % ('bow' if event.value else 'straighten', card.GetStyledName())
			else:
				msg = '%s %s %s.' % (player.name, 'bows' if event.value else 'straightens', card.GetStyledName())
			self.PrintToChat(msg)
		elif event.property == 'faceUp':  # Facing has changed.
			if self.client.IsLocalPlayer(player.pid):
				msg = 'You flip %s face-%s.' % (card.GetStyledName(), 'up' if event.value else 'down')
			else:
				msg = '%s flips %s face-%s.' % (player.name, card.GetStyledName(), 'up' if event.value else 'down')
			self.PrintToChat(msg)
		elif event.property == 'dishonored':  # Dishonored!
			if self.client.IsLocalPlayer(player.pid):
				msg = 'You %s %s.' % ('dishonor' if event.value else 'rehonor', card.GetStyledName())
			else:
				msg = '%s %s %s.' % (player.name, 'dishonors' if event.value else 'rehonors', card.GetStyledName())
			self.PrintToChat(msg)
		elif event.property == 'dead':  # Dead status has changed.
			if event.value:
				self.PrintToChat('%s is now dead.' % card.GetStyledName())
			else:
				self.PrintToChat('%s is no longer dead.' % card.GetStyledName())
		
		self.gameTable.Refresh()
	
	def OnClientZoneShuffled(self, event):
		if self.client.IsLocalPlayer(event.pid):
			self.PrintToChat('You shuffle your %s.' % game.zoneNames[event.zid])
		else:
			self.PrintToChat('%s shuffles their %s.' % (self.client.gameState.GetPlayer(event.pid).name, game.zoneNames[event.zid]))
	
	def OnClientViewZone(self, event):
		if self.client.IsLocalPlayer(event.viewer):  # If it's us looking, we should open a dialog.
			zone = self.client.gameState.FindZone(event.pid, event.zid)
			
			if event.number == 0:
				dialog = ViewDeckDialog(self, title='%s\'s %s' % (self.client.gameState.GetPlayer(event.viewer).name, game.zoneNames[event.zid]), \
					gameState = self.client.gameState, zone=zone)
			elif event.number > 0:
				dialog = PeekDialog(self, title='Top %d cards of fate deck' % event.number, gameState = self.client.gameState, cgids=zone.TopCards(event.number))
			else:
				dialog = PeekDialog(self, title='Bottom %d cards of fate deck' % -event.number, gameState = self.client.gameState, cgids=zone.BottomCards(-event.number))

			dialog.Show()
		else:
			# Mention it in case it's a non-public zone.
			if event.number == 0:
				topcards = ''
			elif event.number > 0:
				topcards = 'the top %d cards of ' % event.number
			else:
				topcards = 'the bottom %d cards of ' % -event.number
			
			if event.zid in [game.ZONE_DECK_FATE, game.ZONE_DECK_DYNASTY, game.ZONE_HAND]:
				if self.client.IsLocalPlayer(event.pid):
					self.PrintToChat('%s looks through %syour %s.' % \
						(self.client.gameState.GetPlayer(event.viewer).name,
						topcards,
						game.zoneNames[event.zid]))
				else:
					self.PrintToChat('%s looks through %s%s\'s %s.' % \
						(self.client.gameState.GetPlayer(event.viewer).name,
						topcards,
						self.client.gameState.GetPlayer(event.pid).name,
						game.zoneNames[event.zid]))
	
	def OnClientFamilyHonor(self, event):
		"""Handle a change in family honor."""
		player = self.client.gameState.FindPlayer(event.pid)
		
		# Make a little string showing the change.
		if event.oldhonor > event.honor:
			honorchange = str(event.honor - event.oldhonor)
		else:
			honorchange = '+%d' % (event.honor - event.oldhonor)
		
		if self.client.IsLocalPlayer(event.pid):
			self.PrintToChat('Your family honor is now %s (%s).' % (event.honor, honorchange))
		else:
			self.PrintToChat('%s\'s family honor is now %s (%s).' % (player.name, event.honor, honorchange))
		
		# Update the client list too.
		idx = self.lstClients.FindItemData(-1, player.clid)
		self.lstClients.SetStringItem(idx, 1, str(event.honor))

	#--------------------
	# Added 10-04-2008 by PCW
	# This is the card marker functions
	#--------------------
	def OnClientSetMarkers(self, event):
		# This is important -- make sure the marker exists in our list of available markers.
		# If it doesn't, the menus will break.
		if event.token not in game.MarkerNames:	
			if event.image is None:
				game.AddMarkerTemplate(event.token)
			else:
				game.AddMarkerTemplate(event.token, event.image)
		
		card = self.client.gameState.FindCard(event.cgid)

		if event.change == 0:  # No change--don't bother.
			return
		
		def number_words(n):
			try:
				return ['no', 'a', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve'][n]
			except IndexError:
				return str(n)
		
		# Basically, let's figure out the message.
		if event.number == 0:
			tokenMsg = 'all %s markers' % event.token
		elif abs(event.change) == 1:
			tokenMsg = 'a %s marker' % event.token
		else:
			tokenMsg = '%s %s markers' % (number_words(abs(event.change)), event.token)
		
		if self.client.IsLocalPlayer(event.pid):
			if event.change > 0:
				personMsg = 'You put %s on '
			else:
				personMsg = 'You remove %s from '
		else:
			if event.change > 0:
				personMsg = self.client.gameState.FindPlayer(event.pid).name + ' puts %s on ' 
			else:
				personMsg = self.client.gameState.FindPlayer(event.pid).name + ' removes %s from '
		
		msg = personMsg % tokenMsg + card.GetStyledName()
		if event.number != 0:
			msg += ' (%d total)' % event.number
		self.PrintToChat(msg + '.')
		self.gameTable.Refresh()
	#--------------------
	# End of additions
	#--------------------

	
	def OnClientSetTokens(self, event):
		# This is important -- make sure the token exists in our list of available tokens.
		# If it doesn't, the menus will break.
		if event.token not in game.TokenNames:
			game.AddTokenTemplate(event.token)
		
		card = self.client.gameState.FindCard(event.cgid)
		
		if event.change == 0:  # No change--don't bother.
			return
		
		def number_words(n):
			try:
				return ['no', 'a', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve'][n]
			except IndexError:
				return str(n)
		
		# Basically, let's figure out the message.
		if event.number == 0:
			tokenMsg = 'all %s tokens' % event.token
		elif abs(event.change) == 1:
			tokenMsg = 'a %s token' % event.token
		else:
			tokenMsg = '%s %s tokens' % (number_words(abs(event.change)), event.token)
		
		if self.client.IsLocalPlayer(event.pid):
			if event.change > 0:
				personMsg = 'You put %s on '
			else:
				personMsg = 'You remove %s from '
		else:
			if event.change > 0:
				personMsg = self.client.gameState.FindPlayer(event.pid).name + ' puts %s on ' 
			else:
				personMsg = self.client.gameState.FindPlayer(event.pid).name + ' removes %s from '
		
		msg = personMsg % tokenMsg + card.GetStyledName()
		if event.number != 0:
			msg += ' (%d total)' % event.number
		self.PrintToChat(msg + '.')
		self.gameTable.Refresh()
	
	def OnClientCreateCard(self, event):
		card = self.client.gameState.FindCard(event.cgid)
		
		if self.client.IsLocalPlayer(event.pid):
			self.PrintToChat('You create a card named %s in your %s.' % (card.GetStyledName(), game.zoneNames[event.zid]))
			if event.zid == game.ZONE_HAND: # Update our hand, if applicable.
				idx = self.lstFateHand.InsertStringItem(0, card.GetName())
				self.lstFateHand.SetStringItem(idx, 1, card.data.cost)
				self.lstFateHand.SetStringItem(idx, 2, card.data.focus)
				self.lstFateHand.SetItemData(idx, card.cgid)
		else:
			self.PrintToChat('%s creates a card named %s in their %s.' % (self.client.gameState.FindPlayer(event.pid).name, card.GetStyledName(), game.zoneNames[event.zid]))
			
		# Update the client widget with hand sizes if applicable.
		for player in self.client.gameState.players.itervalues():
			handSize = len(player.FindZone(game.ZONE_HAND))
			idx = self.lstClients.FindItemData(-1, player.clid)
			self.lstClients.SetStringItem(idx, 2, str(handSize))
		
	def OnClientNewCard(self, event):
		CreatedCards.append(event.cdid)
		data = database.get()[event.cdid]
		
		if self.mnuCreateCard.GetMenuItemCount() == 1:
			self.mnuCreateCard.AppendSeparator()
		self.mnuCreateCard.Append(ID_MNU_CREATE_CARD_CUSTOM + len(CreatedCards), data.name, 'Create a %s card.' % data.name)
	
	def OnClientFlipCoin(self, event):
		result = 'heads' if event.result else 'tails'
		if self.client.IsLocalPlayer(event.pid):
			self.PrintToChat('You flip a coin: %s.' % result)
		else:
			self.PrintToChat('%s flips a coin: %s.' % (self.client.gameState.FindPlayer(event.pid).name, result))
	
	def OnClientRollDie(self, event):
		if self.client.IsLocalPlayer(event.pid):
			self.PrintToChat('You roll a %d-sided die: %d.' % (event.size, event.result))
		else:
			self.PrintToChat('%s rolls a %d-sided die: %s.' % (self.client.gameState.FindPlayer(event.pid).name, event.size, event.result))

	def OnClientFavor(self, event):
		"""Update the status of the Imperial Favor."""
		if event.oldpid != -1:
			idx = self.lstClients.FindItemData(-1, self.client.gameState.FindPlayer(event.oldpid).clid)
			self.lstClients.SetItemImage(idx, 2)
		
		if event.pid != -1:
			if self.client.IsLocalPlayer(event.pid):
				self.PrintToChat('You take the Imperial Favor.')
			else:
				self.PrintToChat('%s takes the Imperial Favor.' % self.client.gameState.FindPlayer(event.pid).name)
			idx = self.lstClients.FindItemData(-1, self.client.gameState.FindPlayer(event.pid).clid)
			self.lstClients.SetItemImage(idx, 3)
		elif event.oldpid != -1:
			if self.client.IsLocalPlayer(event.oldpid):
				self.PrintToChat('You discard the Imperial Favor.')
			else:
				self.PrintToChat('%s discards the Imperial Favor.' % self.client.gameState.FindPlayer(event.oldpid).name)
	
	def OnClientShowZone(self, event):
		"""Someone is revealing a zone or a few cards from a zone."""
		
		def litjoin(lst):
			if len(lst) == 1:
				return lst[0]
			else:
				return '%s and %s' % (', '.join(lst[:-1]), lst[-1])
			return ''
		
		cardstr = litjoin([self.client.gameState.FindCard(cgid).GetStyledName() for cgid in event.cgids])
		
		if self.client.IsLocalPlayer(event.pid):
			self.PrintToChat('You %sreveal %s from your %s.' % \
				('randomly ' if event.random else '', cardstr, game.zoneNames[event.zid]))
		else:
			self.PrintToChat('%s %sreveals %s from their %s.' % \
				(self.client.gameState.FindPlayer(event.pid).name, \
				 'randomly ' if event.random else '', cardstr, game.zoneNames[event.zid]))
