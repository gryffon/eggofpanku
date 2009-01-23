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
"""OpenGL-accelerated L5R canvas window for Egg of P'an Ku."""

import wx
import wx.lib.newevent
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from wx.glcanvas import GLCanvas
from PIL import JpegImagePlugin  # If not explictly imported, py2exe will fail
from PIL import PngImagePlugin   # If not explictly imported, py2exe will fail
from PIL import Image
import random

import game
import database
import dragdrop
#from settings import settings
from xmlsettings import settings


CANVAS_MOVE_SNAP = 5.0  # Distance, in world units, to snap when dragging on the playfield.
CANVAS_TOKEN_SIZE = 5
CANVAS_CARD_W = 10.5
CANVAS_CARD_H = 15.0
CANVAS_TOKEN_ARR_W = CANVAS_CARD_W - CANVAS_TOKEN_SIZE
CANVAS_TOKEN_ARR_H = CANVAS_CARD_H - CANVAS_TOKEN_SIZE
CANVAS_TOKEN_ARR_DIAM = 7
CANVAS_TOKEN_ANGLE = 30

CANVAS_BG_PLAIN = 0
CANVAS_BG_GRADIENT_VERT = 1
CANVAS_BG_GRADIENT_HORZ = 2

PlayfieldDoubleClickCardEvent, EVT_PLAYFIELD_DOUBLE_CLICK_CARD = wx.lib.newevent.NewEvent()
PlayfieldRightClickCardEvent, EVT_PLAYFIELD_RIGHT_CLICK_CARD = wx.lib.newevent.NewEvent()
PlayfieldCardDropEvent, EVT_PLAYFIELD_CARD_DROP = wx.lib.newevent.NewEvent()
PlayfieldCardHoverEvent, EVT_PLAYFIELD_CARD_HOVER = wx.lib.newevent.NewEvent()
PlayfieldCardAttachEvent, EVT_PLAYFIELD_CARD_ATTACH = wx.lib.newevent.NewEvent()

def next_power_of_two(n):
	"""Return the next-highest power of two."""
	n = n - 1;
	n = n | (n >> 1)
	n = n | (n >> 2)
	n = n | (n >> 4)
	n = n | (n >> 8)
	n = n | (n >> 16)
	n = n + 1
	return n

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

class L5RCanvas(GLCanvas):
	def __init__(self, parent, id=wx.ID_ANY, *args, **kwargs):
		GLCanvas.__init__(self, parent, id, *args, **kwargs)
		
		wx.EVT_PAINT(self, self.OnPaint)
		wx.EVT_SIZE(self, self.OnResize)
		wx.EVT_ERASE_BACKGROUND(self, self.EraseBackground)
		
		self.init = 0
		self.SetCurrent()
		self.texBorder = self.LoadTexture("images/border.png")
		self.texFateBack = self.LoadTexture("images/fate_back.jpg")
		self.texDynastyBack = self.LoadTexture("images/dynasty_back.jpg")
		self.texCard = {}
		self.texGeneric = {}
		self.texToken = {}
	
	def EraseBackground(self, evt):
		"""Clear the background."""
		pass  # We do absolutely nothing; it just causes flickering!
	
	def LoadTexture(self, fn):
		self.SetCurrent()
		texid = glGenTextures(1)
		try:
			self.LoadTextureInto(fn, texid)
		except Exception, e:
			glDeleteTextures(texid)
			raise e
		return texid
	
	def LoadTextureInto(self, fn, texid):
		"""Load a texture into an OpenGL texture object."""
		self.SetCurrent()
		
		# Open it with PIL.
		img = Image.open(fn)
		
		# Make sure it has dimensions 2^n!
		img = img.resize((next_power_of_two(img.size[0]), next_power_of_two(img.size[1])))
		(width, height) = img.size
		
		glBindTexture(GL_TEXTURE_2D, texid)
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, {"RGBA":GL_RGBA, "RGB":GL_RGB}[img.mode], GL_UNSIGNED_BYTE, img.tostring())
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
	
	def LoadGeneric(self, type):
		self.texGeneric[type] = self.LoadTexture('images/cards/generic_%s.jpg' % type)
		return self.texGeneric[type]
		
	def DrawMarker(self, tex):
		"""Draw a transparent 'marker' for cards."""
		glPushMatrix()
		
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, tex)
		glBegin(GL_QUADS)
		glTexCoord2f(0, 0); glVertex2f(-CANVAS_CARD_W, -CANVAS_CARD_H)
		glTexCoord2f(0, 1); glVertex2f(-CANVAS_CARD_W, CANVAS_CARD_H)
		glTexCoord2f(0.72, 1); glVertex2f(CANVAS_CARD_W, CANVAS_CARD_H)
		glTexCoord2f(0.72, 0); glVertex2f(CANVAS_CARD_W, -CANVAS_CARD_H)
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
		glColor4f(1.0, 1.0, 1.0, 1.0)  # Border color.
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
		
	def DrawCard(self, card):
		"""Draw a single game card centered on the origin."""
		glPushMatrix()
		
		glColor4f(0.0, 0.0, 0.0, 1.0)  # Border color.
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self.texBorder)
		glBegin(GL_QUADS)
		glTexCoord2f(0, 0); glVertex2f(-CANVAS_CARD_W, -CANVAS_CARD_H)
		glTexCoord2f(0, 1); glVertex2f(-CANVAS_CARD_W, CANVAS_CARD_H)
		glTexCoord2f(0.72, 1); glVertex2f(CANVAS_CARD_W, CANVAS_CARD_H)
		glTexCoord2f(0.72, 0); glVertex2f(CANVAS_CARD_W, -CANVAS_CARD_H)
		glEnd()
		
		if card is not None:
			# Make sure we have the card image.
			if not self.texCard.has_key(card.id):
				for k,loc in card.images.iteritems():
					try:
						if loc.startswith('images/cards/'):
							loc = settings.dir_imagepacks + loc[13:]
						self.texCard[card.id] = self.LoadTexture(loc)
						break
					except IOError:
						pass
				else:  # If none of them work, try to go for a generic texture.
					try:
						self.texCard[card.id] = self.LoadGeneric(card.type)
					except IOError:
						self.texCard[card.id] = None  # Give up.
			
			if self.texCard[card.id]:
				glColor4f(1.0, 1.0, 1.0, 1.0)
				glBindTexture(GL_TEXTURE_2D, self.texCard[card.id])
				glBegin(GL_QUADS)
				glTexCoord2f(0.052, 0.037); glVertex2f(-(CANVAS_CARD_W-1), -(CANVAS_CARD_H-1))
				glTexCoord2f(0.052, 0.963); glVertex2f(-(CANVAS_CARD_W-1), (CANVAS_CARD_H-1))
				glTexCoord2f(0.948, 0.963); glVertex2f((CANVAS_CARD_W-1), (CANVAS_CARD_H-1))
				glTexCoord2f(0.948, 0.037); glVertex2f((CANVAS_CARD_W-1), -(CANVAS_CARD_H-1))
				glEnd()
		
		glPopMatrix()
	
	def DrawFacedownCard(self, card):
		"""Draw a face-down card."""
		glPushMatrix()
		
		glColor4f(0.0, 0.0, 0.0, 1.0)
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self.texBorder)
		glBegin(GL_QUADS)
		glTexCoord2f(0, 0); glVertex2f(-CANVAS_CARD_W, -CANVAS_CARD_H)
		glTexCoord2f(0, 1); glVertex2f(-CANVAS_CARD_W, CANVAS_CARD_H)
		glTexCoord2f(0.72, 1); glVertex2f(CANVAS_CARD_W, CANVAS_CARD_H)
		glTexCoord2f(0.72, 0); glVertex2f(CANVAS_CARD_W, -CANVAS_CARD_H)
		glEnd()
		
		if card.IsDynasty():
			glBindTexture(GL_TEXTURE_2D, self.texDynastyBack)
		else:
			glBindTexture(GL_TEXTURE_2D, self.texFateBack)
		
		glColor4f(1.0, 1.0, 1.0, 1.0)
		glBegin(GL_QUADS)
		glTexCoord2f(0, 0); glVertex2f(-(CANVAS_CARD_W-1), -(CANVAS_CARD_H-1))
		glTexCoord2f(0, 1); glVertex2f(-(CANVAS_CARD_W-1), (CANVAS_CARD_H-1))
		glTexCoord2f(1, 1); glVertex2f((CANVAS_CARD_W-1), (CANVAS_CARD_H-1))
		glTexCoord2f(1, 0); glVertex2f((CANVAS_CARD_W-1), -(CANVAS_CARD_H-1))
		glEnd()
		
		glPopMatrix()


	def OnPaint(self, e):
		dc = wx.PaintDC(self)
		self.SetCurrent()
		if not self.init:
			self.InitGL()
			self.init = 1
		self.OnDraw()
		self.SwapBuffers()
	
	def OnEraseBackground(self, e):
		pass
		
	def InitGL(self):
		glDisable(GL_CULL_FACE)
		glDisable(GL_DEPTH_TEST)
		glEnable(GL_TEXTURE_2D)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		(x, y) = self.GetSize()
		if y != 0 and x != 0:
			self.FixSize(x, y)
	
	def OnResize(self, e):
		self.SetCurrent()
		(x, y) = e.GetSize()
		if y != 0 and x != 0:
			self.FixSize(x, y)
	
class CanvasBackground:
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
		img = img.crop((0, 0, next_power_of_two(img.size[0]), next_power_of_two(img.size[1])))
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
	
class PlayfieldCanvas(L5RCanvas):
	def __init__(self, parent, id=wx.ID_ANY, *args, **kwargs):
		L5RCanvas.__init__(self, parent, id, *args, **kwargs)
		self.gameState = None
		self.localPlayer = None
		self.markerPos = None
		self.markerOffset = (0, 0)
		self.attachMarker = None
		
		self.texBorderFrame = self.LoadTexture("images/border2.png")
		self.texAttach = self.LoadTexture("images/border3.png")
		
		wx.EVT_LEFT_DOWN(self, self.OnLeftMouseDown)
		wx.EVT_LEFT_DCLICK(self, self.OnDoubleClick)
		wx.EVT_RIGHT_DOWN(self, self.OnRightMouseDown)
		wx.EVT_MOTION(self, self.OnMotion)
		
		self.SetDropTarget(dragdrop.CardDropTarget(self.OnDragData, self.OnDragOver, self.OnDragLeave))
		
		self.contextCard = None
		self.background = CanvasBackground()
	
	def DrawBackground(self):
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
			glVertex2f(self.pfWidth/2, -self.pfHeight/2)
			glVertex2f(-self.pfWidth/2, -self.pfHeight/2)
			glColor4f(settings.playfield_bg_color2[0]/256.0,
				settings.playfield_bg_color2[1]/256.0,
				settings.playfield_bg_color2[2]/256.0, 1)
			glVertex2f(-self.pfWidth/2, self.pfHeight/2)
			glVertex2f(self.pfWidth/2, self.pfHeight/2)
			glEnd()
		elif settings.playfield_bg_mode == 2:  # Vertical gradient
			glDisable(GL_TEXTURE_2D)
			glBegin(GL_QUADS)
			glColor4f(settings.playfield_bg_color1[0]/256.0,
				settings.playfield_bg_color1[1]/256.0,
				settings.playfield_bg_color1[2]/256.0, 1)
			glVertex2f(-self.pfWidth/2, -self.pfHeight/2)
			glVertex2f(-self.pfWidth/2, self.pfHeight/2)
			glColor4f(settings.playfield_bg_color2[0]/256.0,
				settings.playfield_bg_color2[1]/256.0,
				settings.playfield_bg_color2[2]/256.0, 1)
			glVertex2f(self.pfWidth/2, self.pfHeight/2)
			glVertex2f(self.pfWidth/2, -self.pfHeight/2)
			glEnd()
		
		# Background... maybe.
		if settings.playfield_bg_image_display:
			if self.background.filename != settings.playfield_bg_image:
				self.background.Load(settings.playfield_bg_image)
			
			if self.background:
				glMatrixMode(GL_PROJECTION)
				glLoadIdentity()
				w, h = self.GetSize()
				
				glOrtho(-w/2, w/2, h/2, -h/2, -1, 1)
				
				glEnable(GL_TEXTURE_2D)
				glBindTexture(GL_TEXTURE_2D, self.background.texture)
				
				glBegin(GL_QUADS)
				glTexCoord2f(0, self.background.texcoord[1]); glVertex2f(-self.background.size[0]/2, self.background.size[1]/2)
				glTexCoord2f(self.background.texcoord[0], self.background.texcoord[1]); glVertex2f(self.background.size[0]/2, self.background.size[1]/2)
				glTexCoord2f(self.background.texcoord[0], 0); glVertex2f(self.background.size[0]/2, -self.background.size[1]/2)
				glTexCoord2f(0, 0); glVertex2f(-self.background.size[0]/2, -self.background.size[1]/2)
				glEnd()

				glMatrixMode(GL_PROJECTION)
				glLoadIdentity()
				glOrtho(-self.pfWidth/2, self.pfWidth/2, self.pfHeight/2, -self.pfHeight/2, -1, 1)
				glMatrixMode(GL_MODELVIEW)

	def OnDraw(self):
		glLoadIdentity()
		
		self.DrawBackground()
		
		# Do we have an active state?
		if self.gameState:
			# Loop through all cards in all players' play areas.
			
			for pid,player in self.gameState.players.iteritems():
				for cgid in player.zones[game.ZONE_PLAY].cards:
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
	
	def FixSize(self, x, y):
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		h = 200
		w = h * x/y
		self.pfHeight = h
		self.pfWidth = w
		glOrtho(-w/2, w/2, h/2, -h/2, -1, 1)
		glMatrixMode(GL_MODELVIEW)
		glViewport(0, 0, x, y)
		self.Refresh()
	
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
		(wx, wy) = self.GetSize()
		
		return ((float(x)/wx - 0.5) * self.pfWidth, (float(y)/wy - 0.5) * self.pfHeight)
	
	def FindOwnCardAt(self, px, py):
		"Finds and returns the card pointed to at x/y if owned by the local player, or None."
		if not self.gameState or not self.localPlayer:
			return None
		
		(x, y) = self.CoordScreen2World(px, py)
		for cgid in reversed(self.localPlayer.zones[game.ZONE_PLAY].cards):
			card = self.gameState.FindCard(cgid)
			if (card.tapped and (card.x-CANVAS_CARD_H < x < card.x+CANVAS_CARD_H and \
				card.y-CANVAS_CARD_W < y < card.y+CANVAS_CARD_W)) or \
				(not card.tapped and (card.x-CANVAS_CARD_W < x < card.x+CANVAS_CARD_W and \
				card.y-CANVAS_CARD_H < y < card.y+CANVAS_CARD_H)):
				return card
		return None
		
	def FindCardAt(self, px, py):
		"Finds and returns the card pointed to at x/y, or None."
		if not self.gameState:
			return None
		
		(x, y) = self.CoordScreen2World(px, py)
		for pid,player in reversed(self.gameState.players.items()):
			for cgid in reversed(player.zones[game.ZONE_PLAY].cards):
				card = self.gameState.FindCard(cgid)
				if (card.tapped and (card.x-CANVAS_CARD_H < x < card.x+CANVAS_CARD_H and \
				card.y-CANVAS_CARD_W < y < card.y+CANVAS_CARD_W)) or \
					(not card.tapped and (card.x-CANVAS_CARD_W < x < card.x+CANVAS_CARD_W and \
					card.y-CANVAS_CARD_H < y < card.y+CANVAS_CARD_H)):
					return card
		return None
	
	def OnDoubleClick(self, event):
		(px, py) = event.GetPosition()
		(x, y) = self.CoordScreen2World(px, py)
		card = self.FindOwnCardAt(px, py)
		
		if card:
			wx.PostEvent(self, PlayfieldDoubleClickCardEvent(card=card))
	
	def OnRightMouseDown(self, e):
		if not self.gameState:
			return
		
		# Locate any cards we're pointing at.
		(x, y) = self.CoordScreen2World(*e.GetPosition())
		card = self.FindOwnCardAt(*e.GetPosition())
		
		# Found one?
		if card:
			wx.PostEvent(self, PlayfieldRightClickCardEvent(card=card))
		
	def OnLeftMouseDown(self, e):
		if not self.gameState:
			return
		
		# Locate any cards we're pointing at.
		(x, y) = self.CoordScreen2World(*e.GetPosition())
		card = self.FindOwnCardAt(*e.GetPosition())
		
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
		(x, y) = self.CoordScreen2World(x, y)
		sx, sy = self.SnapCoords((x - dragdata.x, y - dragdata.y))
		
		if self.attachMarker:
			card = self.gameState.FindCard(dragdata.cgid)
			wx.PostEvent(self, PlayfieldCardAttachEvent(card=card, target=self.attachMarker, faceUp=dragdata.faceUp))
		else:
			wx.PostEvent(self, PlayfieldCardDropEvent(x=sx, y=sy, cgid=dragdata.cgid, faceUp=dragdata.faceUp))
		
		self.markerPos = None
		self.markerOffset = (0, 0)
		self.attachMarker = None
		
		self.Refresh()
		
	def OnDragOver(self, x, y):
		"""Handle drag-n-drop 'over' operation."""
		(wx, wy) = self.CoordScreen2World(x, y)
		card = self.FindOwnCardAt(x, y)
		# If something has attachments, attaching THAT to something else is ugly.
		if card and card is not self.contextCard and (not self.contextCard or not self.contextCard.attached_cards):
			if card.attached_to:  # This effectively treats attached cards as whatever they are attached to.
				card = card.attached_to
			self.attachMarker = card
			self.markerPos = None
		else:
			self.attachMarker = None
			self.markerPos = self.SnapCoords((wx - self.markerOffset[0], wy - self.markerOffset[1]))
		self.Refresh()
	
	def OnDragLeave(self):
		self.markerPos = None
		self.markerOffset = (0, 0)
		self.Refresh()
		
	def OnMotion(self, event):
		card = self.FindCardAt(*event.GetPosition())
		if card:
			wx.PostEvent(self, PlayfieldCardHoverEvent(card=card))
	
class CardPreviewCanvas(L5RCanvas):
	def __init__(self, parent, id=wx.ID_ANY, *args, **kwargs):
		L5RCanvas.__init__(self, parent, id, *args, **kwargs)
		self.previewCard = None
		self.previewFacedown = False
		
	def OnDraw(self):
		glClearColor(0.2, 0.2, 0.2, 1.0)
		glClear(GL_COLOR_BUFFER_BIT)
		glLoadIdentity();
		if self.previewCard is not None:
			if self.previewFacedown:
				self.DrawFacedownCard(self.previewCard)
			else:
				self.DrawCard(self.previewCard)
	
	def FixSize(self, x, y):
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		targetAR = 21.0/30.0
		currentAR = float(x)/y
		if currentAR > targetAR:
			glOrtho(-10.5*currentAR/targetAR, 10.5*currentAR/targetAR, 15, -15, -1, 1)
		else:
			glOrtho(-10.5, 10.5, 15*targetAR/currentAR, -15*targetAR/currentAR, -1, 1)
		glMatrixMode(GL_MODELVIEW)
		glViewport(0, 0, x, y)
		self.Refresh()
	
	def SetCard(self, cdid):
		try:
			self.previewCard = database.get()[cdid];
			self.previewFacedown = False
		except KeyError:
			self.previewCard = None
		
		self.Refresh()
	
	def SetFacedown(self, card):
		self.previewCard = card
		self.previewFacedown = True
		self.Refresh()


