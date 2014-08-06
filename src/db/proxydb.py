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
from sqlalchemy import Column, Integer, String, Table
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import hashlib
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

class CardType(Base):
	"""
	Model of cardtypes table
	"""
	__tablename__ = 'cardtypes'

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

	id = Column(Integer, primary_key=True)
	name = Column(String)
	abbreviation = Column(String(5))

	cards = relationship("Card")

	def __repr__(self):
		return "<Set (id='%s', name='%s'>" % (self.id, self.name)

class Keyword(Base):
	"""
	Model of keywords table
	"""
	__tablename = 'keywords'

	id = Column(Integer, primary_key=True)
	keyword = Column(String)

	def __repr__(self):
		return "<Keyword (id='%s', keyword='%s'>" % (self.id, self.keyword)

class Card(Base):
	"""
	Model of cards table
	"""
	__tablename__ = 'cards'

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

	keywords = relationship('Keyword', secondary=card_keywords, backref=backref'cards', lazy='dynamic'))

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
		self.session = sessionmaker(bind=engine)

	def add_card_type(self, name):
		session = self.session()
		new_cardtype = CardType(name = name)
		session.add(new_cardtype)
		session.commit()
		session.close()

	def remove_card_type(self):
		#Placeholder
		session = self.session()

	def get_card_type(self, id):
		session = self.session()
		card_type = session.query.filter(CardType.id == id).first()
		session.commit()
		session.close()
		return card_type

	def get_all_card_types(self):
		session = self.session()
		card_types = session.query(CardType).all()
		session.close()
		return card_types

	def add_set(self):
		session = self.session()
		new_set = Set(name = name)
		session.add(new_set)
		session.commit()
		session.close()

	def remove_set(self):
		#Placeholder
		session = self.session()

	def get_set(self, id):
		session = self.session()
		set = session.query.filter(Set.id == id).first()
		session.commit()
		session.close()
		return set

	def get_all_sets(self):
		#Placeholder
		session = self.session()

	def add_card(self):
		#Placeholder
		session = self.session()

	def remove_card(self):
		#Placeholder
		session = self.session()

	def get_card(self):
		session = self.session()
		card = session.query.filter(Card.id == id).first()
		session.commit()
		session.close()
		return card

	def get_cards_by_filter(self):
		#Placeholder
		session = self.session()

#Use for testing
if __name__ == "__main__":
	proxydb = ProxyDB()
