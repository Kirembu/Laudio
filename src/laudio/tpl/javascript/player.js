{% load i18n %}
/**
 * Laudio - A webbased musicplayer
 *
 * Copyright (C) 2010 Bernhard Posselt, bernhard.posselt@gmx.at
 *
 * Laudio is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * Laudio is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 */



/**
 * The player class which handles playing music and the music logic
 *
 * @param manager: The soundmanager
 */
function Player(manager) {
    // can be library or playlist
    // this is used to determine wether we have to play the next song in the
    // songlist or the playlist
    // songlist and playlist are the ids of div elements with the tables in them
    // songdata is the id of the div with the songdata in it (sidebar)
    this.playlist = 'playlist';
    this.songlist = 'songlist';
    this.songdata = 'songdata';
    this.databasedata = 'databasedata';
    this.progressbar = 'progress';
    this.progressbar_sec = 'progress_sec';
    this.play_icon = 'play_icon';
    this.volume_icon = 'mute_icon';
    this.shuffle_icon = 'shuffle_icon';
    this.repeat_icon = 'repeat_icon';
    this.context = this.songlist;

    // repeat can have 3 modes: 0, 1 and 2
    // 0 is no repeat
    // 1 is repeat current song after finish
    // 2 is repeat all after playlist/songlist has ended
    this.repeat = 0;

    // If shuffle is activated
    this.shuffle = false;

    // volume can be between 0 and 100
    this.volume = 100;

    // muted value only when no song is playing
    this.muted = false;

    // song data
    this.id = 0;
    this.tracknr = '';
    this.title = '';
    this.artist = '';
    this.album = '';
    this.genre = '';
    this.codec = '';
    this.bitrate = '';
    this.duration = 0;
    this.date = '';
    this.est_duration = 0;

    // soundManager setup
    this.manager = manager;
    this.manager.url = '{{ STATIC_URL }}js/lib/soundmanager/swf/';
    this.manager.useHTML5Audio = true;
    this.manager.flashVersion = 8;
    this.manager.debugFlash = true;
    this.manager.audioFormats.mp4.required = false;
    this.manager.wmode = 'transparent';
    this.manager.allowScriptAccess = 'always';
    this.manager.useFastPolling = false;
    this.manager.preferFlash = false;
    
    // icon presets
    this.update_shuffle_icon();
    this.update_repeat_icon();
    this.set_sidebar_db_info();
}


/**
 * Toggles the play or pause
 */
Player.prototype.toggle_play_pause = function () {
    // if no song has been played yet, play the first one in the list
    if (this.id === 0) {
        this.play_next();
    } else {
        this.manager.togglePause(this.id);
    }
    this.update_play_icon();
}

/**
 * Toggles mute
 */
Player.prototype.toggle_mute = function () {
    if (this.id !== 0) {
        this.manager.toggleMute(this.id);
    }
    if (this.muted) {
        this.muted = false;
    } else {
        this.muted = true;
    }
    this.update_volume_icon();
}

/**
 * Toggles shuffle
 */
Player.prototype.toggle_shuffle = function () {
    if (this.shuffle) {
        this.shuffle = false;
    } else {
        this.shuffle = true;
    }
    this.update_shuffle_icon();
}

/**
 * Toggles repeat
 */
Player.prototype.toggle_repeat = function () {
    this.repeat += 1;
    this.repeat %= 3;
    this.update_repeat_icon();
}

/**
 * Plays a row with the id given
 *
 * @param row: The row dom object
 */
Player.prototype.play = function (row) {
    // handle wrong ids
    if (!row) {
        return false;
    }
    
    // check if a song is still playing and if so remove active class
    this.context = $('#' + row.id).parent().parent().parent().attr("id");
    if(this.id !== 0 && this.manager.getSoundById(this.id).playState === 1){
        var song = this.manager.getSoundById(this.id);
        if(song !== undefined){
            this.manager.destroySound(this.id);
        }
    }
    
    $('#content .active').removeClass('active');
    $(row).addClass('active');
    $(row).removeClass('selected');
    
    // get context
    var queryid;
    if (this.context === this.songlist) {
        this.id = row_to_id(row.id);
        queryid = this.id;
    } else {
        this.id = plrow_to_id(row.id);
        queryid = row.title;
    }

    // value needed for play
    var self = this;
    
    $.getJSON('{% url 'player:ajax_song_data' %}', { id: queryid }, function (json) {
        self.tracknr = json.tracknr;
        self.title = json.title;
        self.artist = json.artist;
        self.album = json.album;
        self.genre = json.genre;
        self.codec = json.codec;
        self.bitrate = json.bitrate;
        self.duration = json.duration;
        self.date = json.date;
        self.relpath = json.relpath;
        
        self.manager.onready(function(){
            // play song
            self.manager.createSound({
                id: self.id,
                url: '{{ STATIC_URL }}audio/' + self.relpath,
                volume: self.volume
            });

            self.manager.play(self.id, {
                onfinish: function () {
                    {% if user.is_authenticated %}
                        self.scrobble(self.id);
                    {% endif %}
                    self.play_next();
                    self.update_play_icon();
                },
                onpause: function () {
                    self.update_play_icon();
                },
                onplay: function () {
                    self.update_volume_icon();
                    self.update_play_icon();
                    self.set_volume(self.volume);
                },
                onresume: function () {
                    self.update_play_icon();
                },
                whileplaying: function () {
                    // set values
                    var pos = this.position;
                    if (this.isBuffering) {
                        self.est_dur = this.durationEstimate;
                    } else {
                        self.est_dur = this.duration;
                    }
                    self.update_position(pos, self.est_dur);
                }
            });

            self.set_sidebar_info(); 
            self.set_title_info();
            
            // set cover
            $.getJSON('{% url 'player:ajax_song_cover' %}', { id: queryid }, function (json) {
                $('#songcover').css('background-image', 'url(\'' + json.path + '\')');
            });
        });

    });
}

/**
 * Gets a random row according to the context
 * 
 * @return: The id of the row, if no song is found then return false
 */
Player.prototype.random_row = function () {
    var random_number,
        entries_len;
    entries_len = $('#' + this.context + ' tbody tr').length;
    if (entries_len === 0) {
        return false;
    } else {
        random_number = Math.floor(Math.random() * entries_len);
        return $('#' + this.context + ' tbody tr:eq(' + random_number + ')').attr('id');
    }
}

/**
 * Gets the next song
 * 
 * @return: The id of the row, if no song is next then return false
 */
Player.prototype.next_row = function () {
    // return false if there are no songs in the tables
    if ($('#' + this.context + ' tbody tr').length === 0) {
        return false;
    }
    // get the currently playing song
    var $current_song;
    if (this.context === this.songlist) {
        $current_song = $('#' + this.songlist + ' tbody ' + id_to_row(this.id, true));
    } else {
        $current_song = $('#' + this.playlist + ' tbody ' + id_to_plrow(this.id, true));
    }

    // check if the song is in the current selection
    // if not, return the id of the first song
    if ($current_song.length === 0) {
        return $('#' + this.context + ' tbody tr:first').attr('id');
    }

    // if repeat is enabled, return the same id
    if (this.repeat === 1 && $current_song.length !== 0) {
        return $current_song.attr('id');
    }

    // if shuffle is enabled return a random row
    if (this.shuffle) {
        return this.random_row();
    }

    // If no repeat and shuffle were enabled, just return the next song
    if ($current_song.next().length !== 0) {
        return $current_song.next().attr('id');

    // if theres no next song, check for repeat all
    } else {
        if (this.repeat === 2) {
            return $('#' + this.context + ' tbody tr:first').attr('id');
        }
    }

    // if theres no next song return false
    return false;
}

/**
 * Gets the previous song
 * 
 * @return: The id of the row, if no song is previous then return false
 */
Player.prototype.previous_row = function () {
    // return false if there are no songs in the tables
    if ($('#' + this.context + ' tbody tr').length === 0) {
        return false;
    }

    var $current_song;
    // get the currently playing song
    if (this.context === this.songlist) {
        $current_song = $('#' + this.songlist + ' tbody ' + id_to_row(this.id, true));
    } else {
        $current_song = $('#' + this.playlist + ' tbody ' + id_to_plrow(this.id, true));
    }

    // check if the song is in the current selection
    // if not, return the id of the first song
    if ($current_song.length === 0) {
        return $('#' + this.context + ' tbody tr:first').attr('id');
    }

    // check if the played song is the first in the list
    if ($current_song.prev().length !== 0) {
        return $current_song.prev().attr('id');
    }

    // if theres no previous song return false
    return false;
}

/**
 * Plays the next song
 */
Player.prototype.play_next = function () {
    if (this.next_row() !== false) {
        this.play($('#' + this.next_row())[0]);
    }
}

/**
 * Plays the previous song
 */
Player.prototype.play_previous = function () {
    if (this.previous_row() !== false) {
        this.play($('#' + this.previous_row())[0]);
    }
}

/**
 * Scrobbles the song to lastfm/librefm
 *
 * @param id: The id of the song, integer
 */
Player.prototype.scrobble = function (id) {
    $.post('{% url 'player:ajax_song_scrobble' %}', { id: this.id });
}

/**
 * Sets the values for the sidebar
 *
 */
Player.prototype.set_sidebar_info = function () {
    // calculate date
    var mins,
        secs;
    mins = Math.floor(this.duration / 60);
    secs = this.duration % 60;
    if (secs < 10) {
        secs = '0' + secs;
    }

    // set values in the sidebar
    $('#' + this.songdata + ' tr:eq(0) td').html(this.title);
    $('#' + this.songdata + ' tr:eq(1) td').html(mins + ':' + secs);
    $('#' + this.songdata + ' tr:eq(2) td').html(this.tracknr);
    $('#' + this.songdata + ' tr:eq(3) td').html(this.artist);
    $('#' + this.songdata + ' tr:eq(4) td').html(this.album);
    $('#' + this.songdata + ' tr:eq(5) td').html(this.date);
    $('#' + this.songdata + ' tr:eq(6) td').html(this.genre);
    $('#' + this.songdata + ' tr:eq(7) td').html(this.codec);
    $('#' + this.songdata + ' tr:eq(8) td').html(this.bitrate + ' kb/s');
    
}

/**
 * Sets the value for the <title> element
 */
Player.prototype.set_title_info = function (id) {
    var info = this.title + " - " + this.artist;
    document.title = decode_html_entities(info);    
}

/**
 * Sets the database values of the sidebar
 */
Player.prototype.set_sidebar_db_info = function () {
    var self = this;
    $.getJSON('{% url 'player:ajax_db_statistics' %}', function (json) {
        // set database values in the sidebar
        $('#' + self.databasedata + ' tr:eq(0) td').html(json.numberOfSongs);
        $('#' + self.databasedata + ' tr:eq(1) td').html(json.numberOfDays);
        $('#' + self.databasedata + ' tr:eq(2) td').html(json.numberOfOggs);
        $('#' + self.databasedata + ' tr:eq(3) td').html(json.numberOfMp3s);
    });
}


/**
 * Sets the values for the sidebar
 *
 * @param value: Value from 0 to 100 
 */
Player.prototype.set_volume = function (value) {
    this.volume = value;
    this.update_volume_icon();
    if (this.id !== 0) {
        this.manager.setVolume(this.id, value);
    }
}

/**
 * Sets the position in a song
 *
 * @param position: Value from 0 to 100 
 */
Player.prototype.set_position = function (position) {
    if (this.id !== 0) {
        // get 1% of the duration and multiply by value
        var offset = Math.floor(this.est_dur * (position / 100));
        this.manager.setPosition(this.id, offset);
    }
}

/**
 * Updates the position in a song
 *
 * @param pos: The current position
 * @param dur: The duration
 */
Player.prototype.update_position = function (pos, dur) {
    dur = Math.floor(dur / 1000);
    pos = Math.floor(pos / 1000);
    // avoid div by 0
    if (!dur) {
        dur = 1;
    }

    var cmins,
        csecs,
        dmins,
        dsecs,
        prog,
        offset;
    // calculate seconds and minutes
    cmins = Math.floor(pos / 60);
    csecs = pos % 60;
    if (csecs < 10) {
        csecs = '0' + csecs;
    }
    dmins = Math.floor(dur / 60);
    dsecs = dur % 60;
    if (dsecs < 10) {
        dsecs = '0' + dsecs;
    }

    // update duration progress caption
    prog = cmins + ':' + csecs + ' {% blocktrans %}of{% endblocktrans %} ' + dmins + ':' + dsecs;
    $('#' + this.progressbar_sec).html(prog);

    // move progressbar
    offset = Math.ceil( (100 / dur) * pos);
    $('#' + this.progressbar).slider('value', offset);
}

/**
 * Returns the current id for the playing row
 *
 * @return: the current id
 */
Player.prototype.current_row_id = function () {
    var row_id;
    if (this.context === this.songlist) {
        row_id = 'row' + this.id;
    } else {
        row_id = 'plrow' + this.id;
    }
    return row_id;
}

/**
 * Checks if a song is playing or paused
 *
 * @return: Returns true if the player is playing a song, otherwise false
 */
Player.prototype.is_playing = function () {
    var song = this.manager.getSoundById(this.id);
    if(song === undefined){
        return false;
    } else {
        return !song.paused;
    }
    
}

/**
 * Checks if a song is muted
 *
 * @return: Returns true if the player is playing a song, otherwise false
 */
Player.prototype.is_muted = function () {
    // guard against no song loaded
    if (this.id !== 0) {
        if (this.manager.getSoundById(this.id).muted || this.volume === 0 || this.muted) {
            return true;
        }
    } else {
        if (this.volume === 0 || this.muted) {
            return true;
        }
    }
    return false;
}

/**
 * Updates the playing icon
 */
Player.prototype.update_play_icon = function () {
    if (this.id !== 0) {
        if (this.is_playing()) {
            $('#' + this.play_icon).removeClass('play');
            $('#' + this.play_icon).addClass('pause');
        } else {
            $('#' + this.play_icon).removeClass('pause');
            $('#' + this.play_icon).addClass('play');
        }
    }
}


/**
 * Updates the mute icon
 */
Player.prototype.update_repeat_icon = function () {
    if (this.repeat === 0) {
        $('#' + this.repeat_icon).removeClass('repeat');
        $('#' + this.repeat_icon).removeClass('repeatall');
        $('#' + this.repeat_icon).addClass('norepeat');
    } else if (this.repeat === 1) {
        $('#' + this.repeat_icon).removeClass('norepeat');
        $('#' + this.repeat_icon).removeClass('repeatall');
        $('#' + this.repeat_icon).addClass('repeat');
    } else {
        $('#' + this.repeat_icon).removeClass('repeat');
        $('#' + this.repeat_icon).removeClass('norepeat');
        $('#' + this.repeat_icon).addClass('repeatall');
    }
}

/**
 * Updates the mute icon
 */
Player.prototype.update_shuffle_icon = function () {
    if (this.shuffle) {
        $('#' + this.shuffle_icon).removeClass('noshuffle');
        $('#' + this.shuffle_icon).addClass('shuffle');
    } else {
        $('#' + this.shuffle_icon).removeClass('shuffle');
        $('#' + this.shuffle_icon).addClass('noshuffle');
    }
}

/**
 * Updates the volume icon
 */
Player.prototype.update_volume_icon = function () {
    if (this.is_muted()) {
        $('#' + this.volume_icon).removeClass('quiet');
        $('#' + this.volume_icon).removeClass('louder');
        $('#' + this.volume_icon).removeClass('unmuted');
        $('#' + this.volume_icon).addClass('muted');
    } else if (this.volume >= 66) {
        $('#' + this.volume_icon).removeClass('quiet');
        $('#' + this.volume_icon).removeClass('louder');
        $('#' + this.volume_icon).removeClass('muted');
        $('#' + this.volume_icon).addClass('unmuted');
    } else if (this.volume >= 33) {
        $('#' + this.volume_icon).removeClass('quiet');
        $('#' + this.volume_icon).removeClass('muted');
        $('#' + this.volume_icon).removeClass('unmuted');
        $('#' + this.volume_icon).addClass('louder');
    } else if (this.volume >= 1) {
        $('#' + this.volume_icon).removeClass('louder');
        $('#' + this.volume_icon).removeClass('muted');
        $('#' + this.volume_icon).removeClass('unmuted');
        $('#' + this.volume_icon).addClass('quiet');
    }
}
