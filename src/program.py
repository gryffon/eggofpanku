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
"""Main module."""

import cPickle
import sys
import os
import socket
import wx
import logging

#Local Imports
import eopk
from db import dbimport
from gui.guids import *


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
			frame = eopk.MainWindow(None, ID_MAIN_WINDOW, EOPK_APPNAME)
			app.MainLoop()
	finally:
		if not eopk.MainWindow.LogFile is None:
			eopk.MainWindow.LogFile.close()
			eopk.MainWindow.LogFile = None
		del app
