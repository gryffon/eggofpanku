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
"""Deck panels."""
import wx
import os

#Local Import
from game import game
import dragdrop
from guids import *
from settings.xmlsettings import settings

DeckDropCardEvent, EVT_DECK_DROP_CARD = wx.lib.newevent.NewEvent()


class DeckPanel(wx.Panel):
	dragFaceup = False
	
	"""Deck or pile window."""
	def __init__(self, parent, id=wx.ID_ANY, image=None, zname=None, zid=None):
		wx.Panel.__init__(self, parent, id, size=(32, 32))
		
		self.bitmap = None
		if image:
			self.bitmap = wx.Bitmap(image)
		self.gameState = None
		self.zname = zname
		self.zid = zid
		
		wx.EVT_PAINT(self, self.OnPaint)
		wx.EVT_RIGHT_DOWN(self, self.OnRightMouseDown)
		wx.EVT_LEFT_DOWN(self, self.OnLeftMouseDown)
		
		self.SetDropTarget(dragdrop.CardDropTarget(self.OnDragData, self.OnDragOver, self.OnDragLeave))
		self.UpdateTooltip()
	
	def UpdateTooltip(self):
		if self.gameState:
			numcards = len(self.gameState.MyZone(self.zid))
			self.SetToolTipString('%s - %d cards' % (self.zname, numcards))
		else:
			self.SetToolTipString(self.zname)
	
	def OnPaint(self, evt):
		dc = wx.PaintDC(self)
		if self.bitmap:
			dc.Blit(0, 0, self.bitmap.GetWidth(), self.bitmap.GetHeight(), wx.MemoryDC(self.bitmap), 0, 0)
	
	def OnLeftMouseDown(self, evt):
		if not self.gameState:
			return
		
		zone = self.gameState.MyZone(self.zid)
		if len(zone) > 0:  # Do we have cards to move from here?
			if evt.ControlDown():  # Ctrl-drag -> bottom card.
				cgid = zone.BottomCard()
			else:
				cgid = zone.TopCard()
			
			data = dragdrop.CardDropData(cgid=cgid, x=0, y=0, faceUp=self.dragFaceup)
			src = wx.DropSource(self)
			src.SetData(data)
			result = src.DoDragDrop(True)
		
		evt.Skip()
	
	def OnRightMouseDown(self, evt):
		if not self.gameState:
			return
		
		pileMenu = wx.Menu()
		pileMenu.Append(ID_MNU_PILEPOPUP_SEARCH, 'Look through...')
		if self.canShuffle:
			pileMenu.AppendSeparator()
			pileMenu.Append(ID_MNU_PILEPOPUP_SHUFFLE, 'Shuffle')
		self.ExtraMenus(pileMenu)
		
		self.PopupMenu(pileMenu)
		
	def OnDragData(self, x, y, dragdata):
		"""Handle a drag-n-drop operation."""
		if not self.gameState:
			return
		
		# Make sure we can.
		card = self.gameState.FindCard(dragdata.cgid)
		if not self.CanHold(card):
			return wx.DragNone
		
		wx.PostEvent(self, DeckDropCardEvent(zid=self.zid, cgid=dragdata.cgid, top=dragdata.top))
		self.Refresh()
		
	def OnDragOver(self, x, y):
		"""Handle drag-n-drop 'over' operation."""
		pass
	
	def OnDragLeave(self):
		pass

	def SetGameState(self, state):
		self.gameState = state
		self.UpdateTooltip()
	
	def ExtraMenus(self, menu):
		pass
	
class DynastyDeckPanel(DeckPanel):
	canShuffle = True
	
	def __init__(self, parent, id=wx.ID_ANY):
		DeckPanel.__init__(self, parent, id, image=os.path.join(settings.data_dir, 'images/icon_dynasty.png'), zname='Dynasty Deck', zid=game.ZONE_DECK_DYNASTY)
	
	def CanHold(self, card):
		return card.IsDynasty()
	
	def ExtraMenus(self, menu):
		menu.AppendSeparator()
		menu.Append(ID_MNU_DYN_LOOK_TOP, 'Look at top cards...')
		menu.Append(ID_MNU_DYN_LOOK_BOTTOM, 'Look at bottom cards...')
	
class DynastyDiscardPanel(DeckPanel):
	canShuffle = False
	dragFaceup = True
	
	def __init__(self, parent, id=wx.ID_ANY):
		DeckPanel.__init__(self, parent, id, os.path.join(settings.data_dir, 'images/icon_dynasty_discard.png'), zname='Dynasty Discard Pile', zid=game.ZONE_DISCARD_DYNASTY)
	
	def CanHold(self, card):
		return card.IsDynasty()
	
class FateDeckPanel(DeckPanel):
	canShuffle = True
	
	def __init__(self, parent, id=wx.ID_ANY):
		DeckPanel.__init__(self, parent, id, os.path.join(settings.data_dir, 'images/icon_fate.png'), zname='Fate Deck', zid=game.ZONE_DECK_FATE)
	
	def CanHold(self, card):
		return card.IsFate()

	def ExtraMenus(self, menu):
		menu.AppendSeparator()
		menu.Append(ID_MNU_FATE_LOOK_TOP, 'Look at top cards...')
		menu.Append(ID_MNU_FATE_LOOK_BOTTOM, 'Look at bottom cards...')
	

class FateDiscardPanel(DeckPanel):
	canShuffle = False
	dragFaceup = True
	
	def __init__(self, parent, id=wx.ID_ANY):
		DeckPanel.__init__(self, parent, id, os.path.join(settings.data_dir, 'images/icon_fate_discard.png'), zname='Fate Discard Pile', zid=game.ZONE_DISCARD_FATE)

	def CanHold(self, card):
		return card.IsFate()

class RemovedFromGamePanel(DeckPanel):
	canShuffle = False
	dragFaceup = True
	
	def __init__(self, parent, id=wx.ID_ANY):
		DeckPanel.__init__(self, parent, id, os.path.join(settings.data_dir, 'images/icon_removed.png'), zname='Removed-From-Game Zone', zid=game.ZONE_REMOVED)

	def CanHold(self, card):
		return True
