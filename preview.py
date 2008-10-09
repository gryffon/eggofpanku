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
"""Card preview widget for Egg of P'an Ku."""
import wx
import wx.html
from OpenGL.GL import *

import canvas
import database


# More interesting names for the various card types.
typeNames = {
	'personalities':'Personality',
	'events':'Event',
	'regions':'Region',
	'holdings':'Holding',
	'actions':'Action',
	'items':'Item',
	'followers':'Follower',
	'ancestors':'Ancestor',
	'rings':'Ring',
	'senseis':'Sensei',
	'strongholds':'Stronghold',
	'winds':'Wind',
}

class CardPreviewCanvas(canvas.L5RCanvas):
	def __init__(self, parent, id=wx.ID_ANY, *args, **kwargs):
		canvas.L5RCanvas.__init__(self, parent, id, *args, **kwargs)
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
	
	def SetupSize(self):
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		targetAR = 21.0/30.0
		x, y = self.GetSize()
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



class CardPreviewWindow(wx.SplitterWindow):
	"""L5R card preview window."""
	def __init__(self, *args, **kwargs):
		wx.SplitterWindow.__init__(self, *args, **kwargs)
		
		self.SetMinimumPaneSize(128)
		self.SetSashGravity(0.0)
		
		self.previewCard = None
		
		self.oglCanvas = CardPreviewCanvas(self, style=wx.BORDER_THEME)
		self.notebook = wx.Notebook(self, style=wx.NB_BOTTOM)
		self.cardText = wx.html.HtmlWindow(self.notebook, style=wx.BORDER_THEME)
		self.notebook.AddPage(self.cardText, 'Card Text')
		self.cardRulings = wx.TextCtrl(self.notebook, style=wx.TE_READONLY|wx.TE_MULTILINE)
		self.cardRulings.Show(False)
		
		self.SplitHorizontally(self.oglCanvas, self.notebook, 128)

		self.cardText.SetPage('<html><body bgcolor="#ffffa0"></html>')
		self.cardText.Refresh()

	def SetFacedown(self, card):
		"""Show a facedown card."""
		self.previewCard = None
		self.oglCanvas.SetFacedown(card)
		
		try:  # We might know what card it is (because we played it, for instance)
			reality = '<br>(<b>%s</b>)' % card.data.name
		except AttributeError:
			reality = ''
		
		if card.IsDynasty():
			self.cardText.SetPage('<html><body bgcolor="#ffffa0"><center><font size="-1">Facedown Dynasty Card%s</font></center></body></html>' % reality)
		else:
			self.cardText.SetPage('<html><body bgcolor="#ffffa0"><center><font size="-1">Facedown Fate Card%s</font></center></body></html>' % reality)
	
	def EnableRulings(self, enabled=True):
		if enabled:
			if self.notebook.GetPageCount() == 1:
				self.notebook.AddPage(self.cardRulings, 'Rulings')
			#self.cardRulings.Show(True)
		else:
			self.cardRulings.Show(False)
			if self.notebook.GetPageCount() == 2:
				self.notebook.RemovePage(1)
	
	def SetCard(self, cdid):
		"""Show a faceup card."""
		if self.previewCard == cdid:
			return
		self.previewCard = cdid
		self.oglCanvas.SetCard(cdid)
		try:
			card = database.get()[cdid]
		except KeyError:
			print cdid
			return
		
		# HTML card text
		html = ['<html><body bgcolor="#ffffa0"><center>']
		
		html.append('<font size="+1"><b>%s</b></font>' % card.name) # Everything has a name.
		
		try:
			html.append('<br><font size="-1">%s</font>' % typeNames[card.type])
		except KeyError:
			pass
		
		if card.type in ('personalities', 'followers', 'items'): # Force and chi.
			html.append('<br><font size="-1">Force: <b>%s</b>  Chi: <b>%s</b></font>' % (card.force, card.chi))
		elif card.type == 'holdings' and card.force != '':
			html.append('<br><font size="-1">Gold Production: <b>%s</b></font>' % card.force)
		
		if card.type == 'personalities': # Gold cost, honor req, phonor.
			html.append('<br><font size="-1">HR: <b>%s</b>  GC: <b>%s</b>  PH: <b>%s</b></font>' % (card.honor_req, card.cost, card.personal_honor))
		elif card.type == 'followers': # Gold cost, honor req.
			html.append('<br><font size="-1">HR: <b>%s</b>  GC: <b>%s</b></font>' % (card.honor_req, card.cost))
		elif card.type == 'strongholds': # Production, honor, etc.
			html.append('<br><font size="-1">Province Strength: <b>%s</b><br>Gold Production: <b>%s</b><br>Starting Honor: <b>%s</b></font>' %  \
				(card.province_strength, card.gold_production, card.starting_honor))
		elif card.hasGoldCost(): # Gold cost.
			html.append('<br><font size="-1">Gold Cost: <b>%s</b></font>' % card.cost)
		
		html.append('<hr><font size="-2">%s</font><hr>' % card.text)
		
		if card.isFate():
			html.append('<br><font size="-1">Focus Value: <b>%s</b></font>' % card.focus)
		
		html.append('<br><font size="-2">Legal in <b>%s</b></font>' % ', '.join(card.legal))
		
		if card.id[0] == '_':
			html.append('<br><font size="-2">Created card</font>')
		else:
			html.append('<br><font size="-2">%s</font>' % card.id)
		
		html.append('</center></body></html>')
		
		self.cardText.SetPage('\n'.join(html))
		self.cardText.Refresh()
		
		# Rulings
		try:
			if card.rulings:
				self.EnableRulings()
				txt = '\n'.join('* ' + ruling for ruling in card.rulings)
				self.cardRulings.SetValue(txt)
			else:
				self.EnableRulings(False)
		except AttributeError:
			self.EnableRulings(False)
		
		self.Layout()
		#self.Refresh()

