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
"""Database import interface for Egg of P'an Ku."""
import wx
import os.path

#Local Imports
import database

from settings.xmlsettings import settings
from settings.xmlsettings import locationsettings


def EnsureExists():
	"""Ensure that the database is loaded by prompting the user to load
	it if it is not."""
	should_import = False
	if not os.path.isfile(os.path.join(locationsettings.data_dir, database.LOCALDATABASE)):
		if not os.path.isfile(settings.cardsource):
			dlg = wx.MessageDialog(None, \
				'You do not appear to have a card database configured right now.\n' \
				'Egg of P\'an Ku requires one to function. Would you like to import a suitable\n' \
				'database from disk now?\n\n' \
				'If this is your first time running Egg of P\'an Ku, please consult the manual\n' \
				'for information on how to find a database online.', 'Import card database',
				wx.ICON_QUESTION|wx.YES_NO)
			if dlg.ShowModal() == wx.ID_YES:
				fdlg = wx.FileDialog(None, wildcard='XML card database (*.xml)|*.xml|All files (*.*)|*.*', style=wx.OPEN|wx.FILE_MUST_EXIST)
				if fdlg.ShowModal() == wx.ID_OK:
					settings.cardsource = fdlg.GetPath()
					settings.WriteSettingsFile()
					should_import = True
				else:
					return False
			else:
				return False
		else:
			wx.MessageDialog(None, \
				'You have an existing database import specified, but the local\n' \
				'database does not exist. Egg of P\'an Ku will re-import it now.\n' \
				'This may take a few moments.', 'Import card database',
				wx.ICON_INFORMATION).ShowModal()
			should_import = True
	else:
		try:
			if os.stat(os.path.join(locationsettings.data_dir, database.LOCALDATABASE)).st_mtime < os.stat(settings.cardsource).st_mtime:
				wx.MessageDialog(None, \
					'You have an existing database import specified, and it seems to\n' \
					'be newer than the locally cached database. Egg of P\'an Ku will re-import it now.\n' \
					'This may take a few moments.', 'Import card database',
					wx.ICON_INFORMATION).ShowModal()
				should_import = True
		except:
			pass
	
	if should_import:
		try:
			importer = database.XMLImporter(settings.cardsource)
			importer.convert()
						
		except Exception, e:
			wx.MessageDialog(None, 'There was a problem importing the card database.\n' \
				'Consult the manual for possible ways to address this.\n\n%s: %s\n\n' \
				'Egg of P\'an Ku will abort.' % (e.__class__.__name__, str(e)), 'Card database import error',
				wx.ICON_ERROR).ShowModal()
			return False
	
	try:
		database.get()
	except Exception, e:
		wx.MessageDialog(None, 'There was a problem loading the card database.\n' \
			'Consult the manual for possible ways to address this.\n\n%s: %s\n\n' \
			'Egg of P\'an Ku will abort.' % (e.__class__.__name__, str(e)), 'Card database error',
			wx.ICON_ERROR).ShowModal()
		return False
	
	return True
