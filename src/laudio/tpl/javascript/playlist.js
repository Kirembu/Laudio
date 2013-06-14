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
 * The playlist class which is used to handle everything playlist related
 */
function Playlist() {
    this.playlist = 'playlist';
    this.playlist_header = 'playlist_header h1';
    // this id gets incremented when a new item is added to the playlist to 
    // ensure unique row ids
    this.last_row_id = 0;
    
    this.url_load_playlist = '{% url "player:ajax_playlist_load" %}';
}

/**
 * Adds a dom element to the current playlist
 *
 * @param row: The dom element from the songlist
 */
Playlist.prototype.add = function (row) {
    var id = row_to_id( $(row).attr('id') );
    var title = $(row).children('td:eq(1)').html();
    var artist = $(row).children('td:eq(2)').html();

    var self = this;
    this.last_row_id++;
    $('#' + this.playlist + ' table > tbody').append($('<tr>')
        .attr('title', id)
        .attr('id', 'plrow' + self.last_row_id)
        .dblclick( function(){
            play_row(this);
        })
        .click( function(){
            select_lines(this);
        })
        .append($('<td>')
            .html(artist + ' - ' + title)
        )
    );
    update_line_colors('#playlist table');
    playlist_context_menu();
}


/**
 * Clears the playlist
 */
Playlist.prototype.clear = function () {
    $('#' + this.playlist + ' tbody').empty('tr');
}

/**
 * Saves the current playlist
 *
 * @param name: The name of the playlist
 */
Playlist.prototype.save = function (name) {

}

/**
 * Sets the header of the playlists
 *
 * @param to: The name of the the new header
 */
Playlist.prototype.change_header = function (to) {
    $('#' + this.playlist_header).html(to);
}

/**
 * Loads a playlist
 *
 * @param name: The name of the playlist
 */
Playlist.prototype.load = function (name) {
    // unbind previous items from context to prevent slowdown
    $('#' + this.playlist + ' table tbody tr').unbind('contextmenu');
    var data = { 
        name: name
    };
    var self = this;
    
    // now that we got the get url, start query
    $('#' + self.playlist + ' table tbody').fadeOut('fast', function(){
        $('#' + self.playlist + ' .loader').fadeIn('fast', function(){
            $('#' + self.playlist + ' table tbody').load(self.url_load_playlist, data, function (){
                $('#' + self.playlist + ' .loader').fadeOut('fast', function(){
                    $('#' + self.playlist + ' table tbody').fadeIn('fast');
                    // update context menu
                    playlist_context_menu();
                });
            }); 
        });
    });
    

}
