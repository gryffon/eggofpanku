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

from dumbdbm import _Database
import xml.parsers.expat
import os
import cPickle
import base64
from collections import OrderedDict

#Local Imports
import dbimport
#from lib import odict


from settings.xmlsettings import settings
from settings import xmlfilters

cardAttrs = ("name", "force", "chi", "text", "cost", "focus", \
	"personal_honor", "honor_req", "starting_honor", \
	"province_strength", "gold_production")

_database = None

cardTypes = []
factions = []
minorClans = []
legalityFormats = []
rarityFormats = {}
#cardSets = odict.OrderedDict()
cardSets = OrderedDict()

filterList = xmlfilters.FilterReader().Filters

for filterItem in filterList["cardtype"]:
	cardTypes.append(filterItem.displayName)

for filterItem in filterList["faction"]:
	factions.append(filterItem.displayName)

for filterItem in filterList["minorClan"]:
	minorClans.append(filterItem.displayName)

#sort the factions
minorClans.sort()
factions.sort()
#add the minors to the list
factions.extend(minorClans)

for filterItem in filterList["rarity"]:
	rarityFormats[filterItem.displayName]=filterItem.name


for filterItem in filterList["legality"]:
	legalityFormats.append(filterItem.displayName)

for filterItem in filterList["set"]:
	cardSets.insert(0, filterItem.displayName, filterItem.name)

LOCALDATABASE = 'cards.db'
FILENAME = os.path.basename(settings.cardsource)

class CardData:
	def __init__(self):
		self.type = "none"
		self.name = "none"
		self.rarity = ""
		self.flavor = ""
		self.artist = ""
		self.legal = []
		self.clans = []
		self.rulings = []
		self.images = {}
		self.isencrypted = False
		self.inplay= False

		for x in cardAttrs:
		  setattr(self, x, '')

	def DecryptAttribute(self, x):
		outputstring = ''
		print 'Decrypting attribute: %s' % x
		input = base64.decodestring(getattr(self,x))
		longkey = FILENAME.rpartition('-')[2]
		key = longkey[:longkey.find('.')]
		keylength = len(key)
		for i in range(0,len(input)):
			curchar = input[i]
			keychar = key[(i % keylength)-1] #((i % keylength) - 1)
			decodedchar = chr(ord(curchar)-ord(keychar))
			outputstring += decodedchar

		return outputstring

	def startsInPlay(self):
		return (self.inplay==True)

	def isLegal(self, ed):
		return ed in self.legal

	def isClan(self, cl):
		return cl in self.clans

	def isDynasty(self):
		return self.type in ['holding', 'personality', 'region', \
			'event', 'wind', 'celestial']
	def isHolding(self):
		return self.type == 'holding'

	def isPersonality(self):
		return self.type == 'personality'

	def isRegion(self):
		return self.type == 'region'

	def isEvent(self):
		return self.type == 'event'

	def isWind(self):
		return self.type == 'wind'

	def isCelestial(self):
		return self.type == 'celestial'

	#Don't consider sensei a Fate card for the time being.
	def isFate(self):
		return self.type in ['strategy', 'follower', 'item', \
			'spell', 'ancestor', 'ring']

	def isStrategy(self):
		return self.type == 'strategy'

	def isFollower(self):
		return self.type == 'follower'

	def isItem(self):
		return self.type == 'item'

	def isAncestor(self):
		return self.type == 'ancestor'

	def isRing(self):
		return self.type == 'ring'

	def isSpell(self):
		return self.type == 'spell'

	def isSensei(self):
		return self.type == 'sensei'

	def IsEncrypted(self):
		return self.isencrypted == True

	def hasGoldCost(self):
		#return self.cost != ''
		return self.type in ['strategy', 'follower', 'item', \
			'holding', 'personality', 'spell']

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
			outfile = file(os.path.join(settings.data_dir, LOCALDATABASE), mode='wb')
		cPickle.dump((self.filename, self.date, self.cards), outfile, cPickle.HIGHEST_PROTOCOL)

	def parseStartElem(self, name, attrs):
		if name == "cards":
			self.date = attrs["version"]
		elif name == "card":
			self.cCard = CardData()
			self.cCard.id = attrs["id"]
			#self.cCard.rarity = attrs["rarity"]
			_cardType = attrs["type"]
			if _cardType.find("encrypted-") != -1:
				self.cCard.isencrypted = True
				_typeName = attrs["type"].replace('encrypted-','')
				self.cCard.type = _typeName
				#self.cCard.type = attrs["type"]
			else:
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
		elif name == "rulings":
			self.cCard.rulings.append(self.cdata)
		elif name == "rarity":
			setattr(self.cCard, "rarity", self.cdata.encode("latin-1"))
		elif name == "flavor":
			setattr(self.cCard, "flavor", self.cdata.encode("latin-1"))
		elif name == "artist":
			setattr(self.cCard, "artist", self.cdata.encode("latin-1"))
		elif name in cardAttrs:
			setattr(self.cCard, name, self.cdata.encode("latin-1"))
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

		(self.filename, self.date, self.cards) = cPickle.load(file(os.path.join(settings.data_dir, LOCALDATABASE), mode='rb'))
		if self.filename != settings.cardsource:
			raise NameError, 'Cards.db was created from a different xml file.  Please reload the card database.'

		for x in self.cards.values():
			cardName = x.name
			if x.IsEncrypted():
				cardName = x.DecryptAttribute('name')
				x.name = cardName
				x.text = x.DecryptAttribute('text')
				print 'Decrypted card name: %s' % cardName
			self.cardNames[cardName] = x

	def __getitem__(self, key):
		return self.cards[key]

	def __iter__(self):
		return self.cards.itervalues()

	def __len__(self):
		return len(self.cards)

	def FindCardByName(self, name):
		return self.cardNames[name]

	def FindCardByID(self, cardId):
		return self.cards[cardId]

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

def reset():
	global _database
	os.remove(os.path.join(settings.data_dir, LOCALDATABASE))
	importer = XMLImporter(settings.cardsource)
	importer.convert()
	_database = CardDB()


def get():

	try:
		global _database
		if _database == None:
			_database = CardDB()
		return _database
	except (NameError, AttributeError):
		_database = CardDB()
		return _database

