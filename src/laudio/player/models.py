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
import hashlib

# Django imports
from django.conf import settings 
from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

# Laudio imports
from laudio.src.inc.config import LaudioConfig


config = LaudioConfig(settings.LAUDIO_CFG)


class Artist(models.Model):
    name = models.CharField(_('Artist'), max_length=150, unique=True)
    modified = models.DateTimeField(_('Modified'), auto_now=True)

    def __unicode__(self):
        return self.name


class Album(models.Model):
    name = models.CharField(_('Album'), max_length=150)
    date = models.CharField(_('Year'), max_length=100);
    modified = models.DateTimeField(_('Modified'), auto_now=True)

    def __unicode__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(_('Genre'), max_length=150, unique=True)
    modified = models.DateTimeField(_('Modified'), auto_now=True)

    def __unicode__(self):
        return self.name


class Song(models.Model):
    title = models.CharField(_('Title'), max_length=250)
    album = models.ForeignKey('Album')
    genre = models.ForeignKey('Genre')
    artist = models.ForeignKey('Artist')
    codec = models.CharField(_('Codec'), max_length=10)
    tracknumber = models.IntegerField(_('Tracknumber'))
    path = models.FilePathField(_('Path'), max_length=255)
    lastmodified = models.DateTimeField(_('Last metadata change'))
    added =  models.DateTimeField(_('Added'), auto_now_add=True)
    length = models.IntegerField(_('Length'))
    bitrate = models.CharField(_('Bitrate'), max_length=100);
    size = models.IntegerField(_('Size'));
    modified = models.DateTimeField(_('Modified'), auto_now=True)

    def __unicode__(self):
        return self.title
        
    def rel_path(self):
        """Returns the relative path of the song
        """
        return self.path.replace(config.collectionPath, '', 1)


class Playlist(models.Model):
    name = models.CharField(_('Playlist'), max_length=250)
    added = models.IntegerField(_('Added'))
    songs = models.ManyToManyField(Song, through='PlaylistEntry')
    user = models.ForeignKey(User)
    modified = models.DateTimeField(_('Modified'), auto_now=True)

    def __unicode__(self):
        return self.name


class PlaylistEntry(models.Model):
    playlist = models.ForeignKey(Playlist)
    song = models.ForeignKey(Song)
    modified = models.DateTimeField(_('Modified'), auto_now=True)


class XMLAPIUser(models.Model):
    username = models.CharField(_('Username'), max_length=250, unique=True)
    password = models.CharField(_('Password'), max_length=64, blank=True)
    token = models.CharField(_('Token'), max_length=64)
    last_handshake = models.DateTimeField(_('Last handshake'), auto_now_add=True)
    modified = models.DateTimeField(_('Modified'), auto_now=True)
    is_active = models.BooleanField(_('Is active'), help_text=_('Set to true if \
            you want the user to be able to access the XML API'), blank=True,
            default=True)

    def set_password(self, password):
        self.password = hashlib.sha256(password)


# get themes in the themes directory
THEMES = []
themes_dir = os.path.join(settings.MEDIA_ROOT, 'themes/')
for theme in os.listdir( themes_dir ):
    path = os.path.join(themes_dir, theme)
    if os.path.isdir(path):
        THEMES.append(
            (theme, theme)
            )
# activate streaming compression
STREAM_QUALITY = (
    (1, '64 kbit/s'),
    (2, '128 kbit/s'),
    (3, '256 kbit/s'),
)

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    modified = models.DateTimeField(_('Modified'), auto_now=True)
    lastFMName = models.CharField(_('last.fm username'), max_length=100, blank=True)
    lastFMPass = models.CharField(_('last.fm password'), max_length=100, blank=True)
    lastFMSubmit = models.BooleanField(_('Scrobble last.fm'), 
        help_text=_('Activate this if you want to submit your played tracks \
                    to your last.fm account'), blank=True)
    libreFMName = models.CharField(_('libre.fm username'), max_length=100, blank=True)
    libreFMPass = models.CharField(_('libre.fm password'), max_length=100, blank=True)
    libreFMSubmit = models.BooleanField(_('Scrobble libre.fm'),
        help_text=_('Activate this if you want to submit your played tracks \
                    to your libre.fm account'), blank=True)
    showLib = models.BooleanField(_('Show all songs on startup'), 
                help_text=_('This displays your whole collection automatically on startup. \
                            Be carefull with bigger collections as it may impact your \
                            browser\'s speed'), blank=True)
    hidePlaylist = models.BooleanField(_('Hide playlist by default'), help_text=_('Automatically \
                    hides the playlist in the Collection view so you have \
                    to click playlist to view it'), blank=True)
    hideSidebar = models.BooleanField(_('Hide sidebar by default'), help_text=_('Automatically \
                    hides the sidebar in the Collection view so you have \
                    to click sidebar to view it'), blank=True)
    theme = models.CharField(_('l-audio theme'), max_length=100, choices=THEMES, 
        help_text=_('Choose a custom theme'), blank=True)
    stream_transcoding = models.BooleanField(_('Enable stream transcoding'),
        help_text=_('Activate this if you have a slow internet connection \
                    and want l-audio to deliver a lower bandwidth stream'), blank=True)
    stream_quality = models.CharField(_('Stream quality'), max_length=100, choices=STREAM_QUALITY, 
        help_text=_('The quality which we will transcode the song to'), blank=True)
