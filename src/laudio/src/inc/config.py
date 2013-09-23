#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
Laudio - A webbased musicplayer

Copyright (C) 2010 Bernhard Posselt, bernhard.posselt@gmx.at

Laudio is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

Laudio is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Laudio.  If not, see <http://www.gnu.org/licenses/>.

"""

# System imports
import os
import ConfigParser
import re
import codecs

# Django imports
from django.conf import settings


class LaudioConfig(object):
    """
    Interface for writing to the config file
    """
    
    
    def __init__(self, configs):
        """Constructor
    
        Keyword arguments:
        configs -- A dict with config filepaths
        """
        self.mainConfig = configs['MAIN_CFG']
        self.apacheConfig = configs['APACHE_CFG']
    
        # set default values
        self.parserError = False
        # music settings
        self.collectionPath = '/home/user/music/'
        self.collectionStartup = False
        self.requireLogin = False
        self.debug = False
        # xml token lifespan in seconds
        self.tokenLifespan = 60*60*24
        self.xmlAuth = False
        self.transcoding = False
        
        # read in main config
        try:
            config = ConfigParser.SafeConfigParser(allow_no_value=True)
            with codecs.open(self.mainConfig, 'r', encoding='utf-8') as f:
                config.readfp(f)
                
            # music settings
            try:
                self.collectionPath = config.get('settings', 'collection_path').encode('utf-8')
                if not self.collectionPath.endswith('/'):
                    self.collectionPath += '/'
            except ConfigParser.NoOptionError:
                self.parserError = True
                
            try:
                self.collectionStartup = config.getboolean('settings', 'collection_startup')
            except ConfigParser.NoOptionError:
                self.parserError = True
                
            try:
                self.transcoding = config.getboolean('settings', 'transcoding')
            except ConfigParser.NoOptionError:
                self.parserError = True
                
            try:
                self.requireLogin = config.getboolean('settings', 'require_login')
            except ConfigParser.NoOptionError:
                self.parserError = True
                
            try:
                self.debug = config.getboolean('settings', 'debug')
            except ConfigParser.NoOptionError:
                self.parserError = True
                
            try:
                self.tokenLifespan = config.getint('settings', 'token_lifespan')
            except ConfigParser.NoOptionError:
                self.parserError = True        

            try:
                self.xmlAuth = config.getboolean('settings', 'xml_auth')
            except ConfigParser.NoOptionError:
                self.parserError = True   

        # if there was something wrong with the config or parsing, write default
        # values
        except ConfigParser.NoSectionError:
            self.save()
        if self.parserError:
            self.save()
        
        # now try to read in the server config
        try:
            with open(self.apacheConfig, 'r') as confFile:
                conf = confFile.read()
                regex = r'WSGIScriptAlias (.*) .*wsgi/django.wsgi'
                # FIXME: This could return None
                ## url = re.search(regex, conf).group(1)
                url = 'audio.patrick.co.ke/'
                
                if url.endswith('/'):
                    url = url[:-1]
                self.url = url
        except IOError:
            # FIXME: log error
            pass

    def save(self):
        """Writes the current values into the configfile
        """
        config = ConfigParser.SafeConfigParser()
        config.add_section('settings')
        # music settings
        config.set('settings', 'collection_path', str(self.collectionPath).encode('utf-8'))
        config.set('settings', 'collection_startup', str(self.collectionStartup))
        config.set('settings', 'require_login', str(self.requireLogin))
        config.set('settings', 'debug', str(self.debug))
        config.set('settings', 'token_lifespan', str(self.tokenLifespan))
        config.set('settings', 'xml_auth', str(self.xmlAuth))
        config.set('settings', 'transcoding', str(self.transcoding))
        with open(self.mainConfig, 'wb') as confFile:
            config.write(confFile)


    def symlink_collection(self, path):
        """add symlink to music directory
        keyword arguments
        path -- the path to the music directory
        """
        source = self.collectionPath
        linkName = os.path.join(settings.STATIC_ROOT, 'audio')
        if os.path.exists(linkName):
            os.unlink(linkName)
        if self.collectionPath != '' and os.path.exists(source):
            os.symlink(source, linkName)
