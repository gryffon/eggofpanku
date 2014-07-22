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
"""
	Proxy database module for Egg of P'an Ku.

author: Ryan Karetas
file: proxydb.py
date: 21 Jul 2014
"""

import sqlite3
import hashlib

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
		self.initDB()

	def initDB(self):
		with self.conn:
			cur = self.conn.cursor()
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

	def numTables(self):
		with self.conn:
			cur = self.conn.cursor()
			cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")

			numTables = cur.fetchone()[0]
			print numTables

	def resetDB(self):
		with self.conn:
			self.conn.execute("DROP TABLE ProxyCard")

	def addCardType(self, type):
		with self.conn:
			try:
				cur = self.conn.cursor()
				cur.execute("INSERT INTO CardType VALUES (NULL, ?)", (type,))
			except sqlite3.IntegrityError:
				print "Card Type already exists."

	def getCardTypes(self):
		with self.conn:
			cur = self.conn.cursor()
			cur.execute("SELECT * from CardType")

			rows = cur.fetchall()

			return rows

	def addCard(self, carddata):
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
				print "Card with that name already exists."

	def getCard(self, Id):
		with self.conn:
			cur = self.conn.cursor()
			cur.execute("SELECT * FROM ProxyCard WHERE Id=?", (Id,))

			row = cur.fetchone()

			return row

#Use for testing
if __name__ == "__main__":
	proxydb = ProxyDB()
	proxydb.numTables()

	proxydb.addCardType("Personality")
	proxydb.addCardType("Item")
#	rows = proxydb.getCardTypes()

#	for row in rows:
#		print row

	newcard = {'Name': 'Fudo', 'Type': 1, 'Force': 10, 'Chi': 5, 'HR': -1, 'GC': 0, 'PH': 0,
				'CardText': 'May not be included in decks.\nCards\' effects will not bow this Personality or move him home.', 
				'Image': '' }
	proxydb.addCard(newcard)
	md5 = hashlib.md5()
	md5.update('Fudo')
	CardId = md5.hexdigest()

	card = proxydb.getCard(CardId)
	print card