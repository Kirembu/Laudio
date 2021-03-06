#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
A pure-python library to assist sending data to AudioScrobbler (the LastFM
backend)

Copyright: 2011 Michel Albert <exhuma@users.sourceforge.net>

This package is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public    
License as published by the Free Software Foundation; either
version 2 of the License, or (at your option) any later version.

This package is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this package; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

On Debian systems, the complete text of the GNU Lesser General
Public License can be found in `/usr/share/common-licenses/LGPL'.

"""
import urllib, urllib2
from time import mktime
from datetime import datetime, timedelta
from hashlib import md5

SESSION_ID = None
POST_URL   = None
NOW_URL    = None
HARD_FAILS = 0
LAST_HS    = None   # Last handshake time
HS_DELAY   = 0      # wait this many seconds until next handshake
SUBMIT_CACHE = []
MAX_CACHE  = 5      # keep only this many songs in the cache
PROTOCOL_VERSION = '1.2'

class BackendError(Exception):
   "Raised if the AS backend does something funny"
   pass
class AuthError(Exception):
   "Raised on authencitation errors"
   pass
class PostError(Exception):
   "Raised if something goes wrong when posting data to AS"
   pass
class SessionError(Exception):
   "Raised when problems with the session exist"
   pass
class ProtocolError(Exception):
   "Raised on general Protocol errors"
   pass

def login( user, password, client=('tst', '1.0'), service="lastfm" ):
   """Authencitate with AS (The Handshake)

   @param user:     The username
   @param password: The password
   @param client:   Client information (see http://www.audioscrobbler.net/development/protocol/ for more info)
   @type  client:   Tuple: (client-id, client-version)"""
   global LAST_HS, SESSION_ID, POST_URL, NOW_URL, HARD_FAILS, HS_DELAY, PROTOCOL_VERSION

   if LAST_HS is not None:
      next_allowed_hs = LAST_HS + timedelta(seconds=HS_DELAY)
      if datetime.now() < next_allowed_hs:
         delta = next_allowed_hs - datetime.now()
         raise ProtocolError("""Please wait another %d seconds until next handshake
(login) attempt.""" % delta.seconds)

   LAST_HS = datetime.now()

   tstamp = int(mktime(datetime.now().timetuple()))
   if service == "lastfm":
      url = "http://post.audioscrobbler.com/"
   elif service == "librefm":
      url = "http://turtle.libre.fm/"
   pwhash = md5(password).hexdigest()
   token  = md5( "%s%d" % (pwhash, int(tstamp))).hexdigest()
   values = {
         'hs': 'true',
         'p' : PROTOCOL_VERSION,
         'c': client[0],
         'v': client[1],
         'u': user,
         't': tstamp,
         'a': token
         }
   data = urllib.urlencode(values)
   req = urllib2.Request("%s?%s" % (url, data) )
   response = urllib2.urlopen(req)
   result = response.read()
   lines = result.split('\n')


   if lines[0] == 'BADAUTH':
      raise AuthError('Bad username/password')

   elif lines[0] == 'BANNED':
      raise Exception('''This client-version was banned by Audioscrobbler. Please
contact the author of this module!''')

   elif lines[0] == 'BADTIME':
      raise ValueError('''Your system time is out of sync with Audioscrobbler.
Consider using an NTP-client to keep you system time in sync.''')

   elif lines[0].startswith('FAILED'):
      handle_hard_error()
      raise BackendError("Authencitation with AS failed. Reason: %s" %
            lines[0])

   elif lines[0] == 'OK':
      # wooooooohooooooo. We made it!
      SESSION_ID = lines[1]
      NOW_URL    = lines[2]
      POST_URL   = lines[3]
      HARD_FAILS = 0

   else:
      # some hard error
      handle_hard_error()

def handle_hard_error():
   "Handles hard errors."
   global SESSION_ID, HARD_FAILS, HS_DELAY

   if HS_DELAY == 0:
      HS_DELAY = 60
   elif HS_DELAY < 120*60:
      HS_DELAY *= 2
   if HS_DELAY > 120*60:
      HS_DELAY = 120*60

   HARD_FAILS += 1
   if HARD_FAILS == 3:
      SESSION_ID = None

def now_playing( artist, track, album="", length="", trackno="", mbid="" ):
   """Tells audioscrobbler what is currently running in your player. This won't
   affect the user-profile on last.fm. To do submissions, use the "submit"
   method

   @param artist:  The artist name
   @param track:   The track name
   @param album:   The album name
   @param length:  The song length in seconds
   @param trackno: The track number
   @param mbid:    The MusicBrainz Track ID
   @return: True on success, False on failure"""

   global SESSION_ID, NOW_URL

   if SESSION_ID is None:
      raise AuthError("Please 'login()' first. (No session available)")

   if POST_URL is None:
      raise PostError("Unable to post data. Post URL was empty!")

   if length != "" and type(length) != type(1):
      raise TypeError("length should be of type int")

   if trackno != "" and type(trackno) != type(1):
      raise TypeError("trackno should be of type int")

   values = {'s': SESSION_ID,
             'a': unicode(artist).encode('utf-8'),
             't': unicode(track).encode('utf-8'),
             'b': unicode(album).encode('utf-8'),
             'l': length,
             'n': trackno,
             'm': mbid }

   data = urllib.urlencode(values)
   req = urllib2.Request(NOW_URL, data)
   response = urllib2.urlopen(req)
   result = response.read()

   if result.strip() == "OK":
      return True
   elif result.strip() == "BADSESSION" :
      raise SessionError('Invalid session')
   else:
      return False

def submit(artist, track, time, source='P', rating="", length="", album="",
      trackno="", mbid="", autoflush=False):
   """Append a song to the submission cache. Use 'flush()' to send the cache to
   AS. You can also set "autoflush" to True.

   From the Audioscrobbler protocol docs:
   ---------------------------------------------------------------------------

   The client should monitor the user's interaction with the music playing
   service to whatever extent the service allows. In order to qualify for
   submission all of the following criteria must be met:

   1. The track must be submitted once it has finished playing. Whether it has
      finished playing naturally or has been manually stopped by the user is
      irrelevant.
   2. The track must have been played for a duration of at least 240 seconds or
      half the track's total length, whichever comes first. Skipping or pausing
      the track is irrelevant as long as the appropriate amount has been played.
   3. The total playback time for the track must be more than 30 seconds. Do
      not submit tracks shorter than this.
   4. Unless the client has been specially configured, it should not attempt to
      interpret filename information to obtain metadata instead of tags (ID3,
      etc).

   @param artist: Artist name
   @param track:  Track name
   @param time:   Time the track *started* playing in the UTC timezone (see
                  datetime.utcnow()).

                  Example: int(time.mktime(datetime.utcnow()))
   @param source: Source of the track. One of:
                  'P': Chosen by the user
                  'R': Non-personalised broadcast (e.g. Shoutcast, BBC Radio 1)
                  'E': Personalised recommendation except Last.fm (e.g.
                       Pandora, Launchcast)
                  'L': Last.fm (any mode). In this case, the 5-digit Last.fm
                       recommendation key must be appended to this source ID to
                       prove the validity of the submission (for example,
                       "L1b48a").
                  'U': Source unknown
   @param rating: The rating of the song. One of:
                  'L': Love (on any mode if the user has manually loved the
                       track)
                  'B': Ban (only if source=L)
                  'S': Skip (only if source=L)
                  '':  Not applicable
   @param length: The song length in seconds
   @param album:  The album name
   @param trackno:The track number
   @param mbid:   MusicBrainz Track ID
   @param autoflush: Automatically flush the cache to AS?
   """

   global SUBMIT_CACHE, MAX_CACHE

   source = source.upper()
   rating = rating.upper()

   if source == 'L' and (rating == 'B' or rating == 'S'):
      raise ProtocolError("""You can only use rating 'B' or 'S' on source 'L'.
See the docs!""")

   if source == 'P' and length == '':
      raise ProtocolError("""Song length must be specified when using 'P' as
source!""")

   if type(time) != type(1):
      raise ValueError("""The time parameter must be of type int (unix
timestamp). Instead it was %s""" % time)

   SUBMIT_CACHE.append(
         { 'a': unicode(artist).encode('utf-8'),
           't': unicode(track).encode('utf-8'),
           'i': time,
           'o': source,
           'r': rating,
           'l': length,
           'b': unicode(album).encode('utf-8'),
           'n': trackno,
           'm': mbid
            }
         )

   if autoflush or len(SUBMIT_CACHE) >= MAX_CACHE:
      flush()

def flush():
   "Sends the cached songs to AS."
   global SUBMIT_CACHE

   values = {}

   for i, item in enumerate(SUBMIT_CACHE):
      for key in item:
         values[key + "[%d]" % i] = item[key]

   values['s'] = SESSION_ID

   data = urllib.urlencode(values)
   req = urllib2.Request(POST_URL, data)
   response = urllib2.urlopen(req)
   result = response.read()
   lines = result.split('\n')

   if lines[0] == "OK":
      SUBMIT_CACHE = []
      return True
   elif lines[0] == "BADSESSION" :
      raise SessionError('Invalid session')
   elif lines[0].startswith('FAILED'):
      handle_hard_error()
      raise BackendError("Authencitation with AS failed. Reason: %s" %
            lines[0])
   else:
      # some hard error
      handle_hard_error()
      return False
