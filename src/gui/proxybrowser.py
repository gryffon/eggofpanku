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
	Proxy Browser module for Egg of P'an Ku.

author: Ryan Karetas
file: proxybrowser.py
date: 14 Aug 2014
"""

import wx.lib.newevent
import sys
import os
import StringIO

#Use for testing
if __name__ == "__main__":
	import os
	parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	os.sys.path.insert(0,parentdir)

#Local Import
from gui import card_filters, preview
from db import database, dbimport
from db import proxydb


from settings.xmlsettings import settings
from settings.xmlsettings import locationsettings

MAIN_TITLE = 'Egg of P\'an Ku Proxy Database Browser'

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
		self.proxdb = proxydb.ProxyDB()
		self.cardDB = self.proxdb.get_all_cards()
		self.cardmap = cardmap
		print cardmap

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

		self.SetSizer(panelsizer)

		self.cardMap = []

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


class ProxyBrowsePanel(wx.Panel):
	"""Deck editor panel, allowing editing of the deck."""

	CARDLIST_COL_NAME = 0
	CARDLIST_COL_TYPE = 1
	CARDLIST_COL_CLANS = 2
	CARDLIST_COL_COST = 3
	CARDLIST_COL_FORCECHI = 4
	CARDLIST_COL_PH = 5
	CARDLIST_COL_HR = 6


	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

		self.proxdb = proxydb.ProxyDB()

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.lstCards = wx.ListCtrl(self, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES)
		self.lstCards.InsertColumn(self.CARDLIST_COL_NAME,	 "Name", wx.LIST_FORMAT_LEFT,	 140)
		self.lstCards.InsertColumn(self.CARDLIST_COL_TYPE,	 "Type", wx.LIST_FORMAT_CENTRE,   80)
		self.lstCards.InsertColumn(self.CARDLIST_COL_CLANS,	"Factions", wx.LIST_FORMAT_LEFT, 80)
		self.lstCards.InsertColumn(self.CARDLIST_COL_COST,	 "Cost", wx.LIST_FORMAT_CENTRE,   48)
		self.lstCards.InsertColumn(self.CARDLIST_COL_FORCECHI, "F/C", wx.LIST_FORMAT_CENTRE,	64)
		self.lstCards.InsertColumn(self.CARDLIST_COL_PH,	   "PH", wx.LIST_FORMAT_CENTRE,	 32)
		self.lstCards.InsertColumn(self.CARDLIST_COL_HR,	   "HR", wx.LIST_FORMAT_CENTRE,	 32)
		sizer.Add(self.lstCards, 1, wx.EXPAND|wx.ALL, 5)

		# Filters
		self.panelFilters = FilterPanel(self, size=(120, -1), id=ID_FILTER_PANEL)

		sizer.Add(self.panelFilters, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
		self.SetSizer(sizer)

		EVT_FILTERS_CHANGED(self.panelFilters, self.OnFiltersChanged)
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListClick, self.lstCards)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnListActivate, self.lstCards)
		self.Bind(wx.EVT_LIST_COL_CLICK, self.OnListColumnClick, self.lstCards)

		self.UpdateCards()

	def OldUpdateCards(self):
		filter = self.panelFilters.GetFilter()
		self.cardMap = []

		self.lstCards.DeleteAllItems()
		for card in database.get():
			if not filter(card):
				continue
			idx = self.lstCards.InsertStringItem(self.CARDLIST_COL_NAME, card.name)
			self.lstCards.SetStringItem(idx, self.CARDLIST_COL_TYPE, card.type.capitalize())  # Type
			self.lstCards.SetStringItem(idx, self.CARDLIST_COL_CLANS, ', '.join(clan.capitalize() for clan in card.clans))  # Clans
			self.lstCards.SetStringItem(idx, self.CARDLIST_COL_COST, card.cost)  # Cost
			if card.type in ['personality', 'item', 'follower', 'ancestor']:
				self.lstCards.SetStringItem(idx, self.CARDLIST_COL_FORCECHI, '%sF/%sC' % (card.force, card.chi))
			self.lstCards.SetStringItem(idx, self.CARDLIST_COL_PH, card.personal_honor)
			self.lstCards.SetStringItem(idx, self.CARDLIST_COL_HR, card.honor_req)


			self.lstCards.SetItemData(idx, len(self.cardMap))
			self.cardMap.append(card.id)

		self.lstCards.SortItems(CardNameSorter(self.cardMap))

	def UpdateCards(self):
		filter = self.panelFilters.GetFilter()
		self.cardMap = []

		self.lstCards.DeleteAllItems()
		for card in self.proxdb.get_all_cards():
			#if not filter(card):
			#	continue
			idx = self.lstCards.InsertStringItem(self.CARDLIST_COL_NAME, card.name)
			card_type = self.proxdb.get_card_type(card.type)
			self.lstCards.SetStringItem(idx, self.CARDLIST_COL_TYPE, card_type.type)  # Type
			#self.lstCards.SetStringItem(idx, self.CARDLIST_COL_CLANS, card.clans)  # Clans
			self.lstCards.SetStringItem(idx, self.CARDLIST_COL_COST, str(card.cost))  # Cost
			if card_type.type in ['Personality', 'Item', 'Follower', 'Ancestor']:
				self.lstCards.SetStringItem(idx, self.CARDLIST_COL_FORCECHI, '%sF/%sC' % (card.force, card.chi))
			if card.personal_honor is None:
				ph = "-"
			else:
				ph = card.personal_honor
			self.lstCards.SetStringItem(idx, self.CARDLIST_COL_PH, str(ph))
			if card.honor_req is None:
				hr = "-"
			else:
				hr = card.personal_honor
			self.lstCards.SetStringItem(idx, self.CARDLIST_COL_HR, str(hr))


			self.lstCards.SetItemData(idx, len(self.cardMap))
			self.cardMap.append(card.id)

		self.lstCards.SortItems(CardNameSorter(self.cardMap))

	def OnListClick(self, event):
		idx = event.GetIndex()
		cdid = self.cardMap[self.lstCards.GetItemData(idx)]
		wx.FindWindowById(ID_CARD_PREVIEW).SetCard(cdid, use_db = True, proxy = True)

	def OnListActivate(self, event):
		cdid = self.cardMap[self.lstCards.GetItemData(event.GetIndex())]
		card = database.get()[cdid]
		isStronghold = False
		if card.type == "stronghold":
			isStronghold = True


	def OnListColumnClick(self, event):
		sorters = {
			self.CARDLIST_COL_NAME: CardNameSorter,
			self.CARDLIST_COL_TYPE: CardTypeSorter,
			self.CARDLIST_COL_CLANS: CardClanSorter,
			self.CARDLIST_COL_COST: CardCostSorter,
			self.CARDLIST_COL_FORCECHI: CardForceChiSorter,
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
		self.panelEdit = ProxyBrowsePanel(self.noteViews)
		self.noteViews.AddPage(self.panelEdit, 'Browse Database')
		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnViewChange, self.noteViews)

		# Split the main splitter
		splitterMain.SetMinimumPaneSize(180)
		splitterMain.SplitVertically(self.cardPreview, self.noteViews, 180)
		splitterMain.SetSashGravity(0.0)

		wx.EVT_CLOSE(self, self.OnClose)

		if hasattr(sys, 'frozen'):
			try:
				import win32api
				self.SetIcon(wx.Icon('deckedit.exe', wx.BITMAP_TYPE_ICO))
			except:
				self.SetIcon(wx.Icon(os.path.join(locationsettings.data_dir, 'images/iconedit.ico'), wx.BITMAP_TYPE_ICO))
		else:
			self.SetIcon(wx.Icon(os.path.join(locationsettings.data_dir, 'images/iconedit.ico'), wx.BITMAP_TYPE_ICO))

		self.deck = None
		self.deckName = None

		self.Show()


	def OnViewChange(self, event):
		self.noteViews.GetCurrentPage().Activate()
		event.Skip()

	def OnClose(self, event):
		if event.CanVeto():
			if self.deck and self.deck.modified and not self.QuerySaveFirst():
				event.Veto()
				return
		self.Destroy()

#Use for testing
if __name__ == "__main__":

	app = wx.PySimpleApp()
	if dbimport.EnsureExists():
		frame = MainWindow()
		app.MainLoop()

