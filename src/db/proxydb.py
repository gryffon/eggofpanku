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
from sqlalchemy import Column, Integer, String
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

	cards = relationship("Card")

	def __repr__(self):
		return "<Set (id='%s', name='%s'>" % (self.id, self.name)

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
		self.engine = create_engine('sqlite:///proxy.db')
		self.session = sessionmaker(bind=engine)



#Use for testing
if __name__ == "__main__":
	proxydb = ProxyDB()
