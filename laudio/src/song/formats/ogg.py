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

import os
from time import time
from mutagen.oggvorbis import OggVorbis
from laudio.src.song.song import Song

class OGGSong (Song):

    def __init__(self, path):
        """ Read metainformation from an ogg file
        The multiple KeyErrors check if tags are not Null
        Keyword arguments:
        path -- the full path to the song
        """
        super(OGGSong, self).__init__(path)
        self.codec = "ogg"
        self.song = OggVorbis(self.path)
        for key in ('title', 'artist', 'album', 'genre', 'date'):
            attr = self.song.get(key, ('',))[0]
            setattr(self, key, attr.encode("utf-8") )
        self.bitrate = int(self.song.info.bitrate) / 1000
        self.length = int(self.song.info.length)
        if self.title == "":
            self.title = os.path.basename(self.path)
        # set date
        self.setDatetime()
        # check for empty track number
        try:
            self.tracknumber = int(self.song['tracknumber'][0])
        except (ValueError, KeyError):
            self.tracknumber = 0
