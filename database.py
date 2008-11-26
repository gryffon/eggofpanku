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
"""Card database module for Egg of P'an Ku."""

import xml.parsers.expat
import os
import cPickle
import odict

cardAttrs = ("name", "force", "chi", "text", "cost", "focus", \
	"personal_honor", "honor_req", "starting_honor", \
	"province_strength", "gold_production")
cardTypes = ['Strongholds', 'Regions', 'Holdings', 'Events', \
	'Personalities', 'Actions', 'Items', 'Followers', 'Spells', 'Rings', \
	'Ancestors', 'Senseis', 'Winds']
factions = ['Phoenix', 'Dragon', 'Mantis', 'Crab', 'Spider', 'Scorpion', \
	'Lion', 'Unicorn', 'Crane','Shadowlands']
minorClans = ['Ratling', 'Naga', 'Monk', \
	'Ninja', 'Hare', 'Toturi\'s Army', 'Monkey', 'Spirit']
#sort the factions
minorClans.sort()
factions.sort()
#add the minors to the list
factions.extend(minorClans)

legalityFormats = ('Samurai', 'Lotus', 'Diamond', 'Gold', 'Jade', 'Open') #'Celestial', 

cardSets = odict.OrderedDict([line.strip().split(':') for line in file('sets.dat', 'rb')])

LOCALDATABASE = 'cards.db'



class CardData:
	def __init__(self):
		self.type = "none"
		self.legal = []
		self.clans = []
		self.rulings = []
		self.images = {}
		for x in cardAttrs:
			setattr(self, x, '')
	
	def isLegal(self, ed):
		return ed in self.legal
	
	def isClan(self, cl):
		return cl in self.clans
	
	def isDynasty(self):
		return self.type in ['holdings', 'personalities', 'regions', \
			'events', 'winds']
	def isHolding(self):
		return self.type == 'holdings'

	def isPersonality(self):
		return self.type == 'personalities'

	def isRegion(self):
		return self.type == 'regions'

	def isEvent(self):
		return self.type == 'events'

	def isWind(self):
		return self.type == 'winds'

	def isFate(self):
		return self.type in ['actions', 'followers', 'items', \
			'spells', 'ancestors', 'rings', 'senseis']

	def isAction(self):
		return self.type == 'actions'

	def isFollower(self):
		return self.type == 'followers'

	def isItem(self):
		return self.type == 'items'

	def isAncestor(self):
		return self.type == 'ancestors'

	def isRing(self):
		return self.type == 'rings'

	def isSpell(self):
		return self.type == 'spells'

	def isSensei(self):
		return self.type == 'senseis'
	
	def hasGoldCost(self):
		return self.type in ['actions', 'followers', 'items', \
			'holdings', 'personalities', 'spells']

class XMLImporter:
	def __init__(self, filename):
		self.filename = filename

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
		
		# Finally, dump it.
		if outfile is None:
			outfile = file(LOCALDATABASE, mode='wb')
		cPickle.dump((self.date, self.cards), outfile, cPickle.HIGHEST_PROTOCOL)

	def parseStartElem(self, name, attrs):
		if name == "cards":
			self.date = attrs["version"]
		elif name == "card":
			self.cCard = CardData()
			self.cCard.id = attrs["id"]
			self.cCard.type = attrs["type"]
		elif name == "image":
			self.imageEdition = attrs["edition"]
		self.cdata = ""
		
	def parseEndElem(self, name):
		if name == "legal":
			self.cCard.legal.append(self.cdata)
		elif name == "clan":
			self.cCard.clans.append(self.cdata)
		elif name == "image":
			self.cCard.images[self.imageEdition] = self.cdata
		elif name in cardAttrs:
			setattr(self.cCard, name, self.cdata.encode("latin-1"))
		elif name == "rulings":
			self.cCard.rulings.append(self.cdata)
		elif name == "card":
			self.cards[self.cCard.id] = self.cCard
		
	def parseCData(self, data):
		self.cdata += data


#-----------------------------------------------------------------------------
class CardDB:
	def __init__(self):
		self.cards = {}
		self.cardNames = {}
		self.createIndex = 1  # Next available index for created cards
		
		(self.date, self.cards) = cPickle.load(file(LOCALDATABASE, mode='rb'))
		for x in self.cards.values():
			self.cardNames[x.name] = x

	def __getitem__(self, key):
		return self.cards[key]
	
	def __iter__(self):
		return self.cards.itervalues()
	
	def __len__(self):
		return len(self.cards)
	
	def FindCardByName(self, name):
		return self.cardNames[name]
	
	def CreateCard(self, name, id=None, **kwargs):
		"""Create a temporary card."""
		if id is None:
			id = '_%d' % self.createIndex
			self.createIndex += 1
		
		if id in self.cards:  # Already exists; update it. Note that we can't just replace it, as other things may have references to the card.
			for k, v in kwargs.iteritems():
				setattr(self.cards[id], k, v)
		else:
			card = CardData()
			card.name = name
			card.id = id
			for k, v in kwargs.iteritems():
				setattr(card, k, v)
			self.cards[card.id] = card
		
		return id


def get():
	global _database
	try:
		return _database
	except NameError:
		_database = CardDB()
		return _database

