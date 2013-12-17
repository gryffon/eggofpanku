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
"""Networking module for Egg of P'an Ku."""

import wx
import wx.lib.newevent
import socket
import select
import sys
import threading
import types
import simplejson
import random

#Local Imports
from game import game
from gui import canvas, playfield


from settings.xmlsettings import settings


DEFAULT_PORT = 18072
DEFAULT_GAMEMATCH_PORT = 1023
MAX_RECV = 4096
NET_PROTOCOL_VERSION = 8


ClientDisconnectedEvent,    EVT_CLIENT_DISCONNECTED      = wx.lib.newevent.NewEvent()
ClientRejectedEvent,        EVT_CLIENT_REJECTED          = wx.lib.newevent.NewEvent()
ClientWelcomeEvent,         EVT_CLIENT_WELCOME           = wx.lib.newevent.NewEvent()
ClientClientJoinEvent,      EVT_CLIENT_CLIENT_JOIN       = wx.lib.newevent.NewEvent()
ClientClientQuitEvent,      EVT_CLIENT_CLIENT_QUIT       = wx.lib.newevent.NewEvent()
ClientClientNamesEvent,     EVT_CLIENT_CLIENT_NAMES      = wx.lib.newevent.NewEvent()
ClientNameEvent,            EVT_CLIENT_NAME              = wx.lib.newevent.NewEvent()
ClientChatEvent,            EVT_CLIENT_CHAT              = wx.lib.newevent.NewEvent()
ClientDeckSubmittedEvent,   EVT_CLIENT_DECK_SUBMITTED    = wx.lib.newevent.NewEvent()
ClientDeckUnsubmittedEvent, EVT_CLIENT_DECK_UNSUBMITTED  = wx.lib.newevent.NewEvent()
ClientGameSetupEvent,       EVT_CLIENT_GAME_SETUP        = wx.lib.newevent.NewEvent()
ClientGameStartEvent,       EVT_CLIENT_GAME_START        = wx.lib.newevent.NewEvent()
ClientPlayerJoinEvent,      EVT_CLIENT_PLAYER_JOIN       = wx.lib.newevent.NewEvent()
ClientSetZoneEvent,         EVT_CLIENT_SET_ZONE          = wx.lib.newevent.NewEvent()
ClientRevealCardEvent,      EVT_CLIENT_REVEAL_CARD       = wx.lib.newevent.NewEvent()
ClientPreMoveCardEvent,     EVT_CLIENT_PRE_MOVE_CARD     = wx.lib.newevent.NewEvent()
ClientMoveCardEvent,        EVT_CLIENT_MOVE_CARD         = wx.lib.newevent.NewEvent()
ClientSetCardPropertyEvent, EVT_CLIENT_SET_CARD_PROPERTY = wx.lib.newevent.NewEvent()
ClientZoneShuffledEvent,    EVT_CLIENT_ZONE_SHUFFLED     = wx.lib.newevent.NewEvent()
ClientViewZoneEvent,        EVT_CLIENT_VIEW_ZONE         = wx.lib.newevent.NewEvent()
ClientSetFamilyHonorEvent,  EVT_CLIENT_SET_FAMILY_HONOR  = wx.lib.newevent.NewEvent()
#Added by PCW 10/04/2008
ClientSetMarkersEvent,      EVT_CLIENT_SET_MARKERS       = wx.lib.newevent.NewEvent()
ClientSetTokensEvent,       EVT_CLIENT_SET_TOKENS        = wx.lib.newevent.NewEvent()
ClientNewCardEvent,         EVT_CLIENT_NEW_CARD          = wx.lib.newevent.NewEvent()
ClientCreateCardEvent,      EVT_CLIENT_CREATE_CARD       = wx.lib.newevent.NewEvent()

ClientPeekOpponentCardEvent, EVT_CLIENT_PEEK_OPPONENT_CARD = wx.lib.newevent.NewEvent()
ClientPeekCardEvent,        EVT_CLIENT_PEEK_CARD         = wx.lib.newevent.NewEvent()

ClientFlipCoinEvent,        EVT_CLIENT_FLIP_COIN         = wx.lib.newevent.NewEvent()
ClientRollDieEvent,         EVT_CLIENT_ROLL_DIE          = wx.lib.newevent.NewEvent()
ClientFavorEvent,           EVT_CLIENT_FAVOR             = wx.lib.newevent.NewEvent()
ClientShowZoneEvent,        EVT_CLIENT_SHOW_ZONE         = wx.lib.newevent.NewEvent()


GameMatchNoOpponentEvent,    EVT_GAMEMATCH_NO_OPPONENT    = wx.lib.newevent.NewEvent()
GameMatchOpponentFoundEvent, EVT_GAMEMATCH_OPPONENT_FOUND = wx.lib.newevent.NewEvent()
GameMatchLoggedInEvent,      EVT_GAMEMATCH_LOGGED_IN      = wx.lib.newevent.NewEvent()
#ClientEvent, EVT_CLIENT_ = wx.lib.newevent.NewEvent()


def Msg(_action, **kwargs):
	"""Create a message suitable for sending over the network."""
	return (_action, kwargs)

class ServerGameState(game.GameState):
	"""A game state on the server side."""
	def __init__(self, db):
		game.GameState.__init__(self, db)
		self.nextPid = 1
		self.nextCgid = 1
		
	
	def AddPlayer(self, name, dynasty = None, fate = None):
		"""Add a new player to the game and return it. Optionally, supply the player's decks as arguments."""
		p = game.Player(self.nextPid, name)
		self.players[p.pid] = p
		self.nextPid += 1

		
		borderKeep = self.FindCardByName('Border Keep')
		keepcard = self.AddCard(borderKeep)
		p.zones[game.ZONE_DUMMY].PutTop(keepcard)
		
		bambooHarvesters= self.FindCardByName('Bamboo Harvesters')	
		bamboocard = self.AddCard(bambooHarvesters)
		p.zones[game.ZONE_DUMMY].PutTop(bamboocard)

		# Submit cards, too.
		if dynasty:
			for cdid in dynasty:
				card = self.AddCard(self.cardDB[cdid])  # Create the card...
				if (card.data.name != 'Border Keep') and (card.data.name != 'Bamboo Harvesters'):
					card.MoveToTop(p.zones[game.ZONE_DECK_DYNASTY])  # ... and move it into the deck.
				else:
					print 'Card \'%s\' removed from deck' % (card.data.name)
		if fate:
			for cdid in fate:
				card = self.AddCard(self.cardDB[cdid])  # Create the card...
				card.MoveToTop(p.zones[game.ZONE_DECK_FATE])  # ... and move it into the deck.
		
		# Done
		return p
	
	def AddCard(self, data = None):
		"""Add a single card to the game and return it. The card will originally exist in limbo."""
		card = game.Card(self.nextCgid, data)
		self.cards[card.cgid] = card
		self.nextCgid += 1
		return card

	def ShuffleZone(self, pid, zid):
		"""Shuffle a zone, that is, randomly permute what cdid is associated with each cgid in it."""
		# We're doing Fisher-Yates shuffling.
		# random between 1 and 3 times
		zone = self.FindZone(pid, zid)
		i = 0
		random_shuffle =random.randint(1,3)
		
		while i < random_shuffle:
			i += 1
			n = len(zone.cards)
			while n > 1:
				k = random.randrange(n)
				n -= 1
				card_k = self.FindCard(zone.cards[k])
				card_n = self.FindCard(zone.cards[n])
				temp = card_k.data
				card_k.data = card_n.data
				card_n.data = temp


class ClientCard(game.Card):
	"""A client-side card."""
	def __init__(self, client, db):
		game.Card.__init__(self, db)
		self.client = client
		self.attached_to = None
		self.attached_cards = []
	
	def Isolate(self):
		"""Detach everything associated with this card, ensuring the card is
		entirely isolated from other cards, neither attached to nor attaching
		any of them."""
		self.Detach()
		self.DetachOthers()
		
	def Detach(self):
		"""Detach this card from whatever it's attached to."""
		if self.attached_to is not None:
			self.attached_to.attached_cards.remove(self)
			self.attached_to.AdjustAttachments()
			self.attached_to = None
	
	def DetachOthers(self):
		"""Detach all other cards attached to this card."""
		for card in self.attached_cards:
			card.attached_to = None
		self.attached_cards = []
	
	def AdjustAttachments(self):
		"""Adjust the positions of all attachments on this card."""
		for idx, acard in enumerate(self.attached_cards):
			self.client.Send(Msg('move-card', cgid=acard.cgid, pid=self.location.owner.pid, \
				zid=self.location.zid, x=self.x, y=self.y - 5 * (idx + 1)))
	
class ClientGameState(game.GameState):
	"""A game state on the client side."""
	def __init__(self, client, db):
		game.GameState.__init__(self, db)
		self.client = client
		self.localPlayer = None
		
	def AddPlayer(self, pid, name):
		"""Add a newly received player to the game."""
		p = game.Player(pid, name)
		self.players[pid] = p
		return p
	
	def AddCard(self, cgid):
		"""Add a card to the game."""
		card = ClientCard(self.client, cgid)  # Note that the card is anonymous, i.e. has no valid data member.
		self.cards[cgid] = card
		return card
		
	def MyZone(self, zid):
		"""Return a zone belonging to this player."""
		try:
			return self.localPlayer.zones[zid]
		except KeyError:
			return None
	
	def InvalidateZone(self, pid, zid):
		"""Invalidate a zone, that is, forget what data corresponds to cards in it."""
		zone = self.FindZone(pid, zid)
		for cgid in zone:
			self.FindCard(cgid).data = None

class ServerClient:
	"""Server-side representation of a client connected to the server"""
	def __init__(self, clid, socket, name):
		self.socket = socket  # Socket primitive.
		self.name = name  # This client's name.
		self.alive = True  # Is this still a sane, living client?
		self.clid = clid  # This client's ID as stored in the server structure.
		self.readBuffer = ''
		self.msgQueue = []  # Queue of unhandled messages, first index being the oldest.
		self.handshake_ok = False  # Has gone through handshaking process correctly?
		
		# Game-specific. Typically things like decks go here.
		self.dynastyDeck = []  # Dynasty deck.
		self.fateDeck = []  # Fate deck.
	
	def Close(self):
		"""Shut down all stuff associated with this client."""
		self.socket.close()
		#self.socket = None  # No! Bad!
		self.alive = False
	
	def Update(self):
		"""Update the network aspects of the client and updates its message queue."""
		try:
			data = self.socket.recv(MAX_RECV)
		except socket.error, (code, msg):
			self.Close()  # Error.
			return
		
		if not data:  # Graceful disconnect.
			self.Close()
			return

		# Add what we received to our read buffer and chop it into messages.
		self.readBuffer += data
		while True:
			# \n is the message delimiter.
			cut = self.readBuffer.find('\n')
			if cut == -1:
				break
			
			# Add the raw message to the queue, then remove it from the buffer.
			self.msgQueue.append(self.readBuffer[:cut])
			self.readBuffer = self.readBuffer[cut+1:]

	def Send(self, msg):
		"""Sends a message to the client."""
		if self.alive:
			self._SendRaw(simplejson.dumps(msg)+'\n')
	
	def _SendRaw(self, data):
		try:
			sent = 0
			while sent < len(data):
				sent += self.socket.send(data[sent:])
		except socket.error, (code, msg):
			self.Close()

	def SetDeck(self, cards):
		"""Sets up the player's deck prototype from a list of card database IDs."""
		self.dynastyDeck = []
		self.fateDeck = []
		
		# Add all the cards
		for (count, cdid) in cards:
			card = self.cardDB[cdid]
			for i in xrange(0, count):
				if card.isDynasty():
					self.dynastyDeck.append(cdid)
				else:
					self.fateDeck.append(cdid)
	
	def HasDeck(self):
		"""Return whether this client has a deck or not."""
		return (self.dynastyDeck and self.fateDeck)

def MustBePlayer(fun):
	"""Decorator for enforcing that a client is a player."""
	def foo(self, client, *args, **kwargs):
		if client.player:
			fun(self, client, *args, **kwargs)
	return foo

class Server(threading.Thread):
	"""Main server controller. Handles all the server-side business logic, including networking. Runs in its own thread."""
	def __init__(self, db, port = None):
		threading.Thread.__init__(self)
		
		# Card database
		self.cardDB = db
		
		# Network-related setup.
		if port: self.port = port
		else: self.port = DEFAULT_PORT
		self.clients = []  # All connected clients.
		
		# Abort event; is set when the server should be shut down for some reason.
		self.abort = threading.Event()
		# Game start event. It's an event so that the actual game start will be run in the server thread.
		self.gameStart = threading.Event()
		
		self.gameState = None
		
	def Stop(self):
		"Tells the server it should stop. The thread should be joined afterwards."
		self.abort.set()
	
	def RequestStartGame(self):
		self.gameStart.set()
	
	def Setup(self):
		listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		listener.bind(('', self.port))
		listener.listen(5)
		self.listener = listener
		self.localaddress = '%s:%d' % (socket.gethostbyname(socket.gethostname()), listener.getsockname()[1])
		
	def run(self):
		"Thread implementation. Main business logic."
		# Create and start listening on the specified port for incoming connections.
		# Sockets to select for input on.
		insockets = [self.listener]
		
		while not self.abort.isSet():
			# Wait for something interesting to happen.
			inready,outready,exready = select.select(insockets, [], [], 0.1)
			
			# Do we have an incoming connection?
			if self.listener in inready:
				# Accept the connection...
				client, address = self.listener.accept()
				
				# Make a new ServerClient for it. Use the host part of the address as its default name.
				# TODO: Replace an existing dead client instead of pushing a new one all the time.
				newclient = ServerClient(len(self.clients), client, address[0])
				newclient.cardDB = self.cardDB
				self.clients.append(newclient)
				insockets.append(client) # Add it to the read group too.
				
				# We must now await handshaking.
			
			# Check for any interesting data from already existing clients.
			for c in self.clients:
				if c.alive and c.socket in inready:
					c.Update()
					
					if c.alive:
						# Process messages
						while len(c.msgQueue) > 0:
							self.ProcessRequest(c, c.msgQueue.pop(0))
					
					if not c.alive:
						# If we're not alive after an update, it means we disconnected for some reason.
						insockets.remove(c.socket)
						self.Broadcast(Msg('client-quit', clid=c.clid))
						continue
			
			# Check the game start event has been set...
			if self.gameStart.isSet():
				self.gameStart.clear()
				self.StartGame()
	
	def Broadcast(self, msg):
		"Broadcasts a message to all connected and handshaken clients."
		msg = simplejson.dumps(msg)+'\n' # Create a JSON dump first.
		for c in self.clients:
			if c.alive and c.handshake_ok:
				c._SendRaw(msg)
	
	def Started(self):
		return self.gameState is not None
		
	def StopGame(self):
		pass
	
	def StartGame(self):
		# Stop any existing games first
		self.StopGame()
		
		# First, create a brand new game state.
		self.gameState = ServerGameState(self.cardDB)
		self.gameState.favor = None
		

		self.Broadcast(('game-setup', {}))
		
		# Add those clients who have submitted decks as players.
		for c in self.clients:
	
			#self.gameState.favor = None
			
			#self.Broadcast(Msg('set-favor', pid=-1))

			if c.HasDeck():
				c.player = self.gameState.AddPlayer(c.name, c.dynastyDeck, c.fateDeck)
				c.player.client = c
				
				# Tell everyone they've joined the game
				self.Broadcast(('player-join', {'clid':c.clid, 'pid':c.player.pid}))
				
				# Inform everyone what cgids are in their decks. Does not actually reveal what the cards "are".
				for zone in c.player.zones:
					if len(zone.cards) > 0:
						self.Broadcast(Msg('set-zone', pid=c.player.pid, zid=zone.zid, cgids=[cgid for cgid in zone.cards]))

		# Ready to go!
		self.Broadcast(('game-start', {}))

		
		# Post game start, do some more processing.
		for player in self.gameState.players.itervalues():
			# Now shuffle their decks.
			self.gameState.ShuffleZone(player.pid, game.ZONE_DECK_FATE)
			self.gameState.ShuffleZone(player.pid, game.ZONE_DECK_DYNASTY)
			
			#Added 01/07/2009 by BSB
			#draw 4 Dynasty cards per player
			cardSpacing = settings.canvas_card_spacing
			CANVAS_CARD_AND_GRID = ((canvas.CANVAS_CARD_W*2) + (playfield.CANVAS_MOVE_SNAP * cardSpacing))

			provToDraw = 4
			dynDeck = player.zones[game.ZONE_DECK_DYNASTY]
			
			leftProv = (provToDraw - (provToDraw // 2)) * CANVAS_CARD_AND_GRID
			prov = 2
			for	cgid in reversed(dynDeck.TopCards(provToDraw)):
				prov_loc_x = (prov * CANVAS_CARD_AND_GRID) - leftProv
				self.HandleMoveCard(player.client, cgid, player.pid, game.ZONE_PLAY, x=prov_loc_x, y=0, faceup=False)
				prov += 1
			
			# Find their Stronghold.
			bothDecks = player.zones[game.ZONE_DECK_FATE].cards + player.zones[game.ZONE_DECK_DYNASTY].cards
			if cardSpacing == 1:
				strongLoc = 2 - (leftProv + CANVAS_CARD_AND_GRID)
			else:
				strongLoc = 2 - (leftProv + (CANVAS_CARD_AND_GRID * (cardSpacing)))
				
			for cgid in bothDecks:
				card = self.gameState.FindCard(cgid)
				if card.data.type == 'stronghold':
					# Found it!
					self.HandleMoveCard(player.client, cgid, player.pid, game.ZONE_PLAY, x=strongLoc, y=0, faceup=True)
					# Also set family honor.
					self.HandleSetFamilyHonor(player.client, honor=int(card.data.starting_honor))
					break

			#Put Bamboo Harversters and Border Keep into play
			if settings.use_celestial_holdings == True:
				borderKeepLoc = (strongLoc - (CANVAS_CARD_AND_GRID))
				bambooLoc = (borderKeepLoc - (CANVAS_CARD_AND_GRID))

				#Get Border Keep and put it in play
				keepCgid = player.zones[game.ZONE_DUMMY].cards[0]
				keepcard = self.gameState.FindCard(keepCgid)
				#Get harvesters and put it in play
				bambooCgid = player.zones[game.ZONE_DUMMY].cards[1]
				bamboocard = self.gameState.FindCard(bambooCgid)

				self.HandleMoveCard(player.client, keepCgid, player.pid, game.ZONE_PLAY, x=borderKeepLoc, y=0, faceup=True)
				self.HandleMoveCard(player.client, bambooCgid, player.pid, game.ZONE_PLAY, x=bambooLoc, y=0, faceup=True)
				#Bow Harvesters
				self.HandleSetCardProperty(player.client,bambooCgid, property='tapped', value=True)
				
			#Added 1/5/2009 by PCW
			#draw 5 Fate cards per player
			zone = player.zones[game.ZONE_DECK_FATE]

			#Added change to card draw.
			cardDraw = 6

			if settings.legacy_card_draw == True:
				cardDraw = 5
				
			for cgid in reversed(zone.TopCards(cardDraw)):
				self.HandleMoveCard(player.client,cgid,player.pid,game.ZONE_HAND,x=0,y=0,faceup=True)

		
	def ProcessRequest(self, client, data):
		"Handles a request sent from the specified client."
		action, parameters = simplejson.loads(data)

##		print '[Server] Data:\r\n%s' % (data)
		
		# Figure out handler name.
		name = 'Handle' + ''.join(part.capitalize() for part in action.split('-'))
		try:
			function = getattr(self, name)
		except AttributeError:
			# If there's no net handler for this message, leave it unhandled.
			print "[Server] Warning: Unhandled message '%s'.\r\ndata: %s" % (action,data)
			return
		
		# The dict keys are likely to be unicode strings, and must be turned into bytestrings before they work as kwargs.
		parameters = dict(((k.encode(), v) for k, v in parameters.iteritems()))
		
		try:
			function(client, **parameters)
		except Exception, e:
			print '[Server] Warning: Error executing "%s" handler: %s' % (action, str(e))
	
	def HandleProtocol(self, client, version):
		if version != NET_PROTOCOL_VERSION:
			client.Send(Msg('rejected', msg='Your client protocol version is wrong (got %d, needs %d)' % (version, NET_PROTOCOL_VERSION)))
		elif self.Started():
			client.Send(Msg('rejected', msg='Cannot join a game in progress'))
		else:
			# Okay, great!
			client.handshake_ok = True
			
			# Send some welcome information to the new client.
			client.Send(Msg('welcome', clid=client.clid))
				
			clientNames = [(c.clid, c.name) for c in self.clients if c.alive and c != client]
			client.Send(Msg('client-names', names=clientNames))
			
			# He also needs to know if anyone has already submitted decks.
			for c in self.clients:
				if c != client and c.HasDeck():
					client.Send(Msg('deck-submitted', clid=c.clid))
					
			# Tell everyone it joined, too.
			self.Broadcast(Msg('client-join', clid=client.clid))
			
			return
		
		client.Close()
		return
		
	def HandleName(self, client, value):
		"""Handle a 'name' request."""
		client.name = value
		self.Broadcast(Msg('name', clid=client.clid, value=client.name))
	
	def HandleChat(self, client, msg):
		self.Broadcast(Msg('chat', clid=client.clid, msg=msg))
	
	def HandleSubmitDeck(self, client, cards):
		client.SetDeck(cards)
		self.Broadcast(Msg('deck-submitted', clid=client.clid))

	def HandleUnsubmitDeck(self, client):
		client.SetDeck([])
		self.Broadcast(Msg('deck-unsubmitted', clid=client.clid))

	@MustBePlayer
	def HandleShuffleZone(self, client, zid):
		"""Handle a shuffle request."""
		# Shuffling is done by randomly rearranging what cdids each cgid corresponds to.
		# It should only be done to decks, so check that.
		if zid not in [game.ZONE_DECK_FATE, game.ZONE_DECK_DYNASTY]:
			return
		
		self.gameState.ShuffleZone(client.player.pid, zid)
		self.Broadcast(Msg('zone-shuffled', pid=client.player.pid, zid=zid))

	@MustBePlayer
	def HandlePeekOpponent(self, client, cgid, pid):
		"""Handle a peek-card request."""
		try:
			card = self.gameState.FindCard(cgid)
		except NoSuchCardException:
			return

		for opponentPid in self.clients:
			try:
				oPid = opponentPid.clid
				
				if oPid != client.clid:
					self.RevealCard(card, opponentPid.player)
			except Exception, e:
				print '[HandlePeekOpponent] problem revealing a card. \r\n %s' % e
			
		self.Broadcast(Msg('peek-opponent', pid=pid, cgid=cgid))
	
	@MustBePlayer
	def HandlePeekCard(self, client, cgid):
		"""Handle a peek-card request."""
		card = self.gameState.FindCard(cgid)
		self.RevealCard(card, client.player)
		self.Broadcast(Msg('peek-card', pid=client.player.pid, cgid=cgid))
	
	@MustBePlayer
	def HandleMoveRandom(self, client, pid, zid, fromzid):
		zone = self.gameState.FindZone(pid, fromzid)
		if len(zone) == 0:
			return
		cgid = random.choice(zone.cards)
		self.MoveCard(client, cgid, pid, zid, random=True)
	
	@MustBePlayer
	def HandleMoveCard(self, client, cgid, pid, zid, top=None, x=None, y=None, faceup=None):
		"""Handle a 'move-card' request."""
		self.MoveCard(client, cgid, pid, zid, top, x, y, faceup, random=False)

	@MustBePlayer
	def HandleSetCardProperty(self, client, cgid, property, value):
		"""Handle the 'set-card-property' message."""
		try:
			card = self.gameState.FindCard(cgid)
		except NoSuchCardException:
			return
		
		if card.location and card.location.owner != client.player:
			return  # We can only change properties on cards we control.
		
		# Make sure it's actually going to change.
		if getattr(card, property) == value:
			return
		
		# If we're changing a cards facing, we might need to reveal it.
		if property == 'faceUp' and value:
			self.RevealCard(card)
			
		setattr(card, property, value)
		self.Broadcast(Msg('set-card-property', pid=client.player.pid, cgid=cgid, property=property, value=value))
	
	@MustBePlayer
	def HandleViewZone(self, client, pid, zid, number=0):
		"""Handle the 'view-zone' message, requesting being shown the contents a zone."""
		# Just so no one starts looking at other players' hands.
		if zid == game.ZONE_HAND:
			return
		zone = self.gameState.FindZone(pid, zid)
		
		if number <= 0:
			slice = zone.cards[number:]
		else:
			slice = zone.cards[:number]
		
		for cgid in zone:  # Reveal all cards in that zone to the player.
			self.RevealCard(self.gameState.FindCard(cgid), client.player)
		
		self.Broadcast(Msg('view-zone', viewer=client.player.pid, pid=pid, zid=zid, number=number))
	
	@MustBePlayer
	def HandleSetFamilyHonor(self, client, honor):
		"""Handle the 'set-family-honor' message, requesting a change of the player's family honor."""
		client.player.familyHonor = honor
		self.Broadcast(Msg('set-family-honor', pid=client.player.pid, honor=honor))
	
	@MustBePlayer
	def HandleTakeFavor(self, client):
		if client.player is not self.gameState.favor:  # Only if we don't already control it.
			self.gameState.favor = client.player
			self.Broadcast(Msg('set-favor', pid=client.player.pid))

	@MustBePlayer
	def HandleDiscardFavor(self, client):
		if client.player is self.gameState.favor:  # Only if we control it.
			self.gameState.favor = None
			self.Broadcast(Msg('set-favor', pid=-1))

	@MustBePlayer
	def HandleSetTokens(self, client, cgid, token, number):
		card = self.gameState.FindCard(cgid)
		if card.location.owner != client.player:  # We can only put tokens on our own guys.
			return
		
		if number < 0:  # There can't be fewer than no tokens on a card.
			number = 0;
			
		card.SetTokens(token, number)
		self.Broadcast(Msg('set-tokens', pid=client.player.pid, cgid=cgid, token=token, number=number))

	#--------------------
	# Added 10-04-2008 by PCW
	# This is the card marker functions
	#--------------------
	
	@MustBePlayer
	def HandleSetMarkers(self, client, cgid, token, number, image):
		card = self.gameState.FindCard(cgid)
		if card.location.owner != client.player:  # We can only put markers on our own guys.
			return
		
		if number < 0:  # There can't be fewer than no markers on a card.
			number = 0;
		card.SetMarkers(token, number)
		self.Broadcast(Msg('set-markers', pid=client.player.pid, cgid=cgid, token=token, number=number, image=image))

	#--------------------
	# End of additions
	#--------------------
		
	@MustBePlayer
	def HandleCreateCard(self, client, id=None, **kwargs):
		"""Handle a create-card request. This one is tricky!"""
		# First, figure out whether we should know about this or not.
		if id is not None:
			pass
		else:
			id = self.cardDB.CreateCard(**kwargs) # Add it to the database, then.
			self.Broadcast(Msg('new-card', id=id, **kwargs))  # Advertise it to the world.
		
		# Okay, now we can create it for real.
		card = self.gameState.AddCard(self.cardDB[id])
		self.Broadcast(Msg('create-card', cgid=card.cgid, cdid=id, pid=client.player.pid, zid=game.ZONE_HAND))
	
	def RevealCard(self, card, player = None):
		"""Reveal a card either to all or only one player.
		
		Arguments:
		card -- the card to reveal
		player -- (optional) the player to reveal the card to, or all if None (default None)
		
		"""
		msg = Msg('reveal-card', cgid=card.cgid, cdid=card.data.id)
		if not player:
			self.Broadcast(msg)
		else:
			player.client.Send(msg)
	
	def MoveCard(self, client, cgid, pid, zid, top=None, x=None, y=None, faceup=True, random=False):
		"""Move a card around."""
		card = self.gameState.FindCard(cgid)
		player = self.gameState.GetPlayer(pid)
		
		# Make sure we can actually move this card anywhere, i.e. that it belongs to us (is in one of our zones).
		if card.location and card.location.owner != client.player:
			return
			
		# Make sure the target zone is valid. Note that we CAN put cards in other people's zones; if we do, they now control the card.
		if not 0 <= zid < game.NUM_ZONES:
			return
			
		# Rearranging cards in certain zones makes no sense.
		if self.gameState.GetPlayer(pid).zones[zid] == card.location and card.location.zid in [game.ZONE_FOCUS_POOL, game.ZONE_HAND]:
			return
		
		# Override faceup for deck zones.
		if zid in [game.ZONE_DECK_FATE, game.ZONE_DECK_DYNASTY]:
			faceup = False
		
		# If this is moving anywhere except play, make sure there are no tokens on it.
		if zid != game.ZONE_PLAY:
			tokTypes = [token for token in card.tokens]
			for token in tokTypes:
				self.HandleSetTokens(client, cgid=card.cgid, token=token, number=0)
			#remove all markers
			
			markerTypes = [game.FindMarkerTemplate(game,markertoken) for markertoken in card.markers]
			for marker in markerTypes:
				self.HandleSetMarkers(client, cgid=card.cgid, token=marker.name, number=0, image=marker.image)
						
		# Do the move... if applicable.
		if top is None and card.location.zid == zid and card.location.owner.pid == pid:
			pass
		elif not top:
			card.MoveToBottom(self.gameState.GetPlayer(pid).zones[zid])
		else:
			card.MoveToTop(self.gameState.GetPlayer(pid).zones[zid])
			
		if zid in [game.ZONE_DISCARD_FATE, game.ZONE_DISCARD_DYNASTY, game.ZONE_REMOVED]:  # These zones are public and all cards are face up, so the card needs to be revealed first.
			self.RevealCard(card)
			
		if zid in [game.ZONE_HAND, game.ZONE_FOCUS_POOL]:  # This is someone's hand or focus pool, so reveal it to that player.
			self.RevealCard(card, player)
		
		extra = {}
		if zid == game.ZONE_PLAY:
			# Reset dead flag.
			self.HandleSetCardProperty(client, cgid=card.cgid, property='dead', value=False)
			
			# Also set x/y and facing.
			if x is not None and y is not None:
				card.x = x
				card.y = y
				extra['x'] = x
				extra['y'] = y
			
			if faceup is not None:
				card.faceUp = faceup
			
			# If the card is face up, it needs to be revealed to everyone.
			if card.faceUp:
				self.RevealCard(card)
			
		# Announce the move to everyone.
		self.Broadcast(Msg('move-card', mover=client.player.pid, cgid=cgid, pid=pid, zid=zid, top=top, faceup=faceup, random=random, **extra))
	
	@MustBePlayer
	def HandleFlipCoin(self, client):
		self.Broadcast(Msg('flip-coin', pid=client.player.pid, result=(random.uniform(0, 1) < 0.5)))

	@MustBePlayer
	def HandleRollDie(self, client, size):
		self.Broadcast(Msg('roll-die', pid=client.player.pid, size=size, result=random.randint(1, size)))
	
	@MustBePlayer
	def HandleShowZone(self, client, zid):
		for cgid in client.player.zones[zid]:
			self.RevealCard(self.gameState.FindCard(cgid))
		self.Broadcast(Msg('show-zone', pid=client.player.pid, zid=zid))
	
	@MustBePlayer
	def HandleShowZoneRandom(self, client, zid, num):
		try:
			cgids = random.sample(client.player.zones[zid], num)
		except ValueError:
			return
		
		for cgid in cgids:
			self.RevealCard(self.gameState.FindCard(cgid))
		self.Broadcast(Msg('show-zone-random', pid=client.player.pid, zid=zid, cgids=cgids))

class Client(threading.Thread):
	"""Client side main business logic object. Runs in its own thread."""
	
	def __init__(self, db, localName, eventTarget = None):
		threading.Thread.__init__(self)
		
		# Card database
		self.cardDB = db
		
		# Local name and event target.
		self.localName = localName
		self._eventTarget = eventTarget
		
		# Network read buffer.
		self.readBuffer = ''
		# Abort event; is set when the client should be shut down for some reason.
		self.abort = threading.Event()
		
		# Local client ID.
		self.localClid = None
		self.localPlayer = None
		
		# The names of other clients at the table.
		self.clientNames = {}
		
		# No game state to begin with.
		self.gameState = None
	
	def Playing(self):
		"""Return whether we are playing or not."""
		return (self.localPlayer is not None)
	
	def IsLocalPlayer(self, pid):
		"""Return whether a pid is us or not."""
		return self.Playing() and (self.localPlayer.pid == pid)
		
	def Stop(self):
		"""Stop this client, disconnect, etc."""
		self.abort.set()
		
	def Connect(self, host, port = DEFAULT_PORT):
		"""Connect to a table server somewhere."""
		
		# Open up a socket and connect. In case this fail, an exception will be thrown that
		# should be caught by whatever calls this.
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((host, port))
		
		# If we get this far, connection was fine. Handshake.
		self.Send(Msg('protocol', version=NET_PROTOCOL_VERSION))
		
		# Record the parameters used
		self.host = host
		self.port = port
		
	def run(self):
		"""Run client."""
		insockets = [self.sock]
		
		while not self.abort.isSet():
			inready,outready,exready = select.select(insockets, [], [], 0.1)
			
			# We've got some data coming in? Read it, cut into messages, and process them.
			try:
				if self.sock in inready:
					data = self.sock.recv(MAX_RECV)
					if not data:
						# Disconnected :/
						self.sock.close()
						self.sock = None
						wx.PostEvent(self._eventTarget, ClientDisconnectedEvent())
						break
						
					# Add what we just got to our read buffer.
					self.readBuffer += data
					
					# Cut the buffer into messages and process.
					while True:
						cut = self.readBuffer.find('\n')
						if cut == -1:
							break
						data = self.readBuffer[:cut]
						self.readBuffer = self.readBuffer[cut+1:]
							
						# Process the message.
						#print('*** Client: Processing message %s' % data)
						self.ProcessMessage(data)
			except socket.error:
				self.sock.close()
				self.sock = None
				wx.PostEvent(self._eventTarget, ClientDisconnectedEvent())
				break
	
	def Send(self, msg):
		"""Send a message to the server through this client.
		
		Arguments:
		msg -- the message (being a tuple (action, {parameters}).
		
		"""
		msg = simplejson.dumps(msg)+'\n'
		sent = 0
		while sent < len(msg):
			sent += self.sock.send(msg[sent:])
	
	def ProcessMessage(self, data):
		"""Process an incoming message."""
		action, parameters = simplejson.loads(data)
		
		# Figure out handler name.
		name = 'Handle' + ''.join(part.capitalize() for part in action.split('-'))

		#print "Recieved message: '%s'\r\n%s." % (action, parameters)
		
		try:
			function = getattr(self, name)
		except AttributeError:
			print "[Client] Warning: Unhandled message '%s'." % action
			return
		
		# The dict keys are likely to be unicode strings, and must be turned into bytestrings before they work as kwargs.
		parameters = dict(((k.encode(), v) for k, v in parameters.iteritems()))
		
		try:
			function(**parameters)
		except Exception, e:
			print '[Client] Warning: Error executing "%s" handler: %s' % (action, str(e))
	
	def HandleRejected(self, msg):
		"""Handle connection rejection."""
		wx.PostEvent(self._eventTarget, ClientRejectedEvent(msg=msg))
		
	def HandleWelcome(self, clid):
		"""Handle the 'welcome' message."""
		self.Send(Msg('name', value=self.localName))
		
		self.localClid = clid
		self.clientNames[self.localClid] = self.localName
		wx.PostEvent(self._eventTarget, ClientWelcomeEvent(clid=self.localClid))
	
	def HandleClientJoin(self, clid):
		"""Handle the 'client-join' message, sent when a client joins the table."""
		if clid == self.localClid:
			return  # Ignore it if it's *our* join message.
		self.clientNames[clid] = None
		wx.PostEvent(self._eventTarget, ClientClientJoinEvent(clid=clid))
	
	def HandleClientQuit(self, clid):
		"""Handle the 'client-join' message, sent when a client disonnects from the table."""
		wx.PostEvent(self._eventTarget, ClientClientQuitEvent(clid=clid))
		
	def HandleClientNames(self, names):
		"""Handle the 'client-names' message."""
		for clid, name in names:
			if clid != self.localClid:
				self.clientNames[clid] = name
		wx.PostEvent(self._eventTarget, ClientClientNamesEvent(names=names))
	
	def HandleName(self, clid, value):
		"""Handle the 'name' message."""
		oldname = self.clientNames[clid]
		self.clientNames[clid] = value
		wx.PostEvent(self._eventTarget, ClientNameEvent(clid=clid, name=value, oldname=oldname))

	def HandleChat(self, clid, msg):
		"""Handle the 'chat' message."""
		wx.PostEvent(self._eventTarget, ClientChatEvent(clid=clid, msg=msg))
	
	def HandleDeckSubmitted(self, clid):
		"""Handle the 'deck-submitted' message."""
		wx.PostEvent(self._eventTarget, ClientDeckSubmittedEvent(clid=clid))
	
	def HandleDeckUnsubmitted(self, clid):
		wx.PostEvent(self._eventTarget, ClientDeckUnsubmittedEvent(clid=clid))
		
	def HandleGameSetup(self):
		"""Handle the 'game-setup' message."""
		self.gameState = ClientGameState(self, self.cardDB)  # Create a new, fresh gamestate.
		wx.PostEvent(self._eventTarget, ClientGameSetupEvent())
	
	def HandleGameStart(self):
		"""Handle the 'game-start' message."""
		wx.PostEvent(self._eventTarget, ClientGameStartEvent())
	
	def HandlePlayerJoin(self, pid, clid):
		"""Handle the 'player-join' message."""
		p = self.gameState.AddPlayer(pid, self.GetClientName(clid))
		p.clid = clid
		if clid == self.localClid:
			self.localPlayer = p
			self.gameState.localPlayer = p
		wx.PostEvent(self._eventTarget, ClientPlayerJoinEvent(clid=clid))

	def HandleSetZone(self, pid, zid, cgids):
		"""Handle the 'set-zone' message."""
		player = self.gameState.GetPlayer(pid)
		for cgid in cgids:
			card = self.gameState.AddCard(cgid)
			# Make sure the backface flag is correctly set, based on zone.
			if zid in [game.ZONE_DECK_DYNASTY, game.ZONE_DISCARD_DYNASTY]:
				card.dynasty = True
			card.MoveToTop(player.zones[zid])
		wx.PostEvent(self._eventTarget, ClientSetZoneEvent(pid=pid, zid=zid, cgids=cgids))

	def HandleRevealCard(self, cgid, cdid):
		"""Handle the 'reveal-card' message.
		
		Arguments:
		cgid -- the id of the game card to reveal
		cdid -- the card data id
		
		"""
		try:
			self.gameState.cards[cgid].data = self.cardDB[cdid]
		except KeyError:
			pass
		wx.PostEvent(self._eventTarget, ClientRevealCardEvent(cgid=cgid, cdid=cdid))

	def HandleMoveCard(self, cgid, pid, zid, top=False, mover=None, x=None, y=None, faceup=None, random=False):
		"""Handle the move-card message.
		
		cgid -- the game card id to move
		pid -- the owner of the destination zone
		zid -- the zone id of the destination zone
		top -- True if moving to the top of the destination zone, False otherwise (default False)
		mover -- pid of whoever moved the card (default None)
		x -- x position to move the card to (default None)
		y -- y position to move the card to (default None)
		faceup -- True if the card should be face up, False otherwise, or None for no change (default None)
		random -- True if the card was chosen randomly, False otherwise.
		
		"""
		card = self.gameState.FindCard(cgid)
		zone = self.gameState.FindZone(pid, zid)
		
		# Remember where we used to be.
		oldzone = card.location
		oldzonepos = oldzone.cards.index(cgid)
		oldzonesize = len(card.location)

		# Move card to the appropriate zone.
		if top is None and oldzone is zone:
			pass
		elif top:
			card.MoveToTop(zone)
		else:
			card.MoveToBottom(zone)
		
		# Update play area stuff if requested.
		if x is not None and y is not None:
			card.x = x
			card.y = y
		if faceup is not None:
			card.faceUp = faceup
		
		# Post event about it.
		wx.PostEvent(self._eventTarget, \
			ClientMoveCardEvent(card=card, \
				zone=zone, \
				zonepos=card.ZoneHeight(), \
				oldzone=oldzone, \
				oldzonepos=oldzonepos, \
				oldzonesize=oldzonesize, \
				top=top, \
				mover=mover, \
				x=x, y=y, \
				faceUp=faceup, \
				random=random))

	def HandleSetCardProperty(self, cgid, property, value, pid):
		"""Handle the 'set-card-property' message.
		
		Arguments:
		cgid -- card game id to set property of
		property -- name of property to change
		value -- value to set property to
		pid -- player performing the change
		
		"""
		card = self.gameState.FindCard(cgid)
		setattr(card, property, value)
		wx.PostEvent(self._eventTarget, ClientSetCardPropertyEvent(cgid=cgid, property=property, value=value, pid=pid))

	def HandleZoneShuffled(self, pid, zid):
		"""Handle the 'zone-shuffled' message."""
		self.gameState.InvalidateZone(pid, zid)
		wx.PostEvent(self._eventTarget, ClientZoneShuffledEvent(pid=pid, zid=zid))

	def HandleViewZone(self, viewer, pid, zid, number):
		wx.PostEvent(self._eventTarget, ClientViewZoneEvent(viewer=viewer, pid=pid, zid=zid, number=number))
	
	def HandleSetFamilyHonor(self, pid, honor):
		player = self.gameState.FindPlayer(pid)
		oldhonor = player.familyHonor
		player.familyHonor = honor
		wx.PostEvent(self._eventTarget, ClientSetFamilyHonorEvent(pid=pid, honor=honor, oldhonor=oldhonor))
	
	def HandleSetTokens(self, pid, cgid, token, number):
		card = self.gameState.FindCard(cgid)
		change = number - card.NumTokens(token)
		card.SetTokens(token, number)
		wx.PostEvent(self._eventTarget, ClientSetTokensEvent(pid=pid, cgid=cgid, token=token, number=number, change=change))

	#--------------------------
	# Added 08-23-2008 by PCW
	# These are the handlers for adding custom markers to the cards
	# Markers will be removed at the end of every turn.
	#--------------------------
	def HandleSetMarkers(self, pid, cgid, token, number, image):
		card = self.gameState.FindCard(cgid)
		change = number - card.NumMarkers(token)
		card.SetMarkers(token, number)
		wx.PostEvent(self._eventTarget, ClientSetMarkersEvent(pid=pid, cgid=cgid, token=token, number=number, change=change, image=image))

	#--------------------------
	# end of changes
	#--------------------------		
	def HandleNewCard(self, id, **kwargs):
		self.cardDB.CreateCard(id=id, **kwargs)
		wx.PostEvent(self._eventTarget, ClientNewCardEvent(cdid=id))

	def HandleCreateCard(self, cgid, cdid, pid, zid):
		card = self.gameState.AddCard(cgid)
		card.data = self.cardDB[cdid]
		card.MoveToTop(self.gameState.FindZone(pid, zid))
		wx.PostEvent(self._eventTarget, ClientCreateCardEvent(cgid=cgid, pid=pid, zid=zid))

	def HandlePeekOpponent(self,pid,cgid):
		card = self.gameState.FindCard(cgid)
		cardname= card.GetName()
		wx.PostEvent(self._eventTarget, ClientPeekOpponentCardEvent(pid=pid, cgid=cgid))
		
	def HandlePeekCard(self, pid, cgid):
#		wx.PostEvent(self._eventTarget, ClientPeekCardEvent(cgid=cgid, pid=pid))
		card = self.gameState.FindCard(cgid)
		wx.PostEvent(self._eventTarget, ClientPeekCardEvent(cgid=cgid, card=card, pid=pid))		
	
	def HandleFlipCoin(self, pid, result):
		wx.PostEvent(self._eventTarget, ClientFlipCoinEvent(result=result, pid=pid))

	def HandleRollDie(self, pid, size, result):
		wx.PostEvent(self._eventTarget, ClientRollDieEvent(result=result, size=size, pid=pid))

	def HandleSetFavor(self, pid):
		try:
			oldowner = self.gameState.favor.pid
		except AttributeError:
			oldowner = -1
		if pid != -1:
			self.gameState.favor = self.gameState.FindPlayer(pid)
		else:
			self.gameState.favor = None
		wx.PostEvent(self._eventTarget, ClientFavorEvent(pid=pid, oldpid=oldowner))
	
	def HandleShowZone(self, pid, zid):
		cgids = [c for c in self.gameState.FindZone(pid, zid)]
		wx.PostEvent(self._eventTarget, ClientShowZoneEvent(pid=pid, zid=zid, cgids=cgids, random=False))

	def HandleShowZoneRandom(self, pid, zid, cgids):
		wx.PostEvent(self._eventTarget, ClientShowZoneEvent(pid=pid, zid=zid, cgids=cgids, random=True))

	
	def GetClientName(self, clid = None):
		"""Get the name of a client."""
		if clid is None:
			return self.localName
		return self.clientNames[clid]
	
	def SubmitDeck(self, deck):
		"""Submit a deck."""
		self.Send(Msg('submit-deck', cards=deck.cards))

	def UnsubmitDeck(self):
		self.Send(Msg('unsubmit-deck'))

class GameMatchServer(threading.Thread):
	"""This is a matching Service for EOPK Players"""
	def __init__(self, host, port = DEFAULT_GAMEMATCH_PORT, eventTarget = None):
		threading.Thread.__init__(self)

		# Abort event; is set when the server should be shut down for some reason.
		self.abort = threading.Event()
		self.port = port
		self.host = host

		# Network read buffer.
		self.readBuffer = ''

		self.errorString = ''
		self._eventTarget = eventTarget

		#Opponent defaults
		self.oport= DEFAULT_PORT
		self.oip = ''

		#Socket Settings                
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def Connect(self):
			#connect to the gamematchserver
			self.sock.connect((self.host, self.port))

			# If we get this far, connection was fine. Handshake.
			self.Send(Msg('protocol', version=NET_PROTOCOL_VERSION))

			# make address variable to send to game match service
			address = '%s-%d' % (self.host,self.port)
			self.Send(Msg('login',address=address))

	def Disconnect(self):
			self.Stop()

	def GetOpponentAddress(self):
			address = '%s-%d' % (self.host,self.port)
			self.Send(Msg('get-opponent',address=address))
		
	def HandleLoggedIn(self,address):
		wx.PostEvent(self._eventTarget, GameMatchLoggedInEvent(address = address))

	def ShowNoOpponent(self):
			wx.PostEvent(self._eventTarget, GameMatchNoOpponentEvent('There are no opponents currently available.'))
			
	def HandleOpponent(self, opponentsip):
			retval = opponentsip.split('-')
			self.oip = retval[0]
			self.oport = retval[1]
			if self.oip == '000.000.000.000':
					self.ShowNoOpponent()
					return False

			wx.PostEvent(self._eventTarget, GameMatchOpponentFoundEvent(oip = self.oport, oport = self.oport))
							
	def ProcessMessage(self, data):
			"""Process an incoming message."""
			action, parameters = simplejson.loads(data)
			
			# Figure out handler name.
			name = 'Handle' + ''.join(part.capitalize() for part in action.split('-'))
			try:
					function = getattr(self, name)
			except AttributeError:
					self.errorString = "[Client] Warning: Unhandled message '%s'." % action
					print self.errorString
					return
			
			# The dict keys are likely to be unicode strings, and must be turned into bytestrings before they work as kwargs.
			parameters = dict(((k.encode(), v) for k, v in parameters.iteritems()))
			
			try:
					function(**parameters)
			except Exception, e:
					self.errorString = '[Client] Warning: Error executing "%s" handler: %s\r\n%s' % (action, str(e),data)
					print self.errorString
					return

	def run(self):
		"""Run GameMatch Client."""
		insockets = [self.sock]
		
		while not self.abort.isSet():
			inready,outready,exready = select.select(insockets, [], [], 0.1)
			
			# We've got some data coming in? Read it, cut into messages, and process them.
			try:
				if self.sock in inready:
					data = self.sock.recv(MAX_RECV)
					if not data:
						# Disconnected :/
						self.sock.close()
						self.sock = None
						break
						
					# Add what we just got to our read buffer.
					self.readBuffer += data

					# Cut the buffer into messages and process.
					while True:
						cut = self.readBuffer.find('\n')
						if cut == -1:
							break
						data = self.readBuffer[:cut]
						self.readBuffer = self.readBuffer[cut+1:]
							
						# Process the message.                  
						self.ProcessMessage(data)                       
			except socket.error:
				self.sock.close()
				self.sock = None
				break

	def Stop(self):
		"""Stop this client, disconnect, etc."""
		self.abort.set()
		
	def Send(self, msg):
		"""Send a message to the server through this client.
		
		Arguments:
		msg -- the message (being a tuple (action, {parameters}).
		
		"""
		msg = simplejson.dumps(msg)
		sent = 0
		while sent < len(msg):
			sent += self.sock.send(msg[sent:])

		
