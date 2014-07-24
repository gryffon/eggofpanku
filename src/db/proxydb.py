# Egg of P'an Ku -- an unofficial client for Legend of the Five Rings
# Copyright (C) 2008  Peter C O Johansson
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
	Proxy database module for Egg of P'an Ku.

author: Ryan Karetas
file: proxydb.py
date: 21 Jul 2014
"""

import sqlite3
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


class ProxyDB():
	conn = None

	def __init__(self):
		#Open connection to database
		self.conn = sqlite3.connect(os.path.join(locationsettings.data_dir, 'proxy.db'))
		self.init_db()

	def init_db(self):
		with self.conn:
			cur = self.conn.cursor()
			cur.execute("PRAGMA foreign_keys = ON")

			#Debug
			cur.execute("PRAGMA foreign_keys")
			cur.execute('''CREATE TABLE IF NOT EXISTS CardType 
							(Id Integer PRIMARY KEY,
							 Type TEXT UNIQUE)
						''')

			cur.execute('''CREATE TABLE IF NOT EXISTS ProxyCard 
							(Id TEXT PRIMARY KEY,
							 Name TEXT UNIQUE,
							 Type Integer,
							 Force Integer DEFAULT 0,
							 Chi Integer DEFAULT 0, 
							 HR Integer DEFAULT 0,
							 GC Integer DEFAULT 0,
							 PH Integer DEFAULT 0,
							 CardText Text,
							 Image Text,
							 FOREIGN KEY(Type) REFERENCES CardType(Id))
						''')

	def num_tables(self):
		with self.conn:
			cur = self.conn.cursor()
			cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")

			numTables = cur.fetchone()[0]
			print numTables

	def reset_db(self):
		with self.conn:
			self.conn.execute("DROP TABLE ProxyCard")

	def add_card_type(self, type):
		with self.conn:
			try:
				cur = self.conn.cursor()
				cur.execute("INSERT INTO CardType VALUES (NULL, ?)", (type,))
			except sqlite3.IntegrityError:
				print "Card Type already exists."

	def get_card_types(self):
		with self.conn:
			cur = self.conn.cursor()
			cur.execute("SELECT * from CardType")

			rows = cur.fetchall()

			return rows

	def add_card(self, carddata):
		md5 = hashlib.md5()
		md5.update(carddata['Name'])
		IdHash = md5.hexdigest()
		with self.conn:
			try:
				cur = self.conn.cursor()
				cur.execute("INSERT INTO ProxyCard VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
							(IdHash, carddata['Name'], carddata['Type'], carddata['Force'],
								carddata['Chi'], carddata['HR'], carddata['GC'], carddata['PH'],
								carddata['CardText'], carddata['Image']))
			except sqlite3.IntegrityError:
				error = sys.exc_info()[1]
				if str(error) == "foreign key constraint failed":
					print "Card Type does not exist."
				elif str(error) == "column Name is not unique":
					print "Proxy Card with that name already exists."
				else:
					print "Unknown issue adding Proxy Card."

	def del_card(self, Id):
		with self.conn:
			cur = self.conn.cursor()
			cur.execute("DELETE FROM ProxyCard WHERE Id=?", (Id,))

	def get_card_by_id(self, Id):
		with self.conn:
			cur = self.conn.cursor()
			cur.execute("SELECT * FROM ProxyCard WHERE Id=?", (Id,))

			row = cur.fetchone()

			return row

	def get_cards_by_type(self, Type):
		with self.conn:
			cur = self.conn.cursor()
			cur.execute("SELECT * FROM ProxyCard WHERE Type=?", (Type,))

			rows = cur.fetchall()

			return rows

#Use for testing
if __name__ == "__main__":
	proxydb = ProxyDB()
	proxydb.num_tables()
#	proxydb.reset_db()

#	proxydb.add_card_type("Personality")
#	proxydb.add_card_type("Item")
	rows = proxydb.get_card_types()

	for row in rows:
		print row
'''
	newcard = {'Name': 'Fudo', 'Type': 4, 'Force': 10, 'Chi': 5, 'HR': -1, 'GC': 0, 'PH': 0,
				'CardText': 'May not be included in decks.\nCards\' effects will not bow this Personality or move him home.', 
				'Image': '' }
	proxydb.add_card(newcard)
	md5 = hashlib.md5()
	md5.update('Fudo')
	CardId = md5.hexdigest()

	cards = proxydb.get_cards_by_type(1)
	for card in cards:
		print card

	proxydb.del_card(CardId)

	cards = proxydb.get_cards_by_type(1)
	for card in cards:
		print card
'''