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
"""
	Proxy Import module for Egg of P'an Ku.

author: Ryan Karetas
file: proxyimport.py
date: 14 Aug 2014
"""

import xml.parsers.expat
import os

#Use for testing
if __name__ == "__main__":
	import os
	parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	os.sys.path.insert(0,parentdir)

#Local Imports
from db import proxydb

cardAttrs = ("name", "force", "chi", "text", "cost", \
	"personal_honor", "honor_req")

class ProxyXMLImporter:
	def __init__(self, filename):
		self.filename = filename
		self.proxdb = proxydb.ProxyDB()

	def convert(self, outfile=None):
		"""Import the source file and convert it to a suitable
		database format, saving it to outfile."""

		self.parser = xml.parsers.expat.ParserCreate()
		self.parser.StartElementHandler = self.parseStartElem
		self.parser.EndElementHandler = self.parseEndElem
		self.parser.CharacterDataHandler = self.parseCData

		self.cdata = ""
		self.cCard = None
		self.cards = {}
		self.date = None

		self.parser.ParseFile(file(self.filename, 'rb'))

		#Add to database
		for card in self.cards:
			self.proxdb.add_card(self.cards[card])
			#real_card = self.cards[card]
			#print real_card, real_card.type, real_card.clans, real_card.set

	def parseStartElem(self, name, attrs):
		if name == "cards":
			self.date = attrs["version"]
		elif name == "card":
			self.cCard = proxydb.Card()
			self.cCard.id = attrs["id"]
			type = self.proxdb.get_card_type_by_name(attrs["type"].capitalize())
			self.cCard.type = type.id
		self.cdata = ""

	def parseEndElem(self, name):
		if name == "clan":
			clan_name = self.cdata
			clan = self.proxdb.get_clan_by_name(clan_name.capitalize())
			self.cCard.clans.append(clan)
		elif name == "edition":
			set_name = self.cdata
			set = self.proxdb.get_set_by_abbv(set_name)
			self.cCard.set = set.id
		elif name == "image":
			self.cCard.image = self.cdata
		elif name == "rarity":
			self.cCard.rarity = self.cdata.encode("latin-1")
		elif name == "artist":
			self.cCard.artist =  self.cdata.encode("latin-1")
		elif name in cardAttrs:
			setattr(self.cCard, name, self.cdata.encode("latin-1"))
		elif name == "card":
			self.cards[self.cCard.id] = self.cCard

	def parseCData(self, data):
		self.cdata += data

#Use for testing
if __name__ == "__main__":
	importer = ProxyXMLImporter("C:\Users\Gryffon\eopk\proxy-ivory.xml")
	importer.convert()