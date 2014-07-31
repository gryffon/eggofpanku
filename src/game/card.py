# Egg of P'an Ku -- an unofficial client for Legend of the Five Rings
# Copyright (C) 2008  Peter C O Johansson, Paige Watson
# Copyright (C) 2009,2010  Paige Watson
# Copyright (C) 2014  Ryan Karetas
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
	Card abstraction module for Egg of P'an Ku.

author: Ryan Karetas
file: card.py
date: 24 Jul 2014
"""

class Card():
	#Card Data
	id = 0
	type = 0
	name = ""
	rarity = ""
	edition = ""
	editionimage = ""
	legal = []
	keywords = []
	text = ""
	flavor = ""
	artist = ""
	#Personalities, Strongholds, Ancestor
	clan = []
	#Personalities, Followers, Items, Ancestor
	force = ""
	chi = ""
	#Personalities, Followers, Ancestor
	honor_req = ""
	cost = 0
	personal_honor = 0
	#Fate Cards
	focus = 0
	#Strongholds, Sensei
	starting_honor = 0
	province_strength = 0
	gold_production = 0

	def __init__(self):
		print "Card"



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

#Use for testing
if __name__ == "__main__":
	card = Card()