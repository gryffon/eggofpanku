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
	Diagnostic script for Egg of P'an Ku.

author: Ryan Karetas
file: diagnose.py
date: 27 Oct 2014
"""
import sys
import string
import os
import xml.dom.minidom
from xml.dom.minidom import Node
from xml.dom.minidom import Document

class Logger(object):
    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

outfile = "epok-diagnostic.log"
print "Saving output to: " + outfile
sys.stdout = Logger(outfile)

#Print out expanduser('~')
print "By default the data for Egg of P'an Ku should be located in:"
print os.path.join(os.path.expanduser('~'), 'eopk')

print "Looking at location.xml to determine what location we are using:"

DEFAULT_SETTINGS_DATA_DIR = {
    'data_dir': os.path.join(os.path.expanduser('~'), 'eopk'),
    }

class _XMLSettings:
    def __init__(self, xmlfile, defaults):
        self.__dict__['defaults'] = defaults
        self.__dict__['_filename'] = xmlfile
        self.__dict__.update(defaults)
        self.LoadSettingsFile(self._filename)
        self.ApplySettingsFile()
     
    def ApplySettingsFile(self):   
        try:
            if self.xml:
                pass
                
        except AttributeError:
            self.CreateSettingsFile()
            
        for node in self.xml.getElementsByTagName("eopk:setting"):
            self.__dict__[node.getAttribute("name")] = eval(node.firstChild.nodeValue)
            
                
    def __setattr__(self,newsetting,value):
        try:
            if self.xml:
                pass
                
        except AttributeError:
            self.CreateSettingsFile()
        
        for node in self.xml.getElementsByTagName("eopk:setting"):
            if(node.getAttribute("name") == newsetting):
                node.firstChild.nodeValue = repr(value)
                return
        
        print newsetting + " not found in settings: " + self.__dict__['_filename']
                
    def CreateSettingsFile(self):
        newsettings = Document()
        eopksettings = newsettings.createElement("eopk:settings")
        eopkSchemaLocation = newsettings.createAttributeNS("http://code.google.com/p/eopk/", "eopk:schemaLocation")
        eopkSchemaLocation.nodeValue="http://code.google.com/p/eopk/ http://www.torchdragon.com/l5r/settings.xsd" 
        eopksettings.setAttributeNode(eopkSchemaLocation)
        eopkXMLNS = newsettings.createAttributeNS("http://code.google.com/p/eopk/", "xmlns:eopk")
        eopkXMLNS.nodeValue="http://code.google.com/p/eopk/"
        eopksettings.setAttributeNode(eopkXMLNS)
        newsettings.appendChild(eopksettings)
        for k, v in self.__dict__['defaults'].items():
            eopkSetting = newsettings.createElement("eopk:setting")
            eopkSettingName = newsettings.createAttributeNS("http://code.google.com/p/eopk/", "name")
            eopkSettingName.nodeValue = k
            eopkSetting.setAttributeNode(eopkSettingName)
            eopkSettingValue = newsettings.createTextNode(repr(v))
            eopkSetting.appendChild(eopkSettingValue)
            eopksettings.appendChild(eopkSetting)
            
            
        self.__dict__['xml'] = newsettings
    
    def WriteSettingsFile(self):
        try:
            if self.xml:
                pass
                
        except AttributeError:
            self.CreateSettingsFile()
        
        #Check for new settings
        for k, v in self.__dict__['defaults'].items():
            settingfound = False

            for node in self.xml.getElementsByTagName("eopk:setting"):
                if k == node.getAttribute("name"):
                    settingfound = True
                    break

            if settingfound == False:
                print "Setting not found: " + k
                eopkSetting = self.__dict__['xml'].createElement("eopk:setting")
                eopkSettingName = self.__dict__['xml'].createAttributeNS("http://code.google.com/p/eopk/", "name")
                eopkSettingName.nodeValue = k
                eopkSetting.setAttributeNode(eopkSettingName)
                eopkSettingValue = self.__dict__['xml'].createTextNode(repr(v))
                eopkSetting.appendChild(eopkSettingValue)
                self.__dict__['xml'].childNodes[0].appendChild(eopkSetting)


        f = file(self._filename, 'w')
        self.xml.writexml(f, indent="  ", addindent="  ", newl="\n")
        f.close()
        self.ApplySettingsFile()        
    
    def LoadSettingsFile(self, xmlsettings):
        try:
            self.__dict__['xml'] = xml.dom.minidom.parse(xmlsettings)
        
        except IOError:
            print "Unable to open settings file: " + xmlsettings
            return False
        
        self.StripTextNodes(self.xml.getElementsByTagName('eopk:settings'))
    
    def StripTextNodes(self, nodeList):
        """The XML parser will keep appending \n to each text node when it outputs the text
        so we need to strip the \n characters in order to stop bloat from occurring"""
        for node in nodeList:
            if node.nodeType == node.ELEMENT_NODE:
                self.StripTextNodes(node.childNodes)
            
            if node.nodeType == node.TEXT_NODE:
                node.data = string.strip(string.strip(node.data, '\n'))

locationsettings = _XMLSettings('location.xml', DEFAULT_SETTINGS_DATA_DIR)

print "location.xml is set to use the following as the data directory:"
print DEFAULT_SETTINGS_DATA_DIR['data_dir']

print "Using default data dir?"
if (DEFAULT_SETTINGS_DATA_DIR['data_dir'] == os.path.join(os.path.expanduser('~'), 'eopk')):
	print "Default data dir: TRUE"
	print "Looking for settings.xml in the default directory:"
	if (os.path.exists(os.path.join(os.path.expanduser(os.path.join(os.path.expanduser('~'), 'eopk')), 'settings.xml'))):
		print "settings.xml : FOUND"
	else:
		print "settings.xml : NOT FOUND"
else:
	print "Default data dir: FALSE"
	print "Looking for settings.xml in the location.xml directory:"
	if ( os.path.exists(os.path.join(DEFAULT_SETTINGS_DATA_DIR['data_dir'], 'settings.xml')) ):
		print "settings.xml : FOUND"
	else:
		print "settings.xml : NOT FOUND"

foo = raw_input("Press Enter to finish")