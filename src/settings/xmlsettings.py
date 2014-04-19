import sys
import string
import os
import xml.dom.minidom
from xml.dom.minidom import Node
from xml.dom.minidom import Document

DEFAULT_SETTINGS = {
    'gamehost':'localhost',
    'gameport':18072,
    'last_deck':'',
    'maximize':True,
    'mainwindow_size':(780,560),
    'playername':'Toku-san',
    'cardsource':'',
    'playfield_snap':True,
    'dir_imagepacks':'images/cards/',
    'imagepackdir_changed':False,
    'playfield_bg_mode':0,
    'playfield_bg_color1':(0, 206, 24),
    'playfield_bg_color2':(0, 190, 16),
    'playfield_bg_image':'',
    'playfield_bg_image_display':False,
    'attach_ok': ('personality',),
    'matchuser':'',
    'matchpassword':'1234',
    'log_multiplayer_games':False,
    'canvas_card_spacing':1,
    'use_celestial_holdings':False,
    'celestial_card_draw':False,
    }

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

settings = _XMLSettings(os.path.join(os.path.expanduser(locationsettings.data_dir), 'settings.xml'), DEFAULT_SETTINGS)