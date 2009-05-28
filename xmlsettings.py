import sys
import string
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
    'playfield_bg_mode':0,
    'playfield_bg_color1':(0, 206, 24),
    'playfield_bg_color2':(0, 190, 16),
    'playfield_bg_image':'',
    'playfield_bg_image_display':False,
    'attach_ok': ('personalities',),
    'matchuser':'',
    'matchpassword':'1234',
    'log_multiplayer_games':False,
    'canvas_card_spacing':3,
}

class _XMLSettings:
    def __init__(self, xmlfile):
        self.__dict__['_filename'] = xmlfile
        self.__dict__.update(DEFAULT_SETTINGS)
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
        
        print newsetting + " not found in settings "
                
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
        for k, v in DEFAULT_SETTINGS.items():
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
        
        f = file(settings._filename, 'w')
        self.xml.writexml(f, indent="  ", addindent="  ", newl="\n")
        f.close()
        self.ApplySettingsFile()        
    
    def LoadSettingsFile(self, xmlsettings):
        try:
            self.__dict__['xml'] = xml.dom.minidom.parse(xmlsettings)
        
        except IOError:
            print "Unable to open settings file."
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
                
settings = _XMLSettings('settings.xml')