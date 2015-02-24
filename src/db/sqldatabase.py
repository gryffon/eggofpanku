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
	SQL based database module for Egg of P'an Ku.
author: Ryan Karetas
file: proxydb.py
date: 24 Feb 2015
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Table, MetaData, UniqueConstraint
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

#Database Controller
class EopkDB():
	"""
	Controller for Egg of P'an Ku database
	"""
	engine = None
	session = None

	def __init__(self):
		#Open connection to database
		egg_database = os.path.join(locationsettings.data_dir, 'eopk.db')
		self.engine = create_engine('sqlite:///' + egg_database)
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
	def add_card_type(self, name, displayname):
		session = self.session()
		try:
			new_cardtype = CardType(type = name, display_name = displayname)
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

	def get_card_type_by_name(self, name):
		session = self.session()
		card_type = session.query(CardType).filter(CardType.type == name).first()
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
	def add_set(self, abbv, displayname):
		session = self.session()
		try:
			new_set = Set(name = abbv, display_name = displayname)
			session.add(new_set)
			session.commit()
		except IntegrityError:
			print 'Set already exists with name=' + abbv
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
	
	def get_set_by_display_name(self, name):
		session = self.session()
		set = session.query(Set).filter(Set.display_name == name).first()
		session.close()
		return set

	def get_set_by_abbv(self, abbv):
		session = self.session()
		set = session.query(Set).filter(Set.name == abbv).first()
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
	def add_clan(self, name, displayname):
		session = self.session()
		try:
			new_clan = Faction(faction = name, display_name = displayname)
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

	def get_clan_by_name(self, name):
		session = self.session()
		set = session.query(Clan).filter(Clan.clan == name).first()
		session.close()
		return set

	def get_all_clans(self):
		session = self.session()
		sets = session.query(Clan).all()
		session.close()
		return sets


#Filter Models
class CardType(Base):
	"""
	Model of cardtypes table
	"""
	__tablename__ = 'cardtypes'
	__table_args__ = (UniqueConstraint('type'),)

	id = Column(Integer, primary_key=True)
	type = Column(String)
	display_name = Column(String)
	deck_type = Column(String)
	has_cost = Column(Boolean)

	def __repr__(self):
		return "<CardType (id='%s', type='%s'>" % (self.id, self.type)

class Faction(Base):
	"""
	Model of factions table
	"""
	__tablename__ = 'factions'
	__table_args__ = (UniqueConstraint('faction'),)

	id = Column(Integer, primary_key=True)
	faction = Column(String)
	display_name = Column(String)

	def __repr__(self):
		return "<Faction (id='%s', faction='%s'>" % (self.id, self.faction)

class MinorClan(Base):
	"""
	Model of minor_clans table
	"""
	__tablename__ = 'minor_clans'
	__table_args__ = (UniqueConstraint('minor_clan'),)

	id = Column(Integer, primary_key=True)
	minor_clan = Column(String)
	display_name = Column(String)

	def __repr__(self):
		return "<MinorClan (id='%s', minor_clan='%s'>" % (self.id, self.minor_clan)

class Rarity(Base):
	"""
	Model of rarities table
	"""
	__tablename__ = 'rarities'
	__table_args__ = (UniqueConstraint('rarity'),)

	id = Column(Integer, primary_key=True)
	rarity = Column(String)
	display_name = Column(String)

	def __repr__(self):
		return "<Rarity (id='%s', rarity='%s'>" % (self.id, self.rarity)

class Set(Base):
	"""
	Model of sets table
	"""
	__tablename__ = 'sets'
	__table_args__ = (UniqueConstraint('set'),)

	id = Column(Integer, primary_key=True)
	set = Column(String)
	display_name = Column(String)

	def __repr__(self):
		return "<Set (id='%s', set='%s'>" % (self.id, self.set)

class Legality(Base):
	"""
	Model of legalities table
	"""
	__tablename__ = 'legalitiess'
	__table_args__ = (UniqueConstraint('legality'),)

	id = Column(Integer, primary_key=True)
	legality = Column(String)
	display_name = Column(String)
	included_sets = Column(String)
	excluded_sets = Column(String)

	def __repr__(self):
		return "<Legality (id='%s', legality='%s'>" % (self.id, self.legality)




#Use for testing
if __name__ == "__main__":
	print "Testing"