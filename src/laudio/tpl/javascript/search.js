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
 * This is the search class which handles searches
 *
 */
function Search() {
    // ids
    this.songlist = 'songlist';

    // request urls
    this.url_advanced = '{% url "player:ajax_search_advanced" %}';
    this.url_artist_letters = '{% url "player:ajax_search_artist_letter" %}';
    this.url_search = '{% url "player:ajax_search" %}';
}


/**
 * Start a search
 *
 * @param url: which url we should search
 * @param data: the data array we should pass
 */
Search.prototype.ajax_search = function (url, data) {
    // Start animation
    $('#' + this.songlist + ' table tbody').fadeOut('fast');
    $('#' + this.songlist + ' .loader').fadeIn('slow');
    
    // unbind previous items from context to prevent slowdown
    $('#' + this.songlist + ' table tbody tr').unbind('contextmenu');
    
    var self = this;
    // now that we got the get url, start query
    $('#' + self.songlist + ' table tbody').load(url, data, function (){
        $('#' + self.songlist + ' .loader').fadeOut('fast', function(){
            $('#' + self.songlist + ' table tbody').fadeIn('fast');
            // set color to just playing song
            var lastSong,
                context;
            if(player === undefined){
                lastSong = 0;
                context = '';
            } else {
                lastSong = player.id;
                context = player.context;
            }
            
            // if we didnt just start it see if the currently played
            // song is in the collection and highlight it
            if (lastSong !== 0 && context === self.songlist){
                $( id_to_row(lastSong, true) ).addClass('active');
            }
            
            // update table sorting
            $('#' + self.songlist + ' table').trigger('update');

            // update context menu
            collection_context_menu();
        });
    }); 
}


/**
 * Starts a search for artists and starting letters
 * @param searchterm: The search string
 */
Search.prototype.artist_letters = function (searchterm){
    var data = {
        search: searchterm
    }
    this.ajax_search(this.url_artist_letters, data);
}


/**
 * Starts a search in all columns
 * @param searchterm: The search string
 */
Search.prototype.simple = function (searchterm){
    var data = {
        search: searchterm
    }
    this.ajax_search(this.url_search, data);
}

/**
 * Starts a search in all columns
 * @param artist: the artist
 * @param album: the album
 * @param genre: the genre
 */
Search.prototype.advanced = function (title, artist, album, genre){
    var data = {
        title: title,
        artist: artist,
        album: album,
        genre: genre
    }
    this.ajax_search(this.url_advanced, data);
}

