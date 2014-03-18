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
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from wx.glcanvas import GLCanvas
from PIL import JpegImagePlugin  # If not explictly imported, py2exe will fail
from PIL import PngImagePlugin   # If not explictly imported, py2exe will fail
from PIL import Image
import random
import os

#Local Imports
from game import game
from db import database
import dragdrop

from settings.xmlsettings import settings
from settings.xmlsettings import locationsettings


CANVAS_CARD_W = 10.5
CANVAS_CARD_H = 15.0

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

class L5RCanvas(GLCanvas):
	def __init__(self, parent, id=wx.ID_ANY, *args, **kwargs):
		GLCanvas.__init__(self, parent, id, *args, **kwargs)
		
		wx.EVT_PAINT(self, self.OnPaint)
		wx.EVT_SIZE(self, self.OnResize)
		wx.EVT_ERASE_BACKGROUND(self, self.EraseBackground)
		
		self.init = 0
		self.SetCurrent()
		self.texBorder = self.LoadTexture(os.path.join(locationsettings.data_dir, 'images/border.png'))
		self.texFateBack = self.LoadTexture(os.path.join(locationsettings.data_dir, 'images/fate_back.jpg'))
		self.texDynastyBack = self.LoadTexture(os.path.join(locationsettings.data_dir, 'images/dynasty_back.jpg'))
		self.texCard = {}
		self.texGeneric = {}
	
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
		self.texGeneric[type] = self.LoadTexture(os.path.join(locationsettings.data_dir,'images/cards/generic_%s.jpg') % type)
		return self.texGeneric[type]
		
	def DrawMarker(self, tex):
		"""Draw a transparent 'marker' for cards."""
		#print 'DrawMarker text = %s' % (tex)
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
							if settings.imagepackdir_changed == True:
								loc = locationsettings.dir_imagepacks + loc[13:]
							else:
								loc = locationsettings.data_dir + '/' + settings.dir_imagepacks + loc[13:]
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
			self.SetupSize()
			self.Refresh()
	
	def OnResize(self, e):
		self.SetCurrent()
		(x, y) = e.GetSize()
		if y != 0 and x != 0:
			self.SetupSize()
			self.Refresh()
	
