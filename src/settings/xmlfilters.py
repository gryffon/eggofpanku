'''
Created on May 26, 2009

@author: TorchDragon
'''

import xml.parsers.expat
import os
from settings.xmlsettings import settings
from settings.xmlsettings import locationsettings

class FilterData:
    '''
    The FilterData class is the definition of the filter
    properties.
    '''
    def __init__(self):
        self.type = None
        self.name = None
        self.default = False
        self.displayName = None
        self.deckType = None
        self.hasCost = None
        self.name = []
        self.legal = []

class FilterReader:
    '''
    The FilterReader class does the heavy lifting for moving
    the xml data into python objects

    Because of the initialization structure, you can simply
    assign a variable to the FilterReader().Filters property
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.Filters = {}
        self.current = None
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.parseStartElem
        self.parser.EndElementHandler = self.parseEndElem
        self.parser.CharacterDataHandler = self.parseCData
        __dir__ = os.path.dirname(os.path.abspath(__file__))
        #filepath = os.path.join(__dir__, 'filters.xml')
        filepath = os.path.join(locationsettings.data_dir, 'filters.xml')
        self.parser.ParseFile(open(filepath, 'rb'))

    def parseStartElem(self, name, attrs):
        if name == "filter":
            self.current = FilterData()
        self.cdata = ""

    def parseEndElem(self, name):
        if name == "type":
            self.current.type = self.cdata
        elif name == "deckType":
            self.current.deckType = self.cdata
        elif name == "hasCost":
            self.current.hasCost = self.cdata
        elif name == "name":
            self.current.name.append(self.cdata)
        elif name == "default":
            self.current.default = self.cdata
        elif name == "displayName":
            self.current.displayName = self.cdata
        elif name == "legal":
            self.current.legal.append(self.cdata)
        elif name == "filter":
            if not self.Filters.has_key(self.current.type):
                self.Filters[self.current.type] = []
            self.Filters[self.current.type].append(self.current)
            self.current = None

    def parseCData(self, data):
        self.cdata += data