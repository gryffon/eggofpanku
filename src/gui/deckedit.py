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
"""Deck editor module for Egg of P'an Ku."""

import wx.lib.newevent
import sys
import os
import StringIO

#Local Import
from gui import card_filters, preview
from db import database, dbimport
from game import deck


from settings.xmlsettings import settings

MAIN_TITLE = 'Egg of P\'an Ku Deck Editor'
FILE_DIALOG_WILDCARD = 'Egg of P\'an Ku deck files (*.l5d)|*.l5d|All files (*.*)|*.*'
FILE_DIALOG_GEMPUKKU = 'Gempukku Decks (*.g3d)|*.g3d'
FILE_DIALOG_THEGAME = 'The Game Decks (*.dck)|*.dck'

ID_DE_MNU_NEW_DECK = 9000
ID_DE_MNU_SAVE_DECK = 9001
ID_DE_MNU_SAVE_DECK_AS = 9002
ID_DE_MNU_OPEN_DECK = 9003
ID_DE_MNU_IMPORT_CLIPBOARD = 9004
ID_DE_MNU_IMPORT_GEMPUKKU = 9005
ID_DE_MNU_IMPORT_THEGAME = 9006
ID_DE_MNU_EDIT_OUTPUT_HTML = 9007
ID_DE_MNU_EDIT_OUTPUT_BBCODE = 9008
ID_DE_MNU_RECENT = 9010

ID_MAIN_WINDOW = 8998
ID_CARD_PREVIEW = 8999
ID_FILTER_PANEL = 8997
ID_DECK_LIST_PANEL = 8996

RECENT_FILES_FILE = '.eopkde-recent'
NUM_RECENT = 4

FiltersChangedEvent, EVT_FILTERS_CHANGED = wx.lib.newevent.NewEvent()
AddCardEvent, EVT_ADD_CARD = wx.lib.newevent.NewEvent()
AddInPlayCardEvent, EVT_ADD_IN_PLAY_CARD = wx.lib.newevent.NewEvent()
RemoveCardEvent, EVT_REMOVE_CARD = wx.lib.newevent.NewEvent()
RemoveInPlayCardEvent, EVT_REMOVE_IN_PLAY_CARD = wx.lib.newevent.NewEvent()
SelectCardEvent, EVT_SELECT_CARD = wx.lib.newevent.NewEvent()


def int_or_zero(val):
	try:
		return int(val)
	except ValueError:
		return 0

def GetCurrentDeck():
	return wx.FindWindowById(ID_MAIN_WINDOW).deck


class CardSorter:
	"""Base class for card sorters."""
	def __init__(self, cardmap):
		self.cardDB = database.get()
		self.cardmap = cardmap

	def __call__(self, idx1, idx2):
		card1 = self.cardDB[self.cardmap[idx1]]
		card2 = self.cardDB[self.cardmap[idx2]]
		return self.compare(card1, card2)

class CardNameSorter(CardSorter):
	def compare(self, card1, card2):
		return cmp(card1.name.lower(), card2.name.lower())

class CardTypeSorter(CardSorter):
	def compare(self, card1, card2):
		return cmp(card1.type, card2.type)

class CardClanSorter(CardSorter):
	def compare(self, card1, card2):
		if not card1.clans:
			return -1
		elif not card2.clans:
			return 1
		else:
			return cmp(card1.clans[0], card2.clans[0])

class CardFocusSorter(CardSorter):
	def compare(self, card1, card2):
		if card1.focus == card2.focus:
			return 0
		if not card1.focus:
			return -1
		elif not card2.focus:
			return 1
		else:
			return int(card1.focus) - int(card2.focus)

class CardCostSorter(CardSorter):
	def compare(self, card1, card2):
		if card1.cost == card2.cost:
			return 0
		if not card1.cost:
			return -1
		elif not card2.cost:
			return 1
		elif card1.cost == '*':
			return 1
		elif card2.cost == '*':
			return -1
		else:
			return int(card1.cost) - int(card2.cost)

class CardForceChiSorter(CardSorter):
	def compare(self, card1, card2):
		if card1.force == card2.force and card1.chi == card2.chi:
			return 0
		if not card1.force or not card1.chi:
			return -1
		elif not card2.force or not card2.chi:
			return 1
		else:
			# Okay, this is kind of tricky since we're dealing with a pair.
			force1 = int_or_zero(card1.force)
			force2 = int_or_zero(card2.force)
			chi1 = int_or_zero(card1.chi)
			chi2 = int_or_zero(card2.chi)

			if force1 > force2:
				return 1
			elif force2 > force1:
				return -1
			else:
				return chi1 - chi2

class CardPHSorter(CardSorter):
	def compare(self, card1, card2):
		if card1.personal_honor == card2.personal_honor:
			return 0
		if not card1.personal_honor:
			return -1
		elif not card2.personal_honor:
			return 1
		else:
			return int(card1.personal_honor) - int(card2.personal_honor)

class CardHonorReqSorter(CardSorter):
	def compare(self, card1, card2):
		if card1.honor_req == card2.honor_req:
			return 0
		if not card1.honor_req:
			return -1
		elif not card2.honor_req:
			return 1
		elif card1.honor_req == '-':
			return -1
		elif card2.honor_req == '-':
			return 1
		else:
			return int(card1.honor_req) - int(card2.honor_req)




class DeckPanel(wx.Panel):
	"""Panel showing two decks."""
	LST_COL_NAME = 1
	LST_COL_TYPE = 2
	LST_COL_COST = 3
	LST_COL_FOCUS = 4

	lstInPlay = None

	def __init__(self, parent, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.lstFate = wx.ListCtrl(self, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES)
		self.lstFate.InsertColumn(0, "#", wx.LIST_FORMAT_CENTRE, 24)
		self.lstFate.InsertColumn(self.LST_COL_NAME, "Fate Cards", wx.LIST_FORMAT_LEFT, 140)
		self.lstFate.InsertColumn(self.LST_COL_TYPE, "Type", wx.LIST_FORMAT_CENTRE, 80)
		self.lstFate.InsertColumn(self.LST_COL_COST, "Cost", wx.LIST_FORMAT_CENTRE, 48)
		self.lstFate.InsertColumn(self.LST_COL_FOCUS, "Focus", wx.LIST_FORMAT_CENTRE, 48)

		self.lstDynasty = wx.ListCtrl(self, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES)
		self.lstDynasty.InsertColumn(0, "#", wx.LIST_FORMAT_CENTRE, 24)
		self.lstDynasty.InsertColumn(self.LST_COL_NAME, "Dynasty Cards", wx.LIST_FORMAT_LEFT, 188)
		self.lstDynasty.InsertColumn(self.LST_COL_TYPE, "Type", wx.LIST_FORMAT_CENTRE, 80)
		self.lstDynasty.InsertColumn(self.LST_COL_COST, "Cost", wx.LIST_FORMAT_CENTRE, 48)

##		self.lstInPlay = wx.ListCtrl(self, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES)
##		self.lstInPlay.InsertColumn(0, "#", wx.LIST_FORMAT_CENTRE, 24)
##		self.lstInPlay.InsertColumn(self.LST_COL_NAME, "In Play Cards", wx.LIST_FORMAT_LEFT, 188)
##		self.lstInPlay.InsertColumn(self.LST_COL_TYPE, "Type", wx.LIST_FORMAT_CENTRE, 80)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.lstFate, 1, wx.EXPAND|wx.ALL, 5)
		sizer.Add(self.lstDynasty, 1, wx.EXPAND|wx.ALL, 5)
#	   Add the lstInPlay list to the Filter Panel

##		sizer.Add(self.lstInPlay, 1, wx.EXPAND|wx.ALL, 5)

		self.btnAdd = wx.Button(self, label='Add')
		self.btnAddMore = wx.Button(self, label='Add 3')
		self.btnRemove = wx.Button(self, label='Remove')
		self.btnRemoveMore = wx.Button(self, label='Remove 3')
		self.btnAddToInPlay = wx.Button(self, label='Starts In Play')
		self.btnRemoveFromInPlay = wx.Button(self, label='Doesn\'t Start In Play')

		sizerButtons = wx.BoxSizer(wx.HORIZONTAL)
		sizerButtons.Add(self.btnAdd, 0, wx.CENTRE|wx.ALL, 5)
		sizerButtons.Add(self.btnAddMore, 0, wx.CENTRE|wx.ALL, 5)
		sizerButtons.Add(self.btnRemove, 0, wx.CENTRE|wx.ALL, 5)
		sizerButtons.Add(self.btnRemoveMore, 0, wx.CENTRE|wx.ALL, 5)
		sizerButtons.Add(self.btnAddToInPlay, 0, wx.CENTRE|wx.ALL, 5)
		sizerButtons.Add(self.btnRemoveFromInPlay, 0, wx.CENTRE|wx.ALL, 5)

		sizer2 = wx.BoxSizer(wx.VERTICAL)
		sizer2.Add(sizerButtons, 0, wx.CENTRE|wx.ALL, 0)
		sizer2.Add(sizer, 1, wx.CENTRE|wx.EXPAND|wx.ALL, 0)

		# Events
		self.Bind(wx.EVT_BUTTON, self.OnButtonAdd, self.btnAdd)
		self.Bind(wx.EVT_BUTTON, self.OnButtonAddMore, self.btnAddMore)
		self.Bind(wx.EVT_BUTTON, self.OnButtonRemove, self.btnRemove)
		self.Bind(wx.EVT_BUTTON, self.OnButtonRemoveMore, self.btnRemoveMore)
		self.Bind(wx.EVT_BUTTON, self.OnButtonRemoveFromPlay, self.btnRemoveFromInPlay)
		self.Bind(wx.EVT_BUTTON, self.OnButtonAddToInPlay, self.btnAddToInPlay)

		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListClick, self.lstFate)
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListClick, self.lstDynasty)
		self.Bind(wx.EVT_LIST_COL_CLICK, self.OnListColumnClick, self.lstFate)
		self.Bind(wx.EVT_LIST_COL_CLICK, self.OnListColumnClick, self.lstDynasty)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnListActivate, self.lstFate)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnListActivate, self.lstDynasty)

		self.SetSizer(sizer2)

		self.cardMap = []

	def Deselect(self, ):
		self.lastCardId = None
		for lst in (self.lstFate, self.lstDynasty, self.lstInPlay):
			idx = lst.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
			if idx != -1:
				lst.SetItemState(idx, 0, wx.LIST_STATE_SELECTED)

	def OnButtonAdd(self, event):
		wx.PostEvent(self, AddCardEvent(num=1, id=self.lastCardId))

	def OnButtonAddMore(self, event):
		wx.PostEvent(self, AddCardEvent(num=3, id=self.lastCardId))

	def OnButtonAddToInPlay(self,event):
		wx.PostEvent(self, AddInPlayCardEvent(num=1, id=self.lastCardId))

	def OnButtonRemoveFromPlay(self, event):
		try:
			wx.PostEvent(self, RemoveInPlayCardEvent(cdid=self.lastCardId, num=1, inPlay=True))
		except AttributeError:
			return
		self.Remove(self.lastCardId, 1, inPlay=True)

	def OnButtonRemove(self, event):
		try:
			wx.PostEvent(self, RemoveCardEvent(cdid=self.lastCardId, num=1))
		except AttributeError:
			return
		self.Remove(self.lastCardId, 1)

	def OnButtonRemoveMore(self, event):
		try:
			wx.PostEvent(self, RemoveCardEvent(cdid=self.lastCardId, num=3))
		except AttributeError:
			return
		self.Remove(self.lastCardId, 3)

	def OnListColumnClick(self, event):
		sorters = {
			self.LST_COL_NAME: CardNameSorter,
			self.LST_COL_TYPE: CardTypeSorter,
			self.LST_COL_COST: CardCostSorter,
			self.LST_COL_FOCUS: CardFocusSorter,
		}
		try:
			sortobj = sorters[event.GetColumn()](self.cardMap)
		except KeyError:
			return
		event.GetEventObject().SortItems(sortobj)

	def ListAddCard(self, widget, card, mapidx, num=1):
		idx = widget.InsertStringItem(0, str(num))
		widget.SetStringItem(idx, self.LST_COL_NAME, card.name)  # Name
		widget.SetStringItem(idx, self.LST_COL_TYPE, card.type.capitalize())  # Type
		if (card.isFate() or card.isDynasty()):
		  widget.SetStringItem(idx, self.LST_COL_COST, card.cost)  # Cost

		if card.isFate():
			widget.SetStringItem(idx, self.LST_COL_FOCUS, card.focus)  # Focus
		widget.SetItemData(idx, mapidx)

	def SetDeck(self, deck_):
		self.cardMap = []
		self.deck = deck_
		self.lstFate.DeleteAllItems()
		self.lstDynasty.DeleteAllItems()
		self.lstInPlay.DeleteAllItems()

		cardDB = database.get()
		for num, cdid, inplay in self.deck:
			card = cardDB[cdid]
			if (inplay == True):
				widget = self.lstInPlay
			else:
				if card.isDynasty():
					widget = self.lstDynasty
				else:
					widget = self.lstFate
			self.ListAddCard(widget, card, len(self.cardMap), num)
			self.cardMap.append(cdid)

	def OnListActivate(self, event):
		try:
			wx.PostEvent(self, RemoveCardEvent(cdid=self.lastCardId, num=1))
		except AttributeError:
			return
		self.Remove(self.lastCardId, 1)

	def OnListClick(self, event):
		evtobj = event.GetEventObject()
		cdid = self.cardMap[evtobj.GetItemData(event.GetIndex())]

		# Deselect in the other list.
		lst = self.lstFate
		secondlst = self.lstInPlay

		if evtobj == self.lstFate:
			lst = self.lstDynasty
		elif evtobj == self.lstInPlay:
			secondlst = self.lstDynasty
		else:
			lst = self.lstFate

		idx = lst.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
		if idx != -1:
			lst.SetItemState(idx, 0, wx.LIST_STATE_SELECTED)

		idx = secondlst.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
		if idx != -1:
			secondlst.SetItemState(idx, 0, wx.LIST_STATE_SELECTED)

		wx.FindWindowById(ID_CARD_PREVIEW).SetCard(cdid)
		self.lastCardId = cdid

		wx.PostEvent(self, SelectCardEvent(cdid=cdid))

	def Remove(self, cdid, num=1, inPlay=False):
		try:
			card = database.get()[cdid]
		except KeyError:
			return

		if inPlay==True:
			widget = self.lstInPlay
		else:
			if card.isDynasty():
				widget = self.lstDynasty
			else:
				widget = self.lstFate

		try:
			mapidx = self.cardMap.index(cdid)
		except ValueError:
			return  # It can't possibly be in our decks.

		idx = widget.FindItemData(-1, mapidx)
		if idx != -1:
			newcount = int(widget.GetItemText(idx)) - num
			if newcount <= 0:
				widget.DeleteItem(idx)
				self.lastCardId = None
			else:
				widget.SetStringItem(idx, 0, str(newcount))

	def Add(self, cdid, num=1, inPlay=False):
		card = database.get()[cdid]

		if card.type == 'stronghold':
			inPlay = True
		elif card.isSensei():
			inPlay = True
		elif card.isWind():
			inPlay = True

		if inPlay==True:
			widget = self.lstInPlay
		else:
			if card.isDynasty():
				widget = self.lstDynasty
			else:  # Note that strongholds end up here despite being neither.
				widget = self.lstFate

		# Make sure the cdid exists in the card map.
		try:
			mapidx = self.cardMap.index(cdid)
		except ValueError:
			mapidx = len(self.cardMap)
			self.cardMap.append(cdid)

		# See if we already have an entry.
		idx = widget.FindItemData(-1, mapidx)
		if idx != -1:
			widget.SetStringItem(idx, 0, str(int(widget.GetItemText(idx)) + num))
		else:
			self.ListAddCard(widget, card, mapidx, num)

class FilterPanel(wx.Panel):
	def __init__(self, parent, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		# Set up filters.
		self.filters = card_filters.AllFilters()

		# Realize filters.
		panelsizer = wx.BoxSizer(wx.VERTICAL)

		for group, filters in self.filters:
			sbsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, group), wx.VERTICAL)
			gridsizer = wx.FlexGridSizer(0, 2, 2, 4)
			gridsizer.AddGrowableCol(1)
			for f in filters:
				window = self.MakeFilterWindow(f, gridsizer)
			sbsizer.Add(gridsizer, 0, wx.EXPAND|wx.ALL, 3)
			panelsizer.Add(sbsizer, 0, wx.EXPAND|wx.ALL, 1)

		self.lstInPlay = wx.ListCtrl(self, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES)
		self.lstInPlay.InsertColumn(0, "#", wx.LIST_FORMAT_CENTRE, 24)
		self.lstInPlay.InsertColumn(DeckPanel.LST_COL_NAME, "In Play Cards", wx.LIST_FORMAT_LEFT, 188)
		self.lstInPlay.InsertColumn(DeckPanel.LST_COL_TYPE, "Type", wx.LIST_FORMAT_CENTRE, 80)

		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListClick, self.lstInPlay)
		self.Bind(wx.EVT_LIST_COL_CLICK, self.OnListColumnClick, self.lstInPlay)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnListActivate, self.lstInPlay)

		panelsizer.Add(self.lstInPlay, 1, wx.EXPAND|wx.ALL, 5)
		self.SetSizer(panelsizer)

		self.cardMap = []

	def OnListActivate(self,event):
		wx.FindWindowById(ID_DECK_LIST_PANEL).OnButtonRemoveFromPlay(event)

	def OnListColumnClick(self, event):
		wx.FindWindowById(ID_DECK_LIST_PANEL).OnListColumnClick(event)

	def OnListClick(self, event):
		wx.FindWindowById(ID_DECK_LIST_PANEL).OnListClick(event)

	def MakeFilterWindow(self, filter, sizer):
		"""Create some suitable GUI widgets for some filter and return it."""
		win = filter.MakeWindow(self)

		filter._chk = wx.CheckBox(self, label=filter.name + (':' if win else ''))
		filter._chk.SetValue(filter.enabled)
		self.Bind(wx.EVT_CHECKBOX, self.OnCheck, filter._chk)
		sizer.Add(filter._chk, 0, wx.EXPAND|wx.CENTER|wx.ALL, 0)

		if win:
			card_filters.EVT_FILTER_INPUT_CHANGED(win, self.OnFilterInput)
			sizer.Add(win, 1, wx.EXPAND|wx.CENTER|wx.ALL, 0)
		return sizer

	def OnFilterInput(self, event):
		event.filter._chk.SetValue(True)
		event.filter.enabled = True
		wx.PostEvent(self, FiltersChangedEvent())

	def OnCheck(self, event):
		for f in reduce(lambda a, b: a + b[1], self.filters, []):
			f.enabled = bool(f._chk.GetValue())
			f.UpdateValue()
		wx.PostEvent(self, FiltersChangedEvent())

	def GetFilter(self):
		filters = reduce(lambda a, b: a + b[1], self.filters, [])
		return card_filters.AggregateFilter(f for f in filters if f.enabled)


class DeckStatisticsPanel(wx.Panel):
	"""Deck statistics panel."""
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

	def Activate(self):
		pass

class DeckPlaintextPanel(wx.Panel):
	"""Deck "plain text" panel."""
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

		sizer = wx.BoxSizer(wx.VERTICAL)
		self.txtView = wx.TextCtrl(self, style=wx.TE_READONLY|wx.TE_MULTILINE)
		sizer.Add(self.txtView, 1, wx.EXPAND|wx.ALL, 5)

		self.SetSizer(sizer)

	def Activate(self):
		io = StringIO.StringIO()
		GetCurrentDeck().Save(io, deck.OUTPUT_TYPES.Text)
		self.txtView.SetValue(io.getvalue())

class DeckEditPanel(wx.Panel):
	"""Deck editor panel, allowing editing of the deck."""

	CARDLIST_COL_NAME = 0
	CARDLIST_COL_TYPE = 1
	CARDLIST_COL_CLANS = 2
	CARDLIST_COL_COST = 3
	CARDLIST_COL_FORCECHI = 4
	CARDLIST_COL_PH = 5
	CARDLIST_COL_HR = 6
	CARDLIST_COL_FOCUS = 7

	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

		# Middle panel with card list and decks

		splitterCards = wx.SplitterWindow(self, style=wx.SP_3D)

		panel = wx.Panel(splitterCards)
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.lstCards = wx.ListCtrl(panel, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES)
		self.lstCards.InsertColumn(self.CARDLIST_COL_NAME,	 "Name", wx.LIST_FORMAT_LEFT,	 140)
		self.lstCards.InsertColumn(self.CARDLIST_COL_TYPE,	 "Type", wx.LIST_FORMAT_CENTRE,   80)
		self.lstCards.InsertColumn(self.CARDLIST_COL_CLANS,	"Factions", wx.LIST_FORMAT_LEFT, 80)
		self.lstCards.InsertColumn(self.CARDLIST_COL_COST,	 "Cost", wx.LIST_FORMAT_CENTRE,   48)
		self.lstCards.InsertColumn(self.CARDLIST_COL_FORCECHI, "F/C", wx.LIST_FORMAT_CENTRE,	64)
		self.lstCards.InsertColumn(self.CARDLIST_COL_PH,	   "PH", wx.LIST_FORMAT_CENTRE,	 32)
		self.lstCards.InsertColumn(self.CARDLIST_COL_HR,	   "HR", wx.LIST_FORMAT_CENTRE,	 32)
		self.lstCards.InsertColumn(self.CARDLIST_COL_FOCUS,	"FV", wx.LIST_FORMAT_CENTRE,	 32)
		sizer.Add(self.lstCards, 1, wx.EXPAND|wx.ALL, 5)
		panel.SetSizer(sizer)

		# Filters
		self.panelFilters = FilterPanel(self, size=(120, -1), id=ID_FILTER_PANEL)
		inplayListBox = self.panelFilters.lstInPlay
		self.panelDecks = DeckPanel(splitterCards, id=ID_DECK_LIST_PANEL)

		self.panelDecks.lstInPlay= inplayListBox

		splitterCards.SetMinimumPaneSize(180)
		splitterCards.SplitHorizontally(panel, self.panelDecks, 180)
		splitterCards.SetSashGravity(1.0)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(splitterCards, 1, wx.EXPAND|wx.ALL, 0)
		sizer.Add(self.panelFilters, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
		self.SetSizer(sizer)

		EVT_FILTERS_CHANGED(self.panelFilters, self.OnFiltersChanged)
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListClick, self.lstCards)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnListActivate, self.lstCards)
		self.Bind(wx.EVT_LIST_COL_CLICK, self.OnListColumnClick, self.lstCards)

		EVT_ADD_CARD(self.panelDecks, self.OnAddCard)
		EVT_ADD_IN_PLAY_CARD(self.panelDecks, self.OnAddCardInPlay)
		EVT_REMOVE_CARD(self.panelDecks, self.OnRemoveCard)
		EVT_REMOVE_IN_PLAY_CARD(self.panelDecks, self.OnRemoveCard)
		EVT_SELECT_CARD(self.panelDecks, self.OnSelectCard)

		self.UpdateCards()

	def SetDeck(self, deck):
		self.panelDecks.SetDeck(deck)

	def AddCard(self, cdid, num=1, inPlay=False):
		GetCurrentDeck().Add(cdid, num, inPlay)
		GetCurrentDeck().modified = True
		self.panelDecks.Add(cdid, num, inPlay)
		wx.FindWindowById(ID_MAIN_WINDOW).UpdateStatus()

	def OnAddCardInPlay(self, event):
		if event.id is None:
			idx = self.lstCards.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
			if idx == -1:
				return
			cdid = self.cardMap[self.lstCards.GetItemData(idx)]
		else:
			cdid = event.id

		self.AddCard(cdid, event.num, True)

	def OnAddCard(self, event):
		if event.id is None:
			idx = self.lstCards.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
			if idx == -1:
				return
			cdid = self.cardMap[self.lstCards.GetItemData(idx)]
		else:
			cdid = event.id

		self.AddCard(cdid, event.num)

##	def OnRemoveCardInPlay(self, event):
##		deck = GetCurrentDeck()
##		deck.Remove(event.cdid, event.num)
##		deck.modified = True
##		wx.FindWindowById(ID_MAIN_WINDOW).UpdateStatus()

	def OnRemoveCard(self, event):
		deck = GetCurrentDeck()
		deck.Remove(event.cdid, event.num)
		deck.modified = True
		wx.FindWindowById(ID_MAIN_WINDOW).UpdateStatus()

	def UpdateCards(self):
		filter = self.panelFilters.GetFilter()
		self.cardMap = []

		self.lstCards.DeleteAllItems()
		for card in database.get():
			if not filter(card):
				continue
			idx = self.lstCards.InsertStringItem(self.CARDLIST_COL_NAME, card.name)
			#self.lstCards.SetStringItem(idx, self.CARDLIST_COL_ID, card.id)
			self.lstCards.SetStringItem(idx, self.CARDLIST_COL_TYPE, card.type.capitalize())  # Type
			self.lstCards.SetStringItem(idx, self.CARDLIST_COL_CLANS, ', '.join(clan.capitalize() for clan in card.clans))  # Clans
			self.lstCards.SetStringItem(idx, self.CARDLIST_COL_COST, card.cost)  # Cost
			if card.type in ['personality', 'item', 'follower', 'ancestor']:
				self.lstCards.SetStringItem(idx, self.CARDLIST_COL_FORCECHI, '%sF/%sC' % (card.force, card.chi))
			self.lstCards.SetStringItem(idx, self.CARDLIST_COL_PH, card.personal_honor)
			self.lstCards.SetStringItem(idx, self.CARDLIST_COL_HR, card.honor_req)
			#ctext = re.sub('< */? *\w+ */?\ *>', '', card.text.replace('<br>', '\n'))
			#self.lstCards.SetStringItem(idx, self.CARDLIST_COL_TEXT, ctext)  # Text -- simple regex to strip simple HTML
			self.lstCards.SetStringItem(idx, self.CARDLIST_COL_FOCUS, card.focus)

			self.lstCards.SetItemData(idx, len(self.cardMap))
			self.cardMap.append(card.id)

		self.lstCards.SortItems(CardNameSorter(self.cardMap))

	def OnListClick(self, event):
		idx = event.GetIndex()
		cdid = self.cardMap[self.lstCards.GetItemData(idx)]
		self.panelDecks.Deselect()
		wx.FindWindowById(ID_CARD_PREVIEW).SetCard(cdid)

	def OnListActivate(self, event):
		cdid = self.cardMap[self.lstCards.GetItemData(event.GetIndex())]
		card = database.get()[cdid]
		isStronghold = False
		if card.type == "stronghold":
			isStronghold = True
		self.AddCard(cdid, inPlay = isStronghold)

	def OnListColumnClick(self, event):
		sorters = {
			self.CARDLIST_COL_NAME: CardNameSorter,
			self.CARDLIST_COL_TYPE: CardTypeSorter,
			self.CARDLIST_COL_CLANS: CardClanSorter,
			self.CARDLIST_COL_COST: CardCostSorter,
			self.CARDLIST_COL_FORCECHI: CardForceChiSorter,
			self.CARDLIST_COL_FOCUS: CardFocusSorter,
			self.CARDLIST_COL_PH: CardPHSorter,
			self.CARDLIST_COL_HR: CardHonorReqSorter,
		}
		try:
			sortobj = sorters[event.GetColumn()](self.cardMap)
		except KeyError:
			return
		self.lstCards.SortItems(sortobj)

	def OnFiltersChanged(self, event):
		self.UpdateCards()

	def OnSelectCard(self, event):
		idx = self.lstCards.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
		if idx != -1:
			self.lstCards.SetItemState(idx, 0, wx.LIST_STATE_SELECTED)

	def Activate(self):
		pass


class MainWindow(wx.Frame):
	def __init__(self, parent=None, id=ID_MAIN_WINDOW, title=MAIN_TITLE):
		wx.Frame.__init__(self, parent, id, title, size=(960, 580))

		self.CreateStatusBar(number=4)
		self.GetStatusBar().SetStatusWidths([-65, -15, -10, -10])

		# Splitter between card preview and everything else
		splitterMain = wx.SplitterWindow(self)
		self.cardPreview = preview.CardPreviewWindow(splitterMain, id=ID_CARD_PREVIEW)

		# Notebook with the various deck views
		self.noteViews = wx.Notebook(splitterMain)
		self.panelEdit = DeckEditPanel(self.noteViews)
		self.noteViews.AddPage(self.panelEdit, 'Edit Deck')
		self.noteViews.AddPage(DeckPlaintextPanel(self.noteViews), 'Plaintext')
		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnViewChange, self.noteViews)

		# Split the main splitter
		splitterMain.SetMinimumPaneSize(180)
		splitterMain.SplitVertically(self.cardPreview, self.noteViews, 180)
		splitterMain.SetSashGravity(0.0)

		# Menus
		try:
			self.recent_files = [line.strip() for line in file(RECENT_FILES_FILE).readlines()]
		except IOError:
			self.recent_files = []

		self.mnuFile = wx.Menu()
		self.mnuFile.Append(ID_DE_MNU_NEW_DECK, 'New deck\tCtrl+N', 'Create a new, empty deck.')
		self.mnuFile.Append(ID_DE_MNU_OPEN_DECK, 'Open deck...\tCtrl+O', 'Open an existing deck.')
		self.mnuFile.Append(ID_DE_MNU_SAVE_DECK, 'Save deck\tCtrl+S', 'Save the current deck.')
		self.mnuFile.Append(ID_DE_MNU_SAVE_DECK_AS, 'Save deck as...\tCtrl+Shift+S', 'Save the current deck with a new name.')
		self.mnuFile.AppendSeparator()
		self.recent_files_pos = self.mnuFile.GetMenuItemCount()
		self.mnuFile.AppendSeparator()
		self.mnuFile.Append(wx.ID_EXIT, 'Exit', 'Close the deck editor.')

		self.mnuEdit = wx.Menu()
		self.mnuEdit.Append(ID_DE_MNU_EDIT_OUTPUT_HTML, 'Copy deck as HTML', 'Copy current deck list to the clipboard in HTML format.')
		self.mnuEdit.Append(ID_DE_MNU_EDIT_OUTPUT_BBCODE, 'Copy deck as BBCode', 'Copy current deck list to the clipboard in BBCode format.')
		self.mnuEdit.AppendSeparator()
		self.mnuEdit.Append(ID_DE_MNU_IMPORT_GEMPUKKU, 'Import a Gempukku deck', 'Import a deck saved in Gempukku.')
		self.mnuEdit.Append(ID_DE_MNU_IMPORT_THEGAME, 'Import \'The Game\' deck', 'Import a deck saved in \'The Game\'.')
		self.mnuEdit.AppendSeparator()
		self.mnuEdit.Append(ID_DE_MNU_IMPORT_CLIPBOARD, 'Import from clipboard\tCtrl+Shift+I', 'Import deck list from clipboard.')

		menubar = wx.MenuBar()
		menubar.Append(self.mnuFile, '&File')
		menubar.Append(self.mnuEdit, '&Edit')

		self.SetMenuBar(menubar)

		# Events
		wx.EVT_MENU(self, ID_DE_MNU_NEW_DECK, self.OnMenuNewDeck)
		wx.EVT_MENU(self, ID_DE_MNU_OPEN_DECK, self.OnMenuOpenDeck)
		wx.EVT_MENU(self, ID_DE_MNU_SAVE_DECK, self.OnMenuSaveDeck)
		wx.EVT_MENU(self, ID_DE_MNU_SAVE_DECK_AS, self.OnMenuSaveDeckAs)
		wx.EVT_MENU(self, ID_DE_MNU_IMPORT_THEGAME, self.OnMenuImportTheGame)
		wx.EVT_MENU(self, ID_DE_MNU_IMPORT_GEMPUKKU, self.OnMenuImportGempukku)
		wx.EVT_MENU(self, ID_DE_MNU_IMPORT_CLIPBOARD, self.OnMenuImportClipboard)
		wx.EVT_MENU(self, ID_DE_MNU_EDIT_OUTPUT_HTML, self.OnCopyHTMLDecklistToClipboard)
		wx.EVT_MENU(self, ID_DE_MNU_EDIT_OUTPUT_BBCODE, self.OnCopyBBCodeDecklistToClipboard)
		wx.EVT_MENU(self, wx.ID_EXIT, self.OnMenuExit)
		wx.EVT_MENU_RANGE(self, ID_DE_MNU_RECENT, ID_DE_MNU_RECENT+NUM_RECENT, self.OnMenuRecent)
		wx.EVT_CLOSE(self, self.OnClose)

		if hasattr(sys, 'frozen'):
			try:
				import win32api
				self.SetIcon(wx.Icon('deckedit.exe', wx.BITMAP_TYPE_ICO))
			except:
				self.SetIcon(wx.Icon(os.path.join(settings.data_dir, 'images/iconedit.ico'), wx.BITMAP_TYPE_ICO))
		else:
			self.SetIcon(wx.Icon(os.path.join(settings.data_dir, 'images/iconedit.ico'), wx.BITMAP_TYPE_ICO))

		self.deck = None
		self.deckName = None

		self.UpdateRecentFiles()
		self.NewDeck()
		self.Show()

	def ConvertDeckFromTheGame(self, filename):
		try:
			converter = deck.TheGameDeckConverter(filename)
			self.deck = converter.convert()
		except:
			wx.MessageDialog(self, 'There was an error converting the file from \'The Game\' to Egg of P\'an Ku', 'Deck Error', wx.ICON_ERROR).ShowModal()
			return

		self.panelEdit.SetDeck(self.deck)
		self.deckName = None
		self.deck.modified = True
		self.noteViews.GetCurrentPage().Activate()
		self.UpdateStatus()

	def ConvertDeckFromGempukku(self, filename):
		try:
			converter = deck.GempukkuDeckConverter(filename)
			self.deck = converter.convert()
		except:
			wx.MessageDialog(self, 'There was an error converting the file from Gempukku to Egg of P\'an Ku', 'Deck Error', wx.ICON_ERROR).ShowModal()
			return

		self.panelEdit.SetDeck(self.deck)
		self.deckName = None
		self.deck.modified = True
		self.noteViews.GetCurrentPage().Activate()
		self.UpdateStatus()

	def NewDeck(self):
		if self.deck and self.deck.modified and not self.QuerySaveFirst():
			return

		self.deck = deck.Deck()
		self.deckName = None
		self.panelEdit.SetDeck(self.deck)
		self.UpdateStatus()

	def UpdateStatus(self):
		cardDB = database.get()
		self.SetStatusText('%d Fate/%d Dynasty' % (self.deck.NumFate(), self.deck.NumDynasty()), 1)
		self.SetStatusText('%d Holdings' %
			sum([num for num, c, inplay in self.deck if cardDB[c].type == "holding"]), 2)
		if self.deckName is not None:
			self.SetTitle(MAIN_TITLE + ' - %s%s' % (self.deckName, '*' if self.deck.modified else ''))
		else:
			self.SetTitle(MAIN_TITLE)

	def SaveDeck(self):
		if not self.deckName and not self.PickSaveName():
				return

		self.deck.Save(file(self.deckName, 'wb'), deck.OUTPUT_TYPES.Text)
		self.deck.modified = False
		self.RecentlyUsed(self.deckName)
		self.UpdateStatus()

	def OpenDeck(self, filename):
		try:
			self.deck = deck.Deck.load(file(filename, 'rb'))
		except deck.LoadCardsNotFoundError, ei:
			wx.MessageDialog(self, '%s\n' % ei, 'Load Deck Error', wx.ICON_ERROR).ShowModal()
			self.deck = ei.loadedDeck
		except deck.InvalidCardError, e:
			wx.MessageDialog(self, 'A card in the deck (%s) was not found in the card database.\n' \
				'This could be because your card database is outdated, missing some cards, or ' \
				'because the deck is invalid somehow.' % e.card, 'Deck Error', wx.ICON_ERROR).ShowModal()
			return
		except IOError:
			wx.MessageDialog(self, 'The specified deck file could not be opened.\nMake sure the path ' \
				'entered exists.', 'Deck Error', wx.ICON_ERROR).ShowModal()
			return

		self.panelEdit.SetDeck(self.deck)
		self.deckName = filename
		self.noteViews.GetCurrentPage().Activate()
		self.RecentlyUsed(self.deckName)
		self.UpdateStatus()

	def OpenDeckFromClipboard(self):
		try:
			if not wx.TheClipboard.IsOpened():
				wx.TheClipboard.Open()
				do = wx.TextDataObject()
				success = wx.TheClipboard.GetData(do)
				if success:
					data = do.GetText()
				wx.TheClipboard.Close()
			self.deck = deck.Deck.loadFromClipboard(data)
		except deck.ImportCardsNotFoundError, ei:
			wx.MessageDialog(self, '%s\n' % ei, 'Import Error', wx.ICON_ERROR).ShowModal()
			self.deck = ei.importedDeck
		except deck.InvalidCardError, e:
			wx.MessageDialog(self, 'A card in the deck (%s) was not found in the card database.\n' \
				'This could be because your card database is outdated, missing some cards, or ' \
				'because the deck is invalid somehow.' % e.card, 'Import Error', wx.ICON_ERROR).ShowModal()
			return
		self.panelEdit.SetDeck(self.deck)
		self.deckName = None
		self.deck.modified = True
		self.noteViews.GetCurrentPage().Activate()
		self.UpdateStatus()

	def SaveToClipboard(self, textformat):
		win32clipboard.OpenClipboard()
		win32clipboard.EmptyClipboard()
		io = StringIO.StringIO()
		GetCurrentDeck().Save(io, textformat)
		win32clipboard.SetClipboardData(win32clipboard.CF_TEXT,io.getvalue())
		win32clipboard.CloseClipboard()

	def PickSaveName(self):
		dlg = wx.FileDialog(self, wildcard=FILE_DIALOG_WILDCARD, defaultDir=settings.last_deck, style=wx.SAVE|wx.OVERWRITE_PROMPT)
		if dlg.ShowModal() == wx.ID_OK:
			self.deckName = dlg.GetPath()
			return True
		return False

	def QuerySaveFirst(self):
		"""Ask the user if he wants to save his current deck first."""
		result = wx.MessageDialog(self, 'Your current deck has changed. Do you want to save it first?', \
			'Save first?', wx.ICON_QUESTION|wx.YES_NO|wx.CANCEL).ShowModal()
		if result == wx.ID_CANCEL:
			return False
		elif result == wx.ID_YES:
			self.SaveDeck()
		return True

	def UpdateRecentFiles(self):
		for idx in xrange(NUM_RECENT):
			obj = self.mnuFile.FindItemById(ID_DE_MNU_RECENT + idx)
			if obj:
				self.mnuFile.DeleteItem(obj)
		for num, fn in enumerate(self.recent_files):
			self.mnuFile.Insert(self.recent_files_pos + num, ID_DE_MNU_RECENT + num, "&%d %s" % (num + 1, fn), )

	def RecentlyUsed(self, name):
		try:
			self.recent_files.remove(name)
		except ValueError:
			pass
		self.recent_files.insert(0, name)
		self.recent_files = self.recent_files[:NUM_RECENT]
		file(RECENT_FILES_FILE, 'wb').write('\n'.join(self.recent_files))
		self.UpdateRecentFiles()

	def OnViewChange(self, event):
		self.noteViews.GetCurrentPage().Activate()
		event.Skip()

	def OnClose(self, event):
		if event.CanVeto():
			if self.deck and self.deck.modified and not self.QuerySaveFirst():
				event.Veto()
				return
		self.Destroy()

	def OnMenuNewDeck(self, event):
		self.NewDeck()

	def OnMenuOpenDeck(self, event):
		if self.deck and self.deck.modified and not self.QuerySaveFirst():
			return

		dlg = wx.FileDialog(self, wildcard=FILE_DIALOG_WILDCARD, defaultDir=settings.last_deck, style=wx.OPEN|wx.FILE_MUST_EXIST)
		if dlg.ShowModal() == wx.ID_OK:
			self.OpenDeck(dlg.GetPath())

	def OnMenuRecent(self, event):
		idx = event.GetId() - ID_DE_MNU_RECENT
		self.OpenDeck(self.recent_files[idx])

	def OnMenuSaveDeck(self, event):
		self.SaveDeck()

	def OnMenuSaveDeckAs(self, event):
		if self.PickSaveName():
			self.SaveDeck()

	def OnMenuExit(self, event):
		self.Close()

	def OnCopyBBCodeDecklistToClipboard(self, event):
		self.SaveToClipboard(deck.OUTPUT_TYPES.BBCode)

	def OnCopyHTMLDecklistToClipboard(self, event):
		self.SaveToClipboard(deck.OUTPUT_TYPES.HTML)

	def OnMenuImportClipboard(self, event):
		if self.deck and self.deck.modified and not self.QuerySaveFirst():
			return
		self.OpenDeckFromClipboard()

	def OnMenuImportGempukku(self, event):
		if self.deck and self.deck.modified and not self.QuerySaveFirst():
			return

		dlg = wx.FileDialog(self, wildcard=FILE_DIALOG_GEMPUKKU, defaultDir=settings.last_deck, style=wx.OPEN|wx.FILE_MUST_EXIST)
		if dlg.ShowModal() == wx.ID_OK:
			self.ConvertDeckFromGempukku(dlg.GetPath())


	def OnMenuImportTheGame(self, event):
		if self.deck and self.deck.modified and not self.QuerySaveFirst():
			return
		dlg = wx.FileDialog(self, wildcard=FILE_DIALOG_THEGAME, defaultDir=settings.last_deck, style=wx.OPEN|wx.FILE_MUST_EXIST)
		if dlg.ShowModal() == wx.ID_OK:
			self.ConvertDeckFromTheGame(dlg.GetPath())

if __name__ == "__main__":
	# If we've got psyco, we should use it.
	try:
		import psyco
		psyco.profile()
	except ImportError:
		pass

	try:
		app = wx.PySimpleApp()
		if dbimport.EnsureExists():
			frame = MainWindow()
			app.MainLoop()
	finally:
		del app

