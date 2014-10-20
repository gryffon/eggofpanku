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
"""Card filter module for Egg of P'an Ku. Used by the deck editor."""
import wx
import wx.lib.newevent
import re

#Local Imports
from db import database


# Window-related things
MinMaxEvent, EVT_MIN_MAX = wx.lib.newevent.NewEvent()
FilterInputChangedEvent, EVT_FILTER_INPUT_CHANGED = wx.lib.newevent.NewEvent()

class MinMaxWindow(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.min = wx.TextCtrl(self, size=(32, -1), style=wx.TE_PROCESS_ENTER)
		self.max = wx.TextCtrl(self, size=(32, -1), style=wx.TE_PROCESS_ENTER)
		
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.min, 1, wx.EXPAND|wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 0)
		sizer.Add(wx.StaticText(self, label='-'), 0, wx.EXPAND|wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 3)
		sizer.Add(self.max, 1, wx.EXPAND|wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 0)
		self.SetSizer(sizer)
		
		self.Bind(wx.EVT_TEXT_ENTER, self.OnChange, self.min)
		self.Bind(wx.EVT_TEXT_ENTER, self.OnChange, self.max)
	
	def GetMinValue(self):
		return self.min.GetValue()

	def GetMaxValue(self):
		return self.max.GetValue()

	def OnChange(self, event):
		wx.PostEvent(self, MinMaxEvent(min=self.min.GetValue(), max=self.max.GetValue()))


# Filter base class
class Filter:
	name = '<dummy filter>'
	type = 'none'
	default_enabled = False
	
	def __init__(self):
		self.enabled = self.default_enabled

	def __call__(self, card):
		return self.match(card)

	def OnChange(self, event):
		self.UpdateValue()
		wx.PostEvent(self.ctrl, FilterInputChangedEvent(filter=self))

	def UpdateValue(self):
		pass

class AggregateFilter:
	def __init__(self, filters):
		self.filters = list(filters)
	
	def __call__(self, card):
		return all(filter(card) for filter in self.filters)


# Filter types
class StringFilter(Filter):
	value = ''
	def MakeWindow(self, parent):
		self.ctrl = wx.TextCtrl(parent, style=wx.TE_PROCESS_ENTER)
		parent.Bind(wx.EVT_TEXT_ENTER, self.OnChange, self.ctrl)
		return self.ctrl

	def UpdateValue(self):
		self.value = self.ctrl.GetValue()

class RegexFilter(StringFilter):
	regex = ''
	
	def UpdateValue(self):
		self.value = self.ctrl.GetValue()
		self.regex = re.compile(self.value, re.IGNORECASE)

class ChoiceFilter(Filter):
	value = ''
	options = []
	def MakeWindow(self, parent):
		self.value = self.options[0]
		self.ctrl = wx.ComboBox(parent, style=wx.CB_READONLY)
		for type in self.options:
			self.ctrl.Append(type)
		self.ctrl.SetValue(self.options[0])
		parent.Bind(wx.EVT_COMBOBOX, self.OnChange, self.ctrl)
		return self.ctrl

	def UpdateValue(self):
		self.value = self.ctrl.GetValue()

class IntegerFilter(Filter):
	value = 0
	
	def MakeWindow(self, parent):
		self.ctrl = wx.SpinCtrl(parent, size=(48, -1))
		EVT_SPIN_CTRL(self.ctrl, self.OnChange)
		return self.ctrl

	def UpdateValue(self):
		self.value = int(self.ctrl.GetValue())

class MinMaxFilter(Filter):
	min = 0
	max = 0
	
	def MakeWindow(self, parent):
		self.ctrl = MinMaxWindow(parent)
		EVT_MIN_MAX(self.ctrl, self.OnChange)
		return self.ctrl
	
	def UpdateValue(self):
		self.min = self.ctrl.GetMinValue()
		self.max = self.ctrl.GetMaxValue()

class ConstFilter(Filter):
	def MakeWindow(self, parent):
		return None


# And now, the filters themselves.
class NameFilter(RegexFilter):
	name = 'Card Name'
	def match(self, card):
		return self.regex.search(card.name) is not None

class TextFilter(RegexFilter):
	name = 'Card Text'
	def match(self, card):
		return self.regex.search(card.text) is not None

class TypeFilter(ChoiceFilter):
	name = 'Card Type'
	options = database.cardTypes
	##default_enabled = False #was True
	def match(self, card):
		return self.value.lower() == card.type

class FactionFilter(ChoiceFilter):
	name = 'Faction'
	options = database.factions
	def match(self, card):
		return self.value.lower() in card.clans


class ForceFilter(MinMaxFilter):
	name = 'Force'
	def match(self, card):
		try:
			return card.force \
				and (not self.min or int(self.min) <= int(card.force)) \
				and (not self.max or int(self.max) >= int(card.force))
		except ValueError:
			return False

class ChiFilter(MinMaxFilter):
	name = 'Chi'
	def match(self, card):
		try:
			return card.chi \
				and (not self.min or int(self.min) <= int(card.chi)) \
				and (not self.max or int(self.max) >= int(card.chi))
		except ValueError:
			return False

class CostFilter(MinMaxFilter):
	name = 'Gold Cost'
	def match(self, card):
		try:
			return card.cost \
				and (not self.min or int(self.min) <= int(card.cost)) \
				and (not self.max or int(self.max) >= int(card.cost))
		except ValueError:
			return False

class FocusFilter(MinMaxFilter):
	name = 'Focus Value'
	def match(self, card):
		try:
			return card.focus \
				and (not self.min or int(self.min) <= int(card.focus)) \
				and (not self.max or int(self.max) >= int(card.focus))
		except ValueError:
			return False

class PHFilter(MinMaxFilter):
	name = 'Personal Honor'
	def match(self, card):
		try:
			return card.personal_honor \
				and (not self.min or int(self.min) <= int(card.personal_honor)) \
				and (not self.max or int(self.max) >= int(card.personal_honor))
		except ValueError:
			return False

class HRFilter(MinMaxFilter):
	name = 'Honor Requirement'
	def match(self, card):
		try:
			return card.honor_req \
				and (not self.min or self.min == card.honor_req \
				or int(self.min) <= int(card.honor_req)) \
				and (not self.max or self.max == card.honor_req \
				or int(self.max) >= int(card.honor_req))
		except ValueError:
			return False

class RarityFilter(ChoiceFilter):
	name = 'rarity'
	options = database.rarityFormats.keys()
	def match(self, card):
		return database.rarityFormats[self.value] == card.rarity

class LegalityFilter(ChoiceFilter):
	name = 'Legality'
	options = database.legalityFormats

	def MakeWindow(self, parent):
		
		self.ctrl = wx.ComboBox(parent, style=wx.CB_READONLY)
		for type in sorted(self.options.keys()):
			self.ctrl.Append(type)
			if self.options[type][1] == "True":
				self.value = type
				self.ctrl.SetValue(type)
		parent.Bind(wx.EVT_COMBOBOX, self.OnChange, self.ctrl)
		return self.ctrl

	def match(self, card):
		for name in self.options[self.value][0]:
			if name in card.legal:
				return True

class SetFilter(ChoiceFilter):
	name = 'Set'
	options = database.cardSets.keys()
	def match(self, card):
		return database.cardSets[self.value] in card.images

# Collection of filters.
def AllFilters():
	return (
	('Basic Filters', [
		NameFilter(), TextFilter(), TypeFilter(),
		FactionFilter(),
		]),
	('Card Stats', [
		ForceFilter(), ChiFilter(), CostFilter(),
		HRFilter(), PHFilter(), FocusFilter(), RarityFilter(),
		]),
	('Sets and Formats', [
		LegalityFilter(), SetFilter(),
		]),
	)



