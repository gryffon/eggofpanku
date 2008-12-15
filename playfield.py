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
import wx
import wx.lib.newevent
from OpenGL.GL import *
from PIL import Image
import random

import canvas
import game
import database
import dragdrop
from settings import settings
from guids import *


DEFAULT_PLAYFIELD_HEIGHT = 100

CANVAS_MOVE_SNAP = 5.0  # Distance, in world units, to snap when dragging on the playfield.
CANVAS_TOKEN_SIZE = 5
CANVAS_TOKEN_ARR_W = canvas.CANVAS_CARD_W - CANVAS_TOKEN_SIZE
CANVAS_TOKEN_ARR_H = canvas.CANVAS_CARD_H - CANVAS_TOKEN_SIZE
CANVAS_TOKEN_ARR_DIAM = 7
CANVAS_TOKEN_ANGLE = 30

CANVAS_MARKER_SIZE = 4
CANVAS_MARKER_ARR_W = canvas.CANVAS_CARD_W - CANVAS_MARKER_SIZE
CANVAS_MARKER_ARR_H = canvas.CANVAS_CARD_H - CANVAS_MARKER_SIZE
CANVAS_MARKER_ARR_DIAM = 6
CANVAS_MARKER_ANGLE = 30


CANVAS_BG_PLAIN = 0
CANVAS_BG_GRADIENT_VERT = 1
CANVAS_BG_GRADIENT_HORZ = 2

PlayfieldDoubleClickCardEvent, EVT_PLAYFIELD_DOUBLE_CLICK_CARD = wx.lib.newevent.NewEvent()
PlayfieldWheelClickCardEvent, EVT_PLAYFIELD_WHEEL_CLICK_CARD = wx.lib.newevent.NewEvent()
PlayfieldRightClickCardEvent, EVT_PLAYFIELD_RIGHT_CLICK_CARD = wx.lib.newevent.NewEvent()
PlayfieldCardDropEvent, EVT_PLAYFIELD_CARD_DROP = wx.lib.newevent.NewEvent()
PlayfieldCardHoverEvent, EVT_PLAYFIELD_CARD_HOVER = wx.lib.newevent.NewEvent()
PlayfieldCardAttachEvent, EVT_PLAYFIELD_CARD_ATTACH = wx.lib.newevent.NewEvent()
SearchPileEvent, EVT_SEARCH_PILE = wx.lib.newevent.NewEvent()

def ArrangeTokens(card, number):
	"""Arrange places for a number of tokens on a card."""
	try:
		tokens = card.tokenSpots
	except AttributeError:
		tokens = []
	
	if len(tokens) >= number:
		return
	
	number -= len(tokens)  # We might already have some spots arranged.
	
	while number > 0:
		maxIterations = 20
		while maxIterations > 0:
			pos = (random.uniform(-CANVAS_TOKEN_ARR_W, CANVAS_TOKEN_ARR_W), \
				random.uniform(-CANVAS_TOKEN_ARR_H, CANVAS_TOKEN_ARR_H), \
				random.uniform(-CANVAS_TOKEN_ANGLE, CANVAS_TOKEN_ANGLE))
			for tokpos in tokens:
				if ((tokpos[0]-pos[0]) ** 2 + (tokpos[1]-pos[1]) ** 2) < (CANVAS_TOKEN_ARR_DIAM)**2:
					break
			else:
				break
			maxIterations -= 1
		tokens.append(pos)
		number -= 1
	
	card.tokenSpots = tokens

def ArrangeMarkers(card, number):
	"""Arrange places for a number of tokens on a card."""
	try:
		tokens = card.markerSpots
	except AttributeError:
		tokens = []
	
	if len(tokens) >= number:
		return
	
	number -= len(tokens)  # We might already have some spots arranged.
	while number > 0:
		maxIterations = 20
		while maxIterations > 0:
			pos = (random.uniform(-CANVAS_MARKER_ARR_W, CANVAS_MARKER_ARR_W), \
				random.uniform(-CANVAS_MARKER_ARR_H, CANVAS_MARKER_ARR_H), \
				random.uniform(-CANVAS_MARKER_ANGLE, CANVAS_MARKER_ANGLE))
			for tokpos in tokens:
				if ((tokpos[0]-pos[0]) ** 2 + (tokpos[1]-pos[1]) ** 2) < (CANVAS_MARKER_ARR_DIAM)**2:
					break
			else:
				break
			maxIterations -= 1
		tokens.append(pos)
		number -= 1
	
	card.markerSpots = tokens


class PlayfieldCanvasBackground:
	def __init__(self):
		self.size = None
		self.filename = None
		self.texture = None
	
	def __nonzero__(self):
		return self.texture is not None
	
	def Load(self, filename):
		img = Image.open(filename)
		
		self.size = img.size
		
		# Make sure it has dimensions 2^n!
		img = img.crop((0, 0, canvas.next_power_of_two(img.size[0]), canvas.next_power_of_two(img.size[1])))
		(width, height) = img.size
		
		self.texcoord = (self.size[0]/float(width), self.size[1]/float(height))
		
		self.texture = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, self.texture)
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, {"RGBA":GL_RGBA, "RGB":GL_RGB}[img.mode], GL_UNSIGNED_BYTE, img.tostring())
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
		
		self.filename = filename
	
class PlayfieldCanvas(canvas.L5RCanvas):
	def __init__(self, parent, id=wx.ID_ANY, eventTarget=None):
		canvas.L5RCanvas.__init__(self, parent, id)
		self.eventTarget = eventTarget or self
		
		self.gameState = None
		self.player = None
		self.isLocal = False
		
		self.markerPos = None
		self.markerOffset = (0, 0)
		self.attachMarker = None
		
		self.texBorderFrame = self.LoadTexture("images/border2.png")
		self.texAttach = self.LoadTexture("images/border3.png")
		
		wx.EVT_LEFT_DOWN(self, self.OnLeftMouseDown)
		wx.EVT_LEFT_DCLICK(self, self.OnDoubleClick)
		wx.EVT_RIGHT_DOWN(self, self.OnRightMouseDown)
		wx.EVT_MOTION(self, self.OnMotion)
		wx.EVT_MOUSEWHEEL(self, self.OnMouseWheel)
		wx.EVT_MIDDLE_DOWN(self,self.OnMouseWheelDown)
		
		self.SetDropTarget(dragdrop.CardDropTarget(self.OnDragData, self.OnDragOver, self.OnDragLeave))
		
		self.texToken = {}
		self.texMarker = {}
		self.contextCard = None
		self.hoverCard = None
		self.pfHeight = DEFAULT_PLAYFIELD_HEIGHT
		self.background = PlayfieldCanvasBackground()
	
	def DrawBackground(self):
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		w, h = self.GetSize()
		glOrtho(-w/2, w/2, h/2, -h/2, -1, 1)
		
		if settings.playfield_bg_mode == 0:  # Solid
			glClearColor(settings.playfield_bg_color1[0]/256.0,
				settings.playfield_bg_color1[1]/256.0,
				settings.playfield_bg_color1[2]/256.0,
				1)
			glClear(GL_COLOR_BUFFER_BIT)
		elif settings.playfield_bg_mode == 1:  # Vertical gradient
			glDisable(GL_TEXTURE_2D)
			glBegin(GL_QUADS)
			glColor4f(settings.playfield_bg_color1[0]/256.0,
				settings.playfield_bg_color1[1]/256.0,
				settings.playfield_bg_color1[2]/256.0, 1)
			glVertex2f(w/2, -h/2)
			glVertex2f(-w/2, -h/2)
			glColor4f(settings.playfield_bg_color2[0]/256.0,
				settings.playfield_bg_color2[1]/256.0,
				settings.playfield_bg_color2[2]/256.0, 1)
			glVertex2f(-w/2, h/2)
			glVertex2f(w/2, h/2)
			glEnd()
		elif settings.playfield_bg_mode == 2:  # Vertical gradient
			glDisable(GL_TEXTURE_2D)
			glBegin(GL_QUADS)
			glColor4f(settings.playfield_bg_color1[0]/256.0,
				settings.playfield_bg_color1[1]/256.0,
				settings.playfield_bg_color1[2]/256.0, 1)
			glVertex2f(-w/2, -h/2)
			glVertex2f(-w/2, h/2)
			glColor4f(settings.playfield_bg_color2[0]/256.0,
				settings.playfield_bg_color2[1]/256.0,
				settings.playfield_bg_color2[2]/256.0, 1)
			glVertex2f(w/2, h/2)
			glVertex2f(w/2, -h/2)
			glEnd()
		
		# Background... maybe.
		if settings.playfield_bg_image_display:
			if self.background.filename != settings.playfield_bg_image:
				self.background.Load(settings.playfield_bg_image)
			
			if self.background:
				
				glEnable(GL_TEXTURE_2D)
				glBindTexture(GL_TEXTURE_2D, self.background.texture)
				
				glBegin(GL_QUADS)
				glTexCoord2f(0, self.background.texcoord[1]); glVertex2f(-self.background.size[0]/2, self.background.size[1]/2)
				glTexCoord2f(self.background.texcoord[0], self.background.texcoord[1]); glVertex2f(self.background.size[0]/2, self.background.size[1]/2)
				glTexCoord2f(self.background.texcoord[0], 0); glVertex2f(self.background.size[0]/2, -self.background.size[1]/2)
				glTexCoord2f(0, 0); glVertex2f(-self.background.size[0]/2, -self.background.size[1]/2)
				glEnd()

		self.SetupSize()

	def OnDraw(self):
		glLoadIdentity()
		
		self.DrawBackground()
		
		# Do we have an active state?
		if self.gameState:
			for cgid in self.player.zones[game.ZONE_PLAY].cards:
				card = self.gameState.FindCard(cgid)
				glLoadIdentity()
				glTranslatef(card.x, card.y, 0)
				
				if card.dishonored:
					glRotatef(180.0, 0, 0, 1.0)
				
				if card.tapped:
					glRotatef(90.0, 0, 0, 1.0)
				
				if not card.faceUp:
					self.DrawFacedownCard(card)
				else:
					self.DrawCard(card.data)
				
				# Draw tokens
				ArrangeTokens(card, card.NumTokens())
				tpos = 0
				for token, number in card.tokens.iteritems():
					for i in xrange(number):
						glPushMatrix()
						glTranslatef(card.tokenSpots[tpos][0], card.tokenSpots[tpos][1], 0)
						glRotatef(card.tokenSpots[tpos][2], 0, 0, 1.0)
						self.DrawToken(token)
						glPopMatrix()
						tpos += 1

				# Draw Markers
				ArrangeMarkers(card, card.NumMarkers())
				mpos = 0
				
				for token, number in card.markers.iteritems():
#					print 'PlayfieldCanvas.OnDraw marker = %s' % (token)
					for i in xrange(number):
						glPushMatrix()
						glTranslatef(card.markerSpots[mpos][0], card.markerSpots[mpos][1], 0)
						glRotatef(card.markerSpots[mpos][2], 0, 0, 1.0)
						self.DrawMarkerToken(token)
						glPopMatrix()
						mpos += 1
		
		if self.isLocal:
			if self.markerPos:  # Draw translucent marker if applicable.
				glLoadIdentity()
				glTranslatef(self.markerPos[0], self.markerPos[1], 0)
				if self.contextCard and self.contextCard.tapped:
					glRotatef(90.0, 0, 0, 1.0)
				glColor4f(1.0, 1.0, 0.5, 0.75)
				self.DrawMarker(self.texBorderFrame)
			if self.attachMarker:
				glLoadIdentity()
				glTranslatef(self.attachMarker.x, self.attachMarker.y, 0)
				glColor4f(1.0, 1.0, 1.0, 1.0)
				self.DrawMarker(self.texAttach)

	def DrawMarkerToken(self, token):
		try:
#			print 'PlayfieldCanvas.DrawMarkerToken token = %s' % (token)
			tex = self.texMarker[token]
#			print 'PlayfieldCanvas.DrawMarkerToken tex = %s' % (tex)
		except KeyError:
			try:
				marker = game.FindMarkerTemplate(game, token)
				tokenImage = marker.image
				
			except KeyError:
				tokenImage = game.MARKER_IMAGE_PREFIX + game.MARKER_DEFAULT_IMAGE + game.MARKER_IMAGE_EXTENSION

#			print 'PlayfieldCanvas.DrawMarkerToken tokenImage = %s' % (tokenImage)
			try:
				self.texMarker[token] = self.LoadTexture(tokenImage)
			except IOError:
				defaultImage = game.MARKER_IMAGE_PREFIX + game.MARKER_DEFAULT_IMAGE + game.MARKER_IMAGE_EXTENSION
#				print 'PlayfieldCanvas.DrawMarkerToken Loading defaultImage = %s' % (defaultImage)
				self.texMarker[token] = self.LoadTexture(defaultImage)
		
		glPushMatrix()
		glColor4f(1.0, 1.0, 1.0, 1.0)
		glEnable(GL_TEXTURE_2D)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glBindTexture(GL_TEXTURE_2D, self.texMarker[token])
		glBegin(GL_QUADS)
		glTexCoord2f(0, 0); glVertex2f(-CANVAS_MARKER_SIZE, -CANVAS_MARKER_SIZE)
		glTexCoord2f(0, 1); glVertex2f(-CANVAS_MARKER_SIZE,  CANVAS_MARKER_SIZE)
		glTexCoord2f(1, 1); glVertex2f( CANVAS_MARKER_SIZE,  CANVAS_MARKER_SIZE)
		glTexCoord2f(1, 0); glVertex2f( CANVAS_MARKER_SIZE, -CANVAS_MARKER_SIZE)
		glEnd()
		glPopMatrix()
		
	def DrawToken(self, token):
		try:
			tex = self.texToken[token]
		except KeyError:
			try:
				tokenImage = game.TokenTemplates[game.TokenNames[token]].image
			except KeyError:
				tokenImage = game.TOKEN_DEFAULT_IMAGE
			
			try:
				self.texToken[token] = self.LoadTexture(tokenImage)
			except IOError:
				self.texToken[token] = self.LoadTexture(game.TOKEN_DEFAULT_IMAGE)
		
		glPushMatrix()
		glColor4f(1.0, 1.0, 1.0, 1.0)
		glEnable(GL_TEXTURE_2D)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glBindTexture(GL_TEXTURE_2D, self.texToken[token])
		glBegin(GL_QUADS)
		glTexCoord2f(0, 0); glVertex2f(-CANVAS_TOKEN_SIZE, -CANVAS_TOKEN_SIZE)
		glTexCoord2f(0, 1); glVertex2f(-CANVAS_TOKEN_SIZE,  CANVAS_TOKEN_SIZE)
		glTexCoord2f(1, 1); glVertex2f( CANVAS_TOKEN_SIZE,  CANVAS_TOKEN_SIZE)
		glTexCoord2f(1, 0); glVertex2f( CANVAS_TOKEN_SIZE, -CANVAS_TOKEN_SIZE)
		glEnd()
		glPopMatrix()
		
	def SetupSize(self):
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		x, y = self.GetSize()
		h = self.pfHeight
		w = h * x/y
		self.pfWidth = w
		if self.isLocal:
			glOrtho(-w/2, w/2, canvas.CANVAS_CARD_H + CANVAS_MOVE_SNAP, canvas.CANVAS_CARD_H + CANVAS_MOVE_SNAP - h, -1, 1)
		else:
			glOrtho(w/2, -w/2, canvas.CANVAS_CARD_H + CANVAS_MOVE_SNAP - h, canvas.CANVAS_CARD_H + CANVAS_MOVE_SNAP, -1, 1)
		glMatrixMode(GL_MODELVIEW)
		glViewport(0, 0, x, y)
		#self.Refresh()
	
	def SnapCoords(self, pos):
		"""Return coordinates adjusted for the snap-to-grid setting for this canvas."""
		x, y = pos
		if settings.playfield_snap:
			return (round(x/CANVAS_MOVE_SNAP)*CANVAS_MOVE_SNAP, round(y/CANVAS_MOVE_SNAP)*CANVAS_MOVE_SNAP)
		else:
			return pos
		
	def CoordScreen2World(self, x, y):
		"Converts from screen coordinates to world coordinates. Useful for dragging, etc."
		self.SetCurrent()
		(winx, winy) = self.GetSize()
		
		if self.isLocal:
			worldx = (float(x)/winx - 0.5) * self.pfWidth
			worldy = canvas.CANVAS_CARD_H + CANVAS_MOVE_SNAP - (1.0 - (float(y)/winy)) * self.pfHeight
			return (worldx, worldy)
		else:
			worldx = (0.5 - float(x)/winx) * self.pfWidth
			worldy = canvas.CANVAS_CARD_H + CANVAS_MOVE_SNAP - (float(y)/winy) * self.pfHeight
			return (worldx, worldy)
	
	def FindCardAt(self, px, py):
		"Finds and returns the card pointed to at x/y, or None."
		if not self.gameState:
			return None
		
		(x, y) = self.CoordScreen2World(px, py)
		for cgid in reversed(self.player.zones[game.ZONE_PLAY].cards):
			card = self.gameState.FindCard(cgid)
			if (card.tapped and (card.x-canvas.CANVAS_CARD_H < x < card.x+canvas.CANVAS_CARD_H and \
			card.y-canvas.CANVAS_CARD_W < y < card.y+canvas.CANVAS_CARD_W)) or \
				(not card.tapped and (card.x-canvas.CANVAS_CARD_W < x < card.x+canvas.CANVAS_CARD_W and \
				card.y-canvas.CANVAS_CARD_H < y < card.y+canvas.CANVAS_CARD_H)):
				return card
		
		return None
	
	def OnDoubleClick(self, e):
		#(self, event)
		if not self.gameState or not self.isLocal:
			return
		
		# Locate any cards we're pointing at.
		(x, y) = self.CoordScreen2World(*e.GetPosition())
		card = self.FindCardAt(*e.GetPosition())

#		if self.isLocal:
#			(px, py) = event.GetPosition()
#			(x, y) = self.CoordScreen2World(px, py)
#			card = self.FindCardAt(px, py)
		if card:
			wx.PostEvent(self.eventTarget, PlayfieldDoubleClickCardEvent(card=card))
	
	def OnRightMouseDown(self, e):
		if not self.gameState or not self.isLocal:
			return
		
		# Locate any cards we're pointing at.
		(x, y) = self.CoordScreen2World(*e.GetPosition())
		card = self.FindCardAt(*e.GetPosition())
		
		# Found one?
		if card:
			wx.PostEvent(self.eventTarget, PlayfieldRightClickCardEvent(card=card))
		
	def OnLeftMouseDown(self, e):
		if not self.gameState or not self.isLocal:
			e.Skip()
			return
		
		# Locate any cards we're pointing at.
		(x, y) = self.CoordScreen2World(*e.GetPosition())
		card = self.FindCardAt(*e.GetPosition())
		
		# Found one?
		if card:
			# Start dragging it
			self.markerOffset = (x - card.x, y - card.y)
			top = not e.AltDown()
			
			data = dragdrop.CardDropData(cgid=card.cgid, x=x-card.x, y=y-card.y, top=top, faceUp=card.faceUp)
			src = wx.DropSource(self)
			src.SetData(data)
			self.contextCard = card
			result = src.DoDragDrop(True)
			self.contextCard = None
		
		e.Skip()
	
	def OnDragData(self, x, y, dragdata):
		"""Handle a drag-n-drop operation."""
		if self.isLocal:
			(x, y) = self.CoordScreen2World(x, y)
			sx, sy = self.SnapCoords((x - dragdata.x, y - dragdata.y))
			
			if self.attachMarker:
				card = self.gameState.FindCard(dragdata.cgid)
				wx.PostEvent(self.eventTarget, PlayfieldCardAttachEvent(card=card, target=self.attachMarker, faceUp=dragdata.faceUp))
			else:
				wx.PostEvent(self.eventTarget, PlayfieldCardDropEvent(x=sx, y=sy, cgid=dragdata.cgid, faceUp=dragdata.faceUp))
			
			self.markerPos = None
			self.markerOffset = (0, 0)
			self.attachMarker = None
			
			self.Refresh()
		else:
			return wx.DragNone
		
	def OnDragOver(self, x, y):
		"""Handle drag-n-drop 'over' operation."""
		if self.isLocal:
			card = self.FindCardAt(x, y)
			# If something has attachments, attaching THAT to something else is ugly.
			if card and card is not self.contextCard and (not self.contextCard or not self.contextCard.attached_cards):
				if card.attached_to:  # This effectively treats attached cards as whatever they are attached to.
					card = card.attached_to
				try:
					if card.data.type in settings.attach_ok:
						self.attachMarker = card
						self.markerPos = None
						self.Refresh()
						return
				except AttributeError:
					pass
					
			self.attachMarker = None
			(worldx, worldy) = self.CoordScreen2World(x, y)
			self.markerPos = self.SnapCoords((worldx - self.markerOffset[0], worldy - self.markerOffset[1]))
			self.Refresh()
		else:
			return wx.DragNone
	
	def OnDragLeave(self):
		self.markerPos = None
		self.markerOffset = (0, 0)
		self.Refresh()
		
	def OnMotion(self, event):
		def one_or_many(n):
			if n == 1:
				return 'One %s token'
			else:
				try:
					return ['Two', 'Three', 'Four', 'Five', 'Six',
						'Seven', 'Eight', 'Nine', 'Ten', 'Eleven',
						'Twelve'][n - 2]
				except IndexError:
					return str(n)

		def one_or_manyTokens(n):
			if n == 1:
				return 'One %s token'
			else:
				try:
					return one_or_many(n) + ' %s tokens'
				except IndexError:
					return str(n) + ' %s tokens'

		def one_or_manyMarkers(n):
			if n == 1:
				return 'One %s marker'
			else:
				try:
					return one_or_many(n) + ' %s markers'
				except IndexError:
					return str(n) + ' %s markers'
		
		card = self.FindCardAt(*event.GetPosition())
		if card:
			if self.hoverCard is not card:
				self.hoverCard = card
				wx.PostEvent(self.eventTarget, PlayfieldCardHoverEvent(card=card))
				
				if card.faceUp:
					s = [card.GetName()]
				else:
					if card.data:
						s = ['%s (face down)' % card.GetName()]
					elif card.IsDynasty():
						s = ['Facedown Dynasty Card']
					else:
						s = ['Facedown Fate Card']
				s += [(one_or_manyTokens(num) % type) for type, num in card.tokens.iteritems()]
				s += [(one_or_manyMarkers(num) % type) for type, num in card.markers.iteritems()]
				self.SetToolTipString('\n'.join(s))
		else:
			self.SetToolTip(None)
			self.hoverCard = None

	def Setup(self, state, player, local):
		self.gameState = state
		self.player = player
		self.isLocal = local
	
	def SetPlayfieldHeight(self, height):
		self.pfHeight = height
		self.SetupSize()
		self.Refresh()
	
	def OnMouseWheel(self, event):
		delta = event.GetWheelRotation()
		height = min(400, max(30, self.pfHeight - delta/10))
		self.SetPlayfieldHeight(height)

	def OnMouseWheelDown(self, e):
		#(self, event)
		if not self.gameState or not self.isLocal:
			return
		
		# Locate any cards we're pointing at.
		(x, y) = self.CoordScreen2World(*e.GetPosition())
		card = self.FindCardAt(*e.GetPosition())

		if card:
			wx.PostEvent(self.eventTarget, PlayfieldWheelClickCardEvent(card=card))

		
class MiniPile(wx.Panel):
	def __init__(self, parent, id=wx.ID_ANY, player=None, zid=0, name='', bitmap=None):
		wx.Panel.__init__(self, parent, id, size=(12, 12))
		self.bitmap = bitmap
		wx.EVT_PAINT(self, self.OnPaint)
		wx.EVT_RIGHT_DOWN(self, self.OnRightMouseDown)
		self.SetToolTipString(name)
	
	def OnPaint(self, event):
		dc = wx.PaintDC(self)
		if self.bitmap:
			dc.Blit(0, 0, self.bitmap.GetWidth(), self.bitmap.GetHeight(), wx.MemoryDC(self.bitmap), 0, 0)

	def OnRightMouseDown(self, evt):
		pileMenu = wx.Menu()
		pileMenu.Append(ID_MNU_PILEPOPUP_SEARCH, 'Look through...')
		self.PopupMenu(pileMenu)

class Playfield(wx.Panel):
	def __init__(self, parent):
		try:
			style = wx.BORDER_THEME
		except AttributeError:
			pass
		wx.Panel.__init__(self, parent, style=style)
		
		# Info panel up top
		self.infoPanel = wx.Panel(self)
		self.infoPanel.SetBackgroundColour((0, 0, 0))
		
		# Name label
		self.label = wx.StaticText(self.infoPanel)
		self.label.SetForegroundColour((255, 255, 255))
		
		# Icons
		self.discardFate = MiniPile(self.infoPanel, player=None, zid=game.ZONE_DISCARD_FATE, name='Fate Discard Pile',
			bitmap=wx.Bitmap('images/tiny_fate.png'))
		self.discardDynasty = MiniPile(self.infoPanel, player=None, zid=game.ZONE_DISCARD_DYNASTY, name='Dynasty Discard Pile',
			bitmap=wx.Bitmap('images/tiny_dynasty.png'))
		wx.EVT_MENU(self.discardFate, ID_MNU_PILEPOPUP_SEARCH, self.OnFateSearch)
		wx.EVT_MENU(self.discardDynasty, ID_MNU_PILEPOPUP_SEARCH, self.OnDynastySearch)
		
		psizer = wx.BoxSizer(wx.HORIZONTAL)
		psizer.Add(self.discardDynasty, 0, wx.EXPAND|wx.ALL, 1)
		psizer.Add(self.discardFate, 0, wx.EXPAND|wx.ALL, 1)
		psizer.Add(self.label, 0, wx.EXPAND|wx.ALL, 1)
		self.infoPanel.SetSizer(psizer)
		
		# And the rest
		self.canvas = PlayfieldCanvas(self, eventTarget=parent)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.infoPanel, 0, wx.EXPAND, 0)
		sizer.Add(self.canvas, 1, wx.EXPAND, 0)
		self.SetSizer(sizer)
		
		self.infoPanel.Show(False)
	
	def OnFateSearch(self, event):
		wx.PostEvent(self.GetParent(), SearchPileEvent(player=self.player, zid=game.ZONE_DISCARD_FATE))
		
	def OnDynastySearch(self, event):
		wx.PostEvent(self.GetParent(), SearchPileEvent(player=self.player, zid=game.ZONE_DISCARD_DYNASTY))
		
	def Setup(self, gameState, player, local=False):
		"""Set up this playfield, giving it a game state and assigning a player to it."""
		self.gameState = gameState
		self.player = player
		self.canvas.Setup(gameState, player, local)
		
		if local:
			self.infoPanel.Show(False)
		else:
			self.label.SetLabel(player.name)
			self.infoPanel.Show(True)
	
	def Shutdown(self):
		self.canvas.Setup(None, None, False)
		self.infoPanel.Show(False)


class Table(wx.Panel):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

		self.fieldMain = Playfield(self)
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.fieldMain, 1, wx.EXPAND, 0)
		self.SetSizer(sizer)
		
		self.playfields = []
	
	def Shutdown(self):
		self.fieldMain.Shutdown()
		for f in self.playfields:
			f.Destroy()
		self.playfields = []
		self.fieldMain.Show(True)
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.fieldMain, 1, wx.EXPAND, 0)
		self.SetSizer(sizer)
		self.Layout()
		self.Refresh()
	
	def Setup(self, gameState, localplayer=None):
		for f in self.playfields:
			f.Destroy()
		self.playfields = []
		
		# Other playfields.
		for player in gameState.players.itervalues():
			if player is not localplayer:
				pf = Playfield(self)
				pf.Setup(gameState, player, False)
				self.playfields.append(pf)
		
		# Rearrange
		if localplayer is not None:
			self.fieldMain.Setup(gameState, localplayer, True)
			self.fieldMain.Show(True)
			if self.playfields:
				othersizer = wx.BoxSizer(wx.HORIZONTAL)
				for pf in self.playfields:
					othersizer.Add(pf, 1, wx.EXPAND, 0)
				sizer = wx.BoxSizer(wx.VERTICAL)
				sizer.Add(othersizer, 1, wx.EXPAND|wx.BOTTOM, 1)
				sizer.Add(self.fieldMain, 1, wx.EXPAND, 0)
				self.fieldMain.canvas.SetPlayfieldHeight(DEFAULT_PLAYFIELD_HEIGHT)
				self.SetSizer(sizer)
				self.Layout()
			else:
				self.fieldMain.canvas.SetPlayfieldHeight(DEFAULT_PLAYFIELD_HEIGHT * 2)
		else:
			self.fieldMain.Shutdown()
			self.fieldMain.Show(False)
			sizer = wx.BoxSizer(wx.VERTICAL)
			for pf in self.playfields:
				sizer.Add(pf, 1, wx.EXPAND|wx.BOTTOM, 1, 0)
				pf.canvas.SetPlayfieldHeight(DEFAULT_PLAYFIELD_HEIGHT)
			if len(self.playfields) == 1:  # If only one player, fix height.
				self.playfields[0].canvas.SetPlayfieldHeight(DEFAULT_PLAYFIELD_HEIGHT * 2)
			self.SetSizer(sizer)
			self.Layout()
		
		self.Refresh()
