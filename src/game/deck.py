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
import xml.parsers.expat

#Local Imports
from db import database
from lib.enums import Enumeration

OUTPUT_TYPES = Enumeration("OUTPUT_TYPES",['Text','HTML','BBCode'])

class DeckException(Exception):
	pass

class ImportCardsNotFoundError(DeckException):
	def __init__(self, cardErrors, deck):
		self.problemCards = cardErrors
		self.importedDeck = deck
	def __str__(self):
		errorStr = (''.join(['%s\r\n' % line for line in self.problemCards]))
		return "These cards were unable to be imported:\r\n%s" % errorStr

class LoadCardsNotFoundError(DeckException):
	def __init__(self, cardErrors, deck):
		self.problemCards = cardErrors
		self.loadedDeck = deck
	def __str__(self):
		errorStr = (''.join(['%s\r\n' % line for line in self.problemCards]))
		return "These cards were not found in the card database:\r\n%s" % errorStr

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
		cardDB = database.get()
		return sum([count for count, id, inplay in self.cards if((inplay!=True) and  (cardDB[id].isDynasty()))])

	def NumFate(self):
		"""Return the number of fate cards in the deck."""
		cardDB = database.get()
		return sum([count for count, id, inplay in self.cards if((inplay!=True) and  (cardDB[id].isFate()))])

	def NumInPlay(self):
		cardDB = database.get()
		return sum([count for count,id, inplay in self.cards if inplay == True])

	def numCardsInDeckFileSubSection(section):
		start = section.find('(')
		end = section.find(')')
		return int(section[start+1:end-1])

	@classmethod
	def load(cls, fp):
		"""Read a deck from a list of strings (or a file-like object) and parse it.

		Returns a deck object.

		"""
		foundInPlay = True

		cardErrors=[]

		cardDB = database.get()
		deck = Deck()
		for c in fp:
			if '# Dynasty' in c:
				foundInPlay = False

			if not c.startswith('#') and c.strip() != '':
				(count, cardname) = c.strip().split(' ', 1)
				cardname = cardname.strip()
				if foundInPlay:
					print '%s starts in play.' % (cardname)

				try:
					deck.cards.append((int(count), cardDB.FindCardByName(cardname).id, foundInPlay))
				except (ValueError, KeyError):
					cardErrors.append(cardname)

		if len(cardErrors) >0:
			raise LoadCardsNotFoundError(cardErrors, deck)

		return deck

	@classmethod
	def newload(cls, fp):
		"""Read a deck from a list of strings (or a file-like object) and parse it.

		Returns a deck object.

		"""
		foundInPlay = True

		cardErrors=[]

		cardDB = database.get()
		deck = Deck()
		line = fp.next()
		#Look for Pre-Game cards first
		if '# Pre-Game' in line:	
			numPreGame = deck.numCardsInDeckFileSubSection(line)

		#Look for a combination of Stronghold,Sensei,Winds to match numPreGame
		i = 0
		while i < numPreGame:
			if '# Stronghold' in line:
				numStronghold = deck.numCardsInDeckFileSubSection(line)
				if numStronghold != 1:
					print "More than one stronghold not allowed, only taking the first one."
				line = fp.next()
				i += 1
				#Add Stronghold to Deck
				(count, cardname) = line.strip().split(' ', 1)
				cardname = cardname.strip()
				print '%s starts in play.' % (cardname)

				try:
					deck.cards.append((int(count), cardDB.FindCardByName(cardname).id, foundInPlay))
				except (ValueError, KeyError):
					cardErrors.append(cardname)

				if numStronghold != 1:
					for x in range(numStronghold-1):
						i += 1
						fp.next()

			if '# Sensei' in line:		
				numSensei = deck.numCardsInDeckFileSubSection(line)
				if numSensei != 1:
					print "More than one sensei not allowed, only taking the first one."
				line = fp.next()
				i += 1
				#Add Sensei to Deck
				(count, cardname) = line.strip().split(' ', 1)
				cardname = cardname.strip()
				print '%s starts in play.' % (cardname)

				try:
					deck.cards.append((int(count), cardDB.FindCardByName(cardname).id, foundInPlay))
				except (ValueError, KeyError):
					cardErrors.append(cardname)

				if numSensei != 1:
					for x in range(numSensei-1):
						i += 1
						fp.next()

			if '# Wind' in line:		
				numWind = deck.numCardsInDeckFileSubSection(line)
				if numWind != 1:
					print "More than one wind not allowed, only taking the first one."
				line = fp.next()
				i += 1
				#Add Wind to Deck
				(count, cardname) = line.strip().split(' ', 1)
				cardname = cardname.strip()
				print '%s starts in play.' % (cardname)

				try:
					deck.cards.append((int(count), cardDB.FindCardByName(cardname).id, foundInPlay))
				except (ValueError, KeyError):
					cardErrors.append(cardname)

				if numWind != 1:
					for x in range(numWind-1):
						i += 1
						fp.next()

			#Go to next line before end of loop
			line = fp.next()

		foundInPlay = False

		for line in fp:
			if '# Dynasty' in line:
				numDynasty = deck.numCardsInDeckFileSubSection(line)

			if '# Fate' in line:
				numFate = deck.numCardsInDeckFileSubSection(line)

			if not line.startswith('#') and line.strip() != '':
				(count, cardname) = line.strip().split(' ', 1)
				cardname = cardname.strip()
				if foundInPlay:
					print '%s starts in play.' % (cardname)

				try:
					deck.cards.append((int(count), cardDB.FindCardByName(cardname).id, foundInPlay))
				except (ValueError, KeyError):
					cardErrors.append(cardname)

		if len(cardErrors) >0:
			raise LoadCardsNotFoundError(cardErrors, deck)

		return deck

	@classmethod
	def loadFromClipboard(cls, data):
		#set up a holder for unknown cards
		cardErrors= []
		importLineHeaders = ['stronghold','dynasty','holdings','regions','personalities','events', 'celestials', 'fate','strategies','spells','items','followers','rings']

		cardDB = database.get()
		deck = Deck()

		#Look for a card line, not a header, not a space, and not the EOF (\x00) line.
		for line in data.splitlines():
			if not line.startswith('#') \
			and line.find('\x00') == -1 \
			and line.find(':') == -1 \
			and line.strip() != '' \
			and not line.isspace():
				try:
					#check that the first item is an integer
					cardStr = line.strip().split(' ', 1)
					cardLower = cardStr[0].lower()
					if  cardLower in importLineHeaders:
						continue

					count = cardStr[0].strip('x')
					if count.isdigit():
						cardname =  cardStr[1].strip()
					else:
						count = 1
						cardname = line.strip()
				except (ValueError, IndexError):
						count = 1
						cardname = line.strip()
				try:
					deck.cards.append((int(count), cardDB.FindCardByName(cardname).id))
				except (ValueError,KeyError):
					cardErrors.append(cardname)

		#If there are errors throw an import error.
		if len(cardErrors) > 0:
			raise ImportCardsNotFoundError(cardErrors, deck)

		return deck

	def Save(self, fp, savetype):
		cardDB = database.get()

		headerString = ''
		headerString = {OUTPUT_TYPES.Text:'\n# %s (%d)\n',
						OUTPUT_TYPES.HTML:'\n<h3><u>%s (%d)</u></h3>\n',
						OUTPUT_TYPES.BBCode:'\n[size=150]%s (%d)[/size]\n'}[savetype]

		#Oracle refers to the Stronghold and Sensei as Pre-Game cards
		#Pre-Game Cards
		inPlayCards =[(count, cardDB[cdid]) for count, cdid, inPlay in self if inPlay==True]
		inPlayCount = 0
		for item in inPlayCards:
			inPlayCount += int(item[0])

		fp.write(headerString % ('Pre-Game',inPlayCount))	

		stronghold = [(count, cardDB[cdid]) for count, cdid, inPlay in self if((inPlay==True) and cardDB[cdid].type=="stronghold")]
		self.WriteCardsToTypeList(fp,stronghold,'Stronghold', savetype)

		sensei = [(count, cardDB[cdid]) for count, cdid, inPlay in self if((inPlay==True) and cardDB[cdid].isSensei())]
		self.WriteCardsToTypeList(fp,sensei,'Sensei', savetype)

		wind = [(count, cardDB[cdid]) for count, cdid, inPlay in self if((inPlay==True) and   cardDB[cdid].isWind())]
		self.WriteCardsToTypeList(fp,wind,'Wind', savetype)

		#Dynasty Deck
		dyncards = [(count, cardDB[cdid]) for count, cdid, inPlay in self if((inPlay!=True) and  (cardDB[cdid].isDynasty()))]
		dynCount = 0
		for item in dyncards:
			dynCount += int(item[0])

		fp.write(headerString % ('Dynasty',dynCount))

		celestialcards = [(count, cardDB[cdid]) for count, cdid, inPlay in self if((inPlay!=True) and   cardDB[cdid].isCelestial())]
		self.WriteCardsToTypeList(fp,celestialcards,'Celestials', savetype)

		eventcards = [(count, cardDB[cdid]) for count, cdid, inPlay in self if((inPlay!=True) and   cardDB[cdid].isEvent())]
		self.WriteCardsToTypeList(fp,eventcards,'Events', savetype)

		holdingcards = [(count, cardDB[cdid]) for count, cdid, inPlay in self if((inPlay!=True) and   cardDB[cdid].isHolding())]
		self.WriteCardsToTypeList(fp,holdingcards,'Holdings', savetype)

		personalitycards = [(count, cardDB[cdid]) for count, cdid, inPlay in self if((inPlay!=True) and cardDB[cdid].isPersonality())]
		self.WriteCardsToTypeList(fp,personalitycards,'Personalities', savetype)

		regioncards = [(count, cardDB[cdid]) for count, cdid, inPlay in self if((inPlay!=True) and   cardDB[cdid].isRegion())]
		self.WriteCardsToTypeList(fp,regioncards,'Regions', savetype)

		#Fate Deck
		fatecards = [(count, cardDB[cdid]) for count, cdid, inPlay in self if ((inPlay!=True) and  (cardDB[cdid].isFate()))]
		fateCount = 0
		for item in fatecards:
			fateCount += int(item[0])

		#fatecards.sort(lambda a, b: cmp(a[1].type, b[1].type))
		fp.write(headerString % ('Fate',fateCount))

		ancestorcards = [(count, cardDB[cdid]) for count, cdid, inPlay in self if((inPlay!=True) and cardDB[cdid].isAncestor())]
		self.WriteCardsToTypeList(fp,ancestorcards,'Ancestors', savetype)

		followercards = [(count, cardDB[cdid]) for count, cdid, inPlay in self if((inPlay!=True) and cardDB[cdid].isFollower())]
		self.WriteCardsToTypeList(fp,followercards,'Followers', savetype)

		itemcards = [(count, cardDB[cdid]) for count, cdid, inPlay in self if((inPlay!=True) and cardDB[cdid].isItem())]
		self.WriteCardsToTypeList(fp,itemcards,'Items', savetype)

		ringcards = [(count, cardDB[cdid]) for count, cdid, inPlay in self if((inPlay!=True) and cardDB[cdid].isRing())]
		self.WriteCardsToTypeList(fp,ringcards,'Rings', savetype)

		spellcards = [(count, cardDB[cdid]) for count, cdid, inPlay in self if((inPlay!=True) and cardDB[cdid].isSpell())]
		self.WriteCardsToTypeList(fp,spellcards,'Spells', savetype)

		strategycards = [(count, cardDB[cdid]) for count, cdid, inPlay in self if((inPlay!=True) and cardDB[cdid].isStrategy())]
		self.WriteCardsToTypeList(fp,strategycards,'Strategy', savetype)

		senseicards = [(count, cardDB[cdid]) for count, cdid, inPlay in self if((inPlay!=True) and cardDB[cdid].isSensei())]
		self.WriteCardsToTypeList(fp,senseicards,'Senseis', savetype)


	def WriteCardsToTypeList(self, fp, cardlist, title, saveType):
		"""Writes all the cards to a typed list, for display and saving"""
		#Added 11/24/08 PCW
		headerString = ''
		cardString = ''

		if len(cardlist) > 0:
			cardCount = 0
			for item in cardlist:
				cardCount += int(item[0])

			headerString = {OUTPUT_TYPES.Text:'\n# %s (%d)\n',
							OUTPUT_TYPES.HTML:'\n<br/><b><u>%s (%d)</u></b><br/>\n',
							OUTPUT_TYPES.BBCode:'\n[b][u]%s (%d)[/u][/b]\n'}[saveType]

			cardlist.sort(lambda a, b: cmp(a[1].type, b[1].type))
			cardString = {OUTPUT_TYPES.Text:'%d %s\n',
						  OUTPUT_TYPES.HTML:'%d %s<br/>\n',
						  OUTPUT_TYPES.BBCode:'%d %s\n'}[saveType]

			fp.write(headerString % (title,cardCount))
			for count, card in cardlist:
				fp.write(cardString % (count, card.name))

	def Add(self, cdid, num = 1, inplay=False):
		"""Add a number of a particular card to the deck.

		Returns the number of that card now in the deck.

		"""
		for idx, val in enumerate(self.cards):
			if val[1] == cdid:
				self.cards[idx] = (val[0] + num, cdid, inplay)
				return val[0] + num
		self.cards.append((num, cdid, inplay))
		return num

	def Remove(self, cdid, num = 1):
		"""Remove a number of a particular card from the deck.

		Returns the number of that card now in the deck.

		"""
		for idx, val in enumerate(self.cards):
			if val[1] == cdid:
				if val[0] > num:
					inplay = self.cards[idx][2]
					self.cards[idx] = (val[0] - num, cdid, inplay)
					return val[0] - num
				else:
					del self.cards[idx]
					return 0
		return 0


class GempukkuDeckConverter():
	def __init__(self, filename):
		self.filename = filename

	def convert(self):
		"""Import the source file and convert it to a Eopk Deck File."""

		self.parser = xml.parsers.expat.ParserCreate()
		self.parser.StartElementHandler = self.parseStartElem
		self.parser.EndElementHandler = self.parseEndElem
		self.parser.CharacterDataHandler = self.parseCData

		self.count = 0
		self.cdata = ""
		self.cardId = None
		self.deck = Deck()
		self.cardDB = database.get()
		self.cards = {}

		try:
			self.parser.ParseFile(file(self.filename, 'rb'))

			for k,v in self.cards.iteritems():
				self.deck.cards.append((v, self.cardDB.FindCardByID(k).id))
		except (ValueError,KeyError):
			raise DeckException()

		return self.deck;

	def parseStartElem(self, name, attrs):
		if name== "card":
			self.cdata = ""

	def parseEndElem(self, name):
		if name == "card":
			self.cards[self.cardId] = self.count
			self.cardId = None
			self.count = 0

		elif name == "cardId":
			self.cardId = self.cdata
		elif name == "count":
			self.count = (int(self.cdata))

		self.cdata = ''

	def parseCData(self, data):
		self.cdata = data

class TheGameDeckConverter():
	def __init__(self, filename):
		self.filename = filename
		self.cards = {}

	def convert(self):
		self.cardDB = database.get()
		self.deck = Deck()
		try:
			filestring = (file(self.filename, 'rb')).read()
			cardarray = filestring.rstrip('|').split('|')
			for cardId in cardarray:
				if cardId in self.cards:
					self.cards[cardId] += 1
				else:
					self.cards[cardId]=1

			for k,v in self.cards.iteritems():
				self.deck.cards.append((v, self.cardDB.FindCardByID(k).id))
		except (ValueError,KeyError):
			raise DeckException()
		except IOError:
			wx.MessageDialog(self, 'The specified deck file could not be opened.\nMake sure the path ' \
				'entered exists.', 'Deck Error', wx.ICON_ERROR).ShowModal()
			return
		return self.deck

