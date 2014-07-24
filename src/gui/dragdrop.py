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
"""Drag-and-drop helpers."""
import wx
import cPickle

class _CardDataClass:
	def __init__(self, **kwargs):
		self.top = True
		self.faceUp = True
		
		for key, value in kwargs.iteritems():
			setattr(self, key, value)

class CardDropTarget(wx.PyDropTarget):
	def __init__(self, drop_callback = None, over_callback = None, leave_callback = None):
		wx.PyDropTarget.__init__(self)
		self.drop_callback = drop_callback
		self.over_callback = over_callback
		self.leave_callback = leave_callback
		self.data = wx.CustomDataObject(wx.CustomDataFormat('L5RCard'))
		self.SetDataObject(self.data)
	
	def OnData(self, x, y, default):
		if self.GetData() and self.drop_callback:
			args = cPickle.loads(self.data.GetData())
			ret = self.drop_callback(x, y, _CardDataClass(**args))
			if ret is not None:
				return ret
		return default

	def OnDragOver(self, x, y, default):
		try:
			ret = self.over_callback(x, y)
			if ret is not None:
				return ret
		except TypeError:
			pass
		return default
	
	def OnLeave(self):
		try:
			ret = self.leave_callback()
			if ret is not None:
				return ret
		except TypeError:
			pass

def CardDropData(**kwargs):
	data = wx.CustomDataObject(wx.CustomDataFormat('L5RCard'))
	data.SetData(cPickle.dumps(kwargs))
	return data
