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
"""Deck module for Egg of P'an Ku."""
import database


class DeckException(Exception):
	pass
	
class InvalidCardError(DeckException):
	def __init__(self, card):
		self.card = card
	def __str__(self):
		return "Card '%s' not found in database." % self.card


class Deck:
	def __init__(self):
		self.cards = []
		self.modified = False
	
	def __iter__(self):
		return self.cards.__iter__()
	
	def __len__(self):
		return len(self.cards)
	
	def NumDynasty(self):
		"""Return the number of dynasty cards in the deck."""
		db = database.get()
		return sum([count for count, id in self.cards if db[id].isDynasty()])
	
	def NumFate(self):
		"""Return the number of fate cards in the deck."""
		db = database.get()
		return sum([count for count, id in self.cards if db[id].isFate()])
	
	@classmethod
	def load(cls, fp):
		"""Read a deck from a list of strings (or a file-like object) and parse it.
		
		Returns a deck object.
		
		"""
		db = database.get()
		deck = Deck()
		for c in fp:
			if not c.startswith('#') and c.strip() != '':
				(count, cardname) = c.strip().split(' ', 1)
				cardname = cardname.strip()
				try:
					deck.cards.append((int(count), db.FindCardByName(cardname).id))
				except KeyError:
					raise InvalidCardError(cardname)
		return deck

	def Save(self, fp):
		db = database.get()
		
		for count, cdid in self:
			card = db[cdid]
			if card.type == 'strongholds':
				fp.write('%d %s\n' % (count, card.name))
		
		fp.write('\n# Fate\n')
		fatecards = [(count, db[cdid]) for count, cdid in self if db[cdid].isFate()]
		fatecards.sort(lambda a, b: cmp(a[1].type, b[1].type))
		for count, card in fatecards:
			fp.write('%d %s\n' % (count, card.name))
				
		fp.write('\n# Dynasty\n')
		dyncards = [(count, db[cdid]) for count, cdid in self if db[cdid].isDynasty()]
		dyncards.sort(lambda a, b: cmp(a[1].type, b[1].type))
		for count, card in dyncards:
			fp.write('%d %s\n' % (count, card.name))
		
	def Add(self, cdid, num = 1):
		"""Add a number of a particular card to the deck.
		
		Returns the number of that card now in the deck.
		
		"""
		for idx, val in enumerate(self.cards):
			if val[1] == cdid:
				self.cards[idx] = (val[0] + num, cdid)
				return val[0] + num
		self.cards.append((num, cdid))
		return num

	def Remove(self, cdid, num = 1):
		"""Remove a number of a particular card from the deck.
		
		Returns the number of that card now in the deck.
		
		"""
		for idx, val in enumerate(self.cards):
			if val[1] == cdid:
				if val[0] > num:
					self.cards[idx] = (val[0] - num, cdid)
					return val[0] - num
				else:
					del self.cards[idx]
					return 0
		return 0
