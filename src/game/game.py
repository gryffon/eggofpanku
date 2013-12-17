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
"""Game state module for Egg of P'an Ku."""

#Local Imports
import database

ZONE_DUMMY = 0            # Dummy zone
ZONE_DECK_DYNASTY = 1     # Dynasty deck
ZONE_DECK_FATE = 2        # Fate deck
ZONE_DISCARD_DYNASTY = 3  # Dynasty discard pile
ZONE_DISCARD_FATE = 4     # Fate discard pile
ZONE_HAND = 5             # Fate hand
ZONE_REMOVED = 6          # Removed-from-play zone
ZONE_PLAY = 7             # In play
ZONE_FOCUS_POOL = 8       # Focus pool
NUM_ZONES = 9

TOKEN_DEFAULT_IMAGE = 'images/tokens/token_generic.png'
MARKER_DEFAULT_IMAGE = 'generic'
MARKER_IMAGE_PREFIX = 'images/markers/marker_'
MARKER_IMAGE_EXTENSION = '.png'
	
zoneNames = ['limbo', 'dynasty deck', 'fate deck', 'dynasty discard pile', 'fate discard pile', 'hand', 'removed-from-game pile', 'play', 'focus pool']

class GameException(Exception):
	pass
	
class NotEnoughCardsException(GameException):
	def __str__(self):
		return "Not enough cards in zone."

class NoSuchCardException(GameException):
	def __init__(self, cgid):
		GameException.__init__(self)
		self.cgid = cgid
	
	def __str__(self):
		return "Card %d not found." % self.cgid

class NoSuchPlayerException(GameException):
	def __init__(self, pid):
		GameException.__init__(self)
		self.pid = pid
	
	def __str__(self):
		return "Player %d not found." % pid

class NoSuchZoneException(GameException):
	def __init__(self, zid):
		GameException.__init__(self)
		self.zid = zid
	
	def __str__(self):
		return "Zone %d not found." % zid


class TokenTemplate:
	"""A templated token type."""
	def __init__(self, name, image=None):
		if image is None:
			image = 'images/token_generic.png'
		
		self.name = name
		self.image = image

#--------------------
# Added 08-23-2008 by PCW
# This is the card marker Template
#--------------------
class MarkerTemplate:
	"""A templated marker type."""
	def __init__(self, name, image=None):
		if image is None:
			image = MARKER_DEFAULT_IMAGE
		
		self.name = name
		self.image = image
		
class Card:
	"""A single card involved in the game. Represents an instance of a single card, not the information on it."""
	def __init__(self, cgid, data = None):
		self.cgid = cgid         # In-game ID.
		self.data = data         # Card data.
		self.location = None     # Cards start out in Limbo.
		self.position = (0, 0)   # x/y position of card when in the play area.
		self.faceUp = False      # Face down by default.
		self.dead = False        # Dead (vs. discarded)?
		self.tapped = False      # Tapped status.
		self.dynasty = False     # Dynasty/fate status. We must keep track of this separately from data.
		self.tokens = {}         # Tokens on this card.
		self.markers = {}		 # Markers on this card.
		self.dishonored = False  # Honorable status.
	
	def MoveToTop(self, zone = None):
		"""Move a card to the top of another zone, or its current zone if no zone is specified."""
		if zone is None:
			zone = self.location
		self.Extract()
		zone.PutTop(self)
	
	def MoveToBottom(self, zone = None):
		"""Move a card to the bottom of another zone, or its current zone if no zone is specified."""
		if zone is None:
			zone = self.location
		self.Extract()
		zone.PutBottom(self)
	
	def Extract(self):
		"""Extract a card from wherever it's located and move it to limbo."""
		if self.location:
			self.location.Remove(self)

	def GetName(self):
		"""Return the best name for this card the currently known state allows."""
		try:
			return self.data.name
		except AttributeError:
			return "unknown card #%d" % self.cgid
	
	def GetStyledName(self):
		try:
			return "#card:%s#" % self.data.id
		except AttributeError:
			return "unknown card #%d" % self.cgid
	
	def IsDynasty(self):
		"""Return whether this is a dynasty card or not."""
		try:
			return self.data.isDynasty()  # If we have data, it is authoritative.
		except AttributeError:
			return self.dynasty
	
	def IsFate(self):
		"""Return whether this is a fate card or not."""
		try:
			return self.data.isFate() # If we have data, it is authoritative.
		except AttributeError:
			return not self.dynasty

	def NumTokens(self, type = None):
		"""Return the number of typed tokens are on this card."""
		if type is None:
			return sum(self.tokens.values())
		
		try:
			return self.tokens[type]
		except KeyError:
			return 0
		
	def SetTokens(self, type, number):
		"""Set the number of tokens of a given type on this card."""
		self.tokens[type] = number
		if number == 0:
			del self.tokens[type]
			
	#--------------------
	# Added 08-23-2008 by PCW
	# This is the card marker functions
	#--------------------
	def NumMarkers(self, type = None):
		"""Return the number of typed markers are on this card."""
		if type is None:
			return sum(self.markers.values())
		
		try:
			return self.markers[type]
		except KeyError:
			return 0
		
	def SetMarkers(self, type, number):
		"""Set the number of markers of a given type on this card."""
		self.markers[type] = number
		if number == 0:
			del self.markers[type]

	#--------------------
	# End of additions
	#--------------------
	def ZoneHeight(self):
		try:
			return self.location.cards.index(self.cgid)
		except AttributeError:
			return None

class Zone:
	"""A single zone existing somewhere in the game."""
	# The cards in a zone are ordered from bottom (0) to top (n-1). The zone contains their cgids only.
	
	def __init__(self, zid, owner):
		self.zid = zid  # This zone's ID.
		self.owner = owner  # The player owning the zone.
		self.cards = []  # Contents.
	
	def __iter__(self):
		return self.cards.__iter__()
	
	def __len__(self):
		return len(self.cards)
	
	def __contains__(self, key):
		return key in self.cards
	
	def index(self, cgid):
		return self.cards.index(cgid)
	
	def PutTop(self, card):
		"""Moves a card to the top of this zone."""
		card.Extract()  # Make sure it's not already somewhere first
		card.location = self
		self.cards.append(card.cgid)
		
	def PutBottom(self, card):
		"""Move a card to the bottom of this zone."""
		card.Extract()  # Make sure it's not already somewhere first
		card.location = self
		self.cards.insert(0, card.cgid)
	
	def Remove(self, card):
		"""Remove a card from this zone."""
		card.location = None
		self.cards.remove(card.cgid)
	
	def BottomCard(self):
		try:
			return self.cards[0]
		except IndexError:
			return None
		
	def BottomCards(self, n):
		"""Return the bottom n card of this zone."""
		if len(self.cards) < n:
			raise NotEnoughCardsException()
		return self.cards[:n]
	
	def TopCard(self):
		"""Return the top card of this zone."""
		try:
			return self.cards[-1]
		except IndexError:
			return None

	def TopCards(self, n):
		"""Return the top n card of this zone."""
		if len(self.cards) < n:
			raise NotEnoughCardsException()
		return self.cards[-n:]
	
	def __str__(self):
		return "Zone (%d-%d -- %d cards)" % (self.owner.pid, self.zid, len(self.cards))

class Player:
	"""A single player involved in the game."""
	def __init__(self, pid, name):
		self.pid = pid  # Own player ID
		self.name = name  # Name
		
		self.familyHonor = 0  # Family honor
		
		self.zones = []
		for zone in xrange(0, NUM_ZONES):
			self.zones.append(Zone(zone, self))
	
	def FindZone(self, zid):
		return self.zones[zid]
	
class GameState:
	"""A complete game state. Should exist and be synchronized on both sides of a net connection."""
	def __init__(self, db):
		self.players = {}
		self.cards = {}
		self.favor = None  # Who has the Imperial Favor?
		self.cardDB = db

	def FindCard(self, cgid):
		"""Locate a single card by cgid, no matter where it is, and return it."""
		try:
			return self.cards[cgid]
		except KeyError:
			raise NoSuchCardException(cgid)

	def FindCardByName(self, cardname):
		try:
			return self.cardDB.FindCardByName(cardname)
		except KeyError:
			raise NoSuchCardException(cardname)
	
	def HasPlayer(self, pid):
		"""Return whether we have a player with a given ID."""
		return self.players.has_key(pid)
	
	def GetPlayer(self, pid):
		"""Return the player associated with a given ID."""
		try:
			return self.players[pid]
		except:
			raise NoSuchPlayerException(pid)
	FindPlayer = GetPlayer
	
	def FindZone(self, pid, zid):
		"""Return a zone from pid/zid."""
		try:
			return self.GetPlayer(pid).zones[zid]
		except KeyError:
			raise NoSuchZoneException(zid)



# Load token templates.
TokenTemplates = []
TokenNames = {}

#-------------------------------
# Added 08-23-2008 By PCW
#------------------------------
#Load Marker Templates
MarkerTemplates = []
MarkerNames = {}

def AddMarkerTemplate(name, image=MARKER_DEFAULT_IMAGE):
	imagePath = MARKER_IMAGE_PREFIX + image + MARKER_IMAGE_EXTENSION
	tpl = MarkerTemplate(name, imagePath)
	MarkerTemplates.append(tpl)
	MarkerNames[name] = len(MarkerTemplates) - 1

def FindMarkerTemplate(self, name):
	for marker in self.MarkerTemplates:
		if marker.name == name:
			return marker

	return None

try:
	for line in file('markers.dat', 'rb'):
		args = line.strip().split(':')
		if len(args) != 2:
			continue
		AddMarkerTemplate(*args)
except IOError:
	pass


#-------------------------------
# End Additions
#------------------------------


def AddTokenTemplate(name, image=TOKEN_DEFAULT_IMAGE):
	tpl = TokenTemplate(name, image)
	TokenTemplates.append(tpl)
	TokenNames[name] = len(TokenTemplates) - 1

try:
	for line in file('tokens.dat', 'rb'):
		args = line.strip().split(':')
		if len(args) != 2:
			continue
		AddTokenTemplate(*args)
except IOError:
	pass

