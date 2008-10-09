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
"""Settings module for Egg of P'an Ku."""


DEFAULT_SETTINGS = {
	'gamehost':'localhost',
	'gameport':18072,
	'last_deck':'',
	'maximize':True,
	'mainwindow_size':(780,560),
	'playername':'Toku-san',
	'cardsource':'',
	'playfield_snap':True,
	'dir_imagepacks':'images/cards/',
	'playfield_bg_mode':0,
	'playfield_bg_color1':(0, 206, 24),
	'playfield_bg_color2':(0, 190, 16),
	'playfield_bg_image':'',
	'playfield_bg_image_display':False,
	'attach_ok': ('personalities',),
	'matchuser':'',
	'matchpassword':'1234',
}


class _Settings:
	def __init__(self, setfile):
		self.__dict__['_filename'] = setfile
		self.__dict__.update(DEFAULT_SETTINGS)
		
		try:
			for line in file(setfile, 'r'):
				line = line.strip()
				if len(line) > 0:
					k, v = line.split('=', 1)
					self.__dict__[k] = eval(v)
		except IOError:
			pass

	def __setattr__(self, key, value):
		self.__dict__[key] = value
		
		# Dump settings file to disk.
		f = file(self._filename, 'w')
		for k, v in self.__dict__.iteritems():
			if not k.startswith('_'):
				f.write(''.join((k, '=', repr(v), '\n')))
		f.close()


settings = _Settings('eopk-settings')
