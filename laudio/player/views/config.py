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
from laudio.src.inc.shortcuts import render as csrf_render

def config_settings(request):
    """The settings view
    """
    ctx = {}
    return csrf_render(request, 'player/settings.html', ctx)
    
    
def config_profile(request):
    """The profile view
    """    
    ctx = {}
    return csrf_render(request, 'player/profile.html', ctx)
