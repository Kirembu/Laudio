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

########################################################################
# AJAX Requests                                                        #
########################################################################
@check_login("admin")
def ajax_drop_collection_db(request):
    """Deletes all playlists and songs in the db"""
    config = LaudioSettings()
    config.resetDB()
    return render_to_response('requests/dropscan.html', { "msg": config.log })


@check_login("admin")
def ajax_scan_perc(request):
    """gets the last scan entry and the scan values"""
    f = open(settings.SCAN_LOG, 'r')
    data = f.read()
    f.close()
    try:
        data = data.split(" ")
        scanned = data[0]
        total = data[1]
    except IndexError:
        scanned = 0
        total = 1
    return render_to_response('requests/scan_info.html', {"scanned": scanned,
                                                          "total": total })

@check_login("admin")
def ajax_scan_collection(request):
    """Scan the files in the collection"""
    config = LaudioSettings()
    try:
        config.scan()
    except OSError, e:
        return render_to_response( 'requests/dropscan.html', {"msg": e } )
    return render_to_response('requests/dropscan.html', { "msg": config.log })





@check_login("user")
def ajax_song_metadata(request, id):
    """Returns a json object with metainformation about the song
    
    Keyword arguments:
    id -- the id of the song we want the metadata from
    
    """
    song = Song.objects.get(id=id)
    return render_to_response('requests/song_data.html', {"song": song})


@check_login("user")
def ajax_scrobble_song(request, id):
    """Scrobbles a song to last.fm and/or libre.fm
    
    Keyword arguments:
    id -- the id of the song we want to scrobble
    
    """
    song = Song.objects.get(id=id)
    msg = ""
    
    # if user is logged in submit stats
    if request.user.is_authenticated():
        now = int( time.mktime(datetime.datetime.now().timetuple()) )
        userprofile = request.user.get_profile()
        # check for last.fm scrobbling
        try:
            if request.user.get_profile().lastFMSubmit:
                if userprofile.lastFMName != "" and userprofile.lastFMPass != "":
                    scrobbler.login(userprofile.lastFMName,
                                    userprofile.lastFMPass,
                                    service="lastfm"
                                    )
                    scrobbler.submit(song.artist, song.title, now, source='P',
                                    length=song.length)
                    scrobbler.flush()
                    msg = msg + "Scroblled song to lastfm!<br />"
        # if something bad happens, just ignore it
        except (scrobbler.BackendError, scrobbler.AuthError,
                scrobbler.PostError, scrobbler.SessionError,
                scrobbler.ProtocolError):
            pass
            
        # check for libre.fm scrobbling
        try:
            if request.user.get_profile().libreFMSubmit:
                if userprofile.libreFMName != "" and userprofile.libreFMPass != "":
                    scrobbler.login(userprofile.libreFMName, 
                                    userprofile.libreFMPass,
                                    service="librefm" 
                                    )
                    scrobbler.submit(song.artist, song.title, now, source='P',
                                    length=song.length)
                    scrobbler.flush()
                    msg = msg + "Scroblled song to librefm!<br />"
        # if something bad happens, just ignore it
        except (scrobbler.BackendError, scrobbler.AuthError,
                scrobbler.PostError, scrobbler.SessionError,
                scrobbler.ProtocolError):
            pass

    return render_to_response('requests/scrobble.html', {"msg": msg})


@check_login("user")
def ajax_cover_fetch(request, id):
    """Fetches the URL of albumcover, either locally or from the Internet
    
    Keyword arguments:
    id -- the id of the song we want the cover from
    
    """
    song = Song.objects.get(id=id)
    fetcher = CoverFetcher(song)
    cover = fetcher.fetch()
    return render_to_response('requests/cover.html', {"coverpath": cover, "album": song.album})


@check_login("user")
def ajax_artists_by_letters(request, artist):
    """Returns songs of all artists starting with artist
    
    Keyword arguments:
    artist -- searches for artists in the db starting with this value
    
    """
    #artist = artist.encode("utf-8")
    songs = Song.objects.filter(artist__istartswith=artist).extra(select=
    {'lartist': 'lower(artist)', 'lalbum': 'lower(album)', 'ltrnr': 'tracknumber',}
            ).order_by('lartist', 'lalbum', 'ltrnr')
    return render_to_response('requests/songs.html', {'songs': songs, })


@check_login("user")
def ajax_whole_collection(request):
    """Get all the songs from the collection"""
    songs = Song.objects.all().extra(select=
    {'lartist': 'lower(artist)', 'lalbum': 'lower(album)', 'ltrnr': 'tracknumber',}
            ).order_by('lartist', 'lalbum', 'ltrnr')
    return render_to_response('requests/songs.html', {'songs': songs, })


@check_login("user")
def ajax_adv_autocompletion(request, row): 
    """This is the advanced autocompletion. We got 4 fields where the 
    can enter data. The data entered will be send as GET var term.
    The remaining 3 fields will be available as GET vars, title, artist,
    album or genre.
    
    Keyword arguments:
    row -- the field where the search is being entered
    
    """
    if request.method == "GET":
        songs = Song.objects.filter(
                title__contains=urllib.unquote_plus( request.GET.get("title", "") ),
                artist__contains=urllib.unquote_plus( request.GET.get("artist", "") ),
                album__contains=urllib.unquote_plus( request.GET.get("album", "") ),
                genre__contains=urllib.unquote_plus( request.GET.get("genre", "") ),
        ).values(row).distinct()
        return render_to_response('requests/autocomplete.html', {'songs': songs, 'row': row})
    #'values': songs.get(row)

@check_login("user")
def ajax_search_collection(request, search):
    """Get song where any field matches the search
    
    Keyword arguments:
    search -- terms we search for in one of our fields
    
    """
    # FIXME:    seperate keywords by space and check db for each element
    #           current setup only retrieves a result when one row matches the search
    #           the search should also match if the parts of the search var appear
    #           in different rows
    
    """Check if we get this via GET as an autocomplete request"""
    songs = Song.objects.filter(
        Q(title__contains=search)|
        Q(artist__contains=search)|
        Q(album__contains=search)|
        Q(genre__contains=search)
    ).extra(select=
            {'lartist': 'lower(artist)', 'lalbum': 'lower(album)', 'ltrnr': 'tracknumber',}
            ).order_by('lartist', 'lalbum', 'ltrnr')
    return render_to_response('requests/songs.html', {'songs': songs, })


@check_login("user")
def ajax_adv_search_collection(request):
    """Get songs where the fields contain the search params"""
    title = urllib.unquote_plus( request.GET.get("title", "") )
    length = urllib.unquote_plus( request.GET.get("length", "") )
    tracknr = urllib.unquote_plus( request.GET.get("tracknr", "") )
    artist = urllib.unquote_plus( request.GET.get("artist", "") )
    album = urllib.unquote_plus( request.GET.get("album", "") )
    date = urllib.unquote_plus( request.GET.get("date", "") )
    genre = urllib.unquote_plus( request.GET.get("genre", "") )
    codec = urllib.unquote_plus( request.GET.get("codec", "") )
    bitrate = urllib.unquote_plus( request.GET.get("bitrate", "") )
    songs = Song.objects.filter(title__contains=title,
                                length__contains=length,
                                tracknumber__contains=tracknr,
                                artist__contains=artist,
                                album__contains=album,
                                date__contains=date,
                                genre__contains=genre,
                                codec__contains=codec,
                                bitrate__contains=bitrate
    ).extra( select={'lartist': 'lower(artist)', 'lalbum': 'lower(album)', 
    'ltrnr': 'tracknumber',} ).order_by('lartist', 'lalbum', 'ltrnr')
    return render_to_response('requests/songs.html', {'songs': songs})


@check_login("user")
def ajax_song_download(request, id):
    """Returns a download of the requested song
    
    Keyword arguments:
    id -- the id of the song
    
    """
    song = Song.objects.get(id=id)
    path = os.path.join(settings.AUDIO_DIR, song.path)
    return send_file(request, path)



"""
START playlist requests
"""
@check_login("user")
def save_playlist(request, playlistName):
    """Saves a Playlist with name and items
    
    Keyword arguments:
    playlistName -- the name of the playlist
    
    """
    
    # check if any elements were passed at all
    playlistName = urllib2.unquote(playlistName)
    playlistItems = request.GET["songs"].split(",")
    
    # look up if a playlist with the name exists already, if so delete it
    try:
        pl = Playlist.objects.get(name=playlistName, user=request.user)
        pl.delete()
    except Playlist.DoesNotExist:
        pass
    
    # now create a new playlist with the passed items
    pl = Playlist(name=playlistName, added= int( time.time() ), user=request.user)
    pl.save()
    songs = []
    for number in playlistItems:
        try:
            sg = Song.objects.get(id=number)
            pe = PlaylistEntry(song=sg, playlist=pl)
            pe.save()
        except Song.DoesNotExist:
            pass
    msg = "saved playlist %s with %i songs" % (playlistName, len(playlistItems))
    return render_to_response('requests/empty.html', {"msg": msg})


@check_login("user")
def open_playlist(request, playlistId):
    """Opens a Playlist with name and items
    
    Keyword arguments:
    playlistId -- the id of the playlist
    
    """
    playlist = Playlist.objects.get(id=playlistId, user=request.user)
    songs = playlist.songs.all()
    name = playlist.name
    return render_to_response('requests/playlist_songs.html', {'songs': songs, 'playlist': name})


@check_login("user")
def get_playlist_name(request, playlistId):
    """Looks up a playlist name to the id
    
    Keyword arguments:
    playlistId -- the id of the playlist
    
    """
    playlist = Playlist.objects.get(id=playlistId, user=request.user)
    name = playlist.name
    return render_to_response('requests/empty.html', {"msg": name})


@check_login("user")
def playlist_exists(request, playlistName):
    """Looks if a playlist with a certain name already exsists for this
    user
    
    Keyword arguments:
    playlistName -- the name of the playlist
    
    """
    try:
        playlist = Playlist.objects.get(name=playlistName, user=request.user)
        return render_to_response('requests/playlist_exists.html', {"exists": 1})
    except Playlist.DoesNotExist:
        return render_to_response('requests/playlist_exists.html', {"exists": 0})
    
    
@check_login("user")
def delete_playlist(request, playlistId):
    """Deletes a Playlist with name and items
    
    Keyword arguments:
    playlistId -- the id of the playlist
    
    """
    playlist = Playlist.objects.get(id=playlistId, user=request.user).delete()
    msg = "deleted playlist"
    return render_to_response('requests/empty.html', {"msg": msg})
    
    
@check_login("user")
def rename_playlist(request, oldName, newName):
    """Saves a Playlist with name and items
    
    Keyword arguments:
    oldName -- the old name of the playlist
    newName -- the new name of the playlist
    
    """
    # see if the new name already exists in the database
    try:
        playlist = Playlist.objects.get(name=urllib2.unquote(newName), user=request.user)
        return render_to_response('requests/playlist_exists.html', {"exists": 1})
    except Playlist.DoesNotExist:
        playlist = Playlist.objects.get(name=urllib2.unquote(oldName), user=request.user)
        playlist.name = urllib2.unquote(newName)
        playlist.save()
        msg = "renamed playlist %s to %s" % (oldName, newName)
        return render_to_response('requests/playlist_exists.html', {"exists": 0})
    
    
@check_login("user")
def list_playlists(request):
    """Returns a list of all playlists"""
    playlists = Playlist.objects.filter(user=request.user).order_by('name')
    return render_to_response('requests/list_playlists.html', {'playlists': playlists})
