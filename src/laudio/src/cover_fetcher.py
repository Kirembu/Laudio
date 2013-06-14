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
import urllib, urllib2
from urllib2 import URLError, HTTPError
from lxml import etree
from lxml.etree import XMLSyntaxError

# Django imports
from django.conf import settings
from django.core.urlresolvers import reverse

# Laudio imports
from laudio.player.models import UserProfile


class CoverFetcher(object):
    """
    Class for fetching covers from last.fm or harddisk
    """

    def __init__(self, song, request):
        """ Get the cover of a song

        Keyword arguments:
        song -- The django model of the song we want to get the cover from
        request -- The request object
        """
        self.artist = song.artist.name.encode('utf-8')
        self.album = song.album.name.encode('utf-8')

        # standardpath, we default to this if no cover is being found
        self.default_cover = settings.STATIC_URL + 'img/nocover.png'
        
    
    def fetch(self):
        """ Fetches the songcover from different services"""
        # get cover from last.fm        
        cover = self._lastFM()
        if cover == None:
            return self.default_cover
        else:
            return cover
        
    
    def _lastFM(self):
        """ Fetches and returns the link to the last.fm cover of the song
        """
        data = {}
        
        # The api key which is unique to LAudio
        # If you want to implement this for your app you need to register
        # your app at last.fm to tell it with which app you submit/get data
        data['api_key'] = settings.LAST_FM_API_KEY
        data['method'] = 'album.getinfo'
        data['artist'] = self.artist
        data['album'] = self.album
        url_values = urllib.urlencode(data)
        url = 'http://ws.audioscrobbler.com/2.0/'
        full_url = url + '?' + url_values
        try:
            response = urllib2.urlopen(full_url)
            elements = etree.fromstring(response.read())
            if elements.get('status') == 'ok':
                try:
                    return elements.xpath('/lfm/album/image[@size="extralarge"]/text()')[0]
                except IndexError:
                    return None
            else:
                return None

        except (URLError, HTTPError, UnicodeEncodeError, XMLSyntaxError):
            return None
