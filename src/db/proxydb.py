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
	Proxy database module for Egg of P'an Ku.

author: Ryan Karetas
file: proxydb.py
date: 21 Jul 2014
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Table, MetaData, UniqueConstraint
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
import sys
import os

#Use for testing
if __name__ == "__main__":
	import os
	parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	os.sys.path.insert(0,parentdir) 

from settings.xmlsettings import settings
from settings.xmlsettings import locationsettings
from settings import xmlfilters

Base = declarative_base()

#association table for keywords
card_keywords = Table('card_keywords', Base.metadata,
	Column('card_id', String(10), ForeignKey('cards.id')),
	Column('keyword_id', Integer, ForeignKey('keywords.id'))
)

#association table for clans
card_clans = Table('card_clans', Base.metadata,
	Column('card_id', String(10), ForeignKey('cards.id')),
	Column('clan_id', Integer, ForeignKey('clans.id'))
)

class CardType(Base):
	"""
	Model of cardtypes table
	"""
	__tablename__ = 'cardtypes'
	__table_args__ = (UniqueConstraint('type'),)

	id = Column(Integer, primary_key=True)
	type = Column(String)

	cards = relationship("Card")

	def __repr__(self):
		return "<CardType (id='%s', type='%s'>" % (self.id, self.type)

class Set(Base):
	"""
	Model of sets table
	"""
	__tablename__ = 'sets'
	__table_args__ = (UniqueConstraint('name', 'abbreviation'),)

	id = Column(Integer, unique=True, primary_key=True)
	name = Column(String)
	abbreviation = Column(String(5))

	cards = relationship("Card")

	def __repr__(self):
		return "<Set (id='%s', name='%s', abbreviation='%s'>" % (self.id, self.name, self.abbreviation)

class Keyword(Base):
	"""
	Model of keywords table
	"""
	__tablename__ = 'keywords'
	__table_args__ = (UniqueConstraint('keyword'),)

	id = Column(Integer, primary_key=True)
	keyword = Column(String)

	def __repr__(self):
		return "<Keyword (id='%s', keyword='%s'>" % (self.id, self.keyword)

class Clan(Base):
	"""
	Model of clans table
	"""
	__tablename__ = 'clans'
	__table_args__ = (UniqueConstraint('clan'),)

	id = Column(Integer, primary_key=True)
	clan = Column(String)

	def __repr__(self):
		return "<Clan (id='%s', clan='%s'>" % (self.id, self.clan)

class Card(Base):
	"""
	Model of cards table
	"""
	__tablename__ = 'cards'
	__table_args__ = (UniqueConstraint('name'),)

	id = Column(String(10), primary_key=True)
	name = Column(String)
	type = Column(Integer, ForeignKey('cardtypes.id'))
	set = Column(Integer, ForeignKey('sets.id'))
	force = Column(Integer)
	chi = Column(Integer)
	hr = Column(Integer)
	gc = Column(Integer)
	ph = Column(Integer)
	cardtext = Column(String)
	image = Column(String)
	artist = Column(String)

	keywords = relationship('Keyword', secondary=card_keywords, backref=backref('cards', lazy='dynamic'))
	clans = relationship('Clan', secondary=card_clans, backref=backref('cards', lazy='dynamic'))

	def __repr__(self):
		return "<Card (name='%s')>" % self.name

class ProxyDB():
	"""
	Controller for proxy database
	"""
	engine = None
	session = None

	def __init__(self):
		#Open connection to database
		proxy_database = os.path.join(locationsettings.data_dir, 'proxy.db')
		self.engine = create_engine('sqlite:///' + proxy_database)
		disk_metadata = MetaData(bind=self.engine, reflect=True)
		if len(disk_metadata.tables) == 0:
			print "No tables defined, creating initial database."
			Base.metadata.create_all(self.engine)
		self.session = sessionmaker(bind=self.engine)

		#Debug; verify foreign_keys
		foreign_keys = self.engine.execute('PRAGMA foreign_keys').fetchone()
		if foreign_keys[0] == 0:
			print "FOREIGN KEYS are OFF"
		elif foreign_keys[0] == 1:
			print "FOREIGN KEYS are ON"

	#Ensure that we're correctly using foreign keys.
	@event.listens_for(Engine, "connect")
	def set_sqlite_pragma(dbapi_connection, connection_record):
		cursor = dbapi_connection.cursor()
		cursor.execute("PRAGMA foreign_keys=ON")
		cursor.close()

	"""
	CardType Functions
	"""
	def add_card_type(self, name):
		session = self.session()
		try:
			new_cardtype = CardType(type = name)
			session.add(new_cardtype)
			session.commit()
		except IntegrityError:
			print 'CardType already exists with type=' + name
		
		session.close()

	def remove_card_type(self, cardtype):
		session = self.session()
		session.delete(cardtype)
		session.commit()
		session.close()

	def get_card_type(self, id):
		session = self.session()
		card_type = session.query(CardType).filter(CardType.id == id).first()
		session.close()
		return card_type

	def get_all_card_types(self):
		session = self.session()
		card_types = session.query(CardType).all()
		session.close()
		return card_types

	"""
	Set Functions
	"""
	def add_set(self, name, abbv):
		session = self.session()
		try:
			new_set = Set(name = name, abbreviation=abbv)
			session.add(new_set)
			session.commit()
		except IntegrityError:
			print 'Set already exists with name=' + name
		session.close()

	def remove_set(self, set):
		session = self.session()
		session.delete(set)
		session.commit
		session.close()

	def get_set(self, id):
		session = self.session()
		set = session.query(Set).filter(Set.id == id).first()
		session.close()
		return set

	def get_all_sets(self):
		session = self.session()
		sets = session.query(Set).all()
		session.close()
		return sets

	"""
	Clan Functions
	"""
	def add_clan(self, name):
		session = self.session()
		try:
			new_clan = Clan(clan = name)
			session.add(new_clan)
			session.commit()
		except IntegrityError:
			print 'Clan already exists with clan=' + name
		session.close()

	def remove_clan(self, clan):
		session = self.session()
		session.delete(clan)
		session.commit()
		session.close()

	def get_clan(self, id):
		session = self.session()
		set = session.query(Clan).filter(Clan.id == id).first()
		session.close()
		return set

	def get_all_clans(self):
		session = self.session()
		sets = session.query(Clan).all()
		session.close()
		return sets

	"""
	Card Functions
	"""
	def add_card(self, card = None, name=None, type=None, set=None, clan=None, force=None, chi=None, hr=None, gc=None, ph=None, text=None, artist=None):
		session = self.session()
		if card != None:
			try:
				session.add(card)
				session.commit()
			except IntegrityError:
				print "Card alread exists with name=" + card.name
		session.close()


	def remove_card(self, card):
		session = self.session()
		session.delete(card)
		session.commit()
		session.close()

	def get_card(self, id):
		session = self.session()
		card = session.query(Card).filter(Card.id == id).first()
		session.close()
		return card

	def get_cards_by_filter(self, name=None, type=None, set=None, clan=None, force=None, chi=None, hr=None, gc=None, ph=None, text=None, limit=None):
		session = self.session()
		filter_query = 'session.query(Card)'
		if name != None:
			filter_query = filter_query + '.filter(Card.name.like(\'%\'+name+\'%\'))'
		if type != None:
			filter_query = filter_query + '.filter(Card.type==type)'
		if set != None:
			filter_query = filter_query + '.filter(Card.set==set)'
		if clan != None:
			filter_query = filter_query + '.filter(Card.clan==clan)'
		if force != None:
			filter_query = filter_query + '.filter(Card.force==force)'
		if chi != None:
			filter_query = filter_query + '.filter(Card.chi==chi)'
		if hr != None:
			filter_query = filter_query + '.filter(Card.hr==hr)'
		if gc != None:
			filter_query = filter_query + '.filter(Card.gc==gc)'
		if ph != None:
			filter_query = filter_query + '.filter(Card.ph==ph)'
		if text != None:
			filter_query = filter_query + '.filter(Card.cardtext.like(\'%\'+text+\'%\'))'
		if limit != None:
			filter_query = filter_query + '.limit(limit)'
		filter_query = filter_query + '.all()'
		cards = eval(filter_query)
		session.close()
		return cards


#Use for testing
if __name__ == "__main__":
	proxydb = ProxyDB()
	"""
	Create data
	""
	proxydb.add_card_type("Personality")
	proxydb.add_card_type("Follower")
	proxydb.add_set("Aftermath", "AM")
	proxydb.add_set("Gates of Chaos", "GoC")
	proxydb.add_set("Ivory Edition", "Ivory")
	proxydb.add_clan("Crab")
	proxydb.add_clan("Crane")
	proxydb.add_clan("Dragon")
	proxydb.add_clan("Lion")
	#"""
	#card_types = proxydb.get_all_card_types()
	print proxydb.get_card_type(1)
	print proxydb.get_card_type(2)
	print proxydb.get_card_type(3)
	sets = proxydb.get_all_sets()
	#print sets
	print proxydb.get_set(1)
	print proxydb.get_set(2)
	print proxydb.get_set(3)
	clans = proxydb.get_all_clans()
	print clans
	print proxydb.get_clan(1)
	print proxydb.get_clan(3)
	print proxydb.get_clan(5)
	#Cards
	#new_card = Card(id="Ivory005", name="Ashalan", force=4, chi=4, hr=-1, gc=0, ph=0, type=1, set=3, cardtext="![CDATA[<b>Shugenja &#8226;</b> Ashalan &#8226; Nonhuman &#8226; <br>(This is a proxy for a created card. It is not considered to have a title and cannot be included in decks.)]]")
	#proxydb.add_card(card=new_card)
	card = proxydb.get_card(id="Ivory005")
	#print card
	for qcard in proxydb.get_cards_by_filter(name="Ash", limit=1):
		print qcard

	