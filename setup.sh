#!/bin/bash
# Laudio - A webbased musicplayer
# 
# Copyright (C) 2010 Bernhard Posselt, bernhard.posselt@gmx.at
# 
# Laudio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# 
# Laudio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Laudio.  If not, see <http://www.gnu.org/licenses/>.


# general constants
INSTALL_DIR="/usr/share/laudio"
LAUDIO_CONF_DIR="/etc/laudio"
STANDARD_HTTP_USER="www-data"
CREATE_DIRS=(   "/usr/share/laudio" 
                "/var/lib/laudio" 
                "/var/log/laudio"
                "/etc/laudio"
                "/etc/laudio/apache"
                "/etc/laudio/lighttpd"
        )
DATABASE_FILE="/var/lib/laudio/laudio.db"

# arch linux specific contents
ARCH_HTTP_USER="http"


if [ "$(whoami)" != 'root' ]; then
    echo "You have no permission to run $0 as non-root user."
    exit 1;
fi

echo -e "\n\n\n                     WARNING\n\n"
echo "#####################################################"
echo "# This install script hasnt been thouroughly tested!#"
echo "# You have been warned.                             #"
echo "# Please read and check it before you execute it!   #"
echo -e "#####################################################\n"

echo "Please select your distribution and enter the number"
echo "0) Ubuntu"
echo "1) Arch Linux"
echo "2) Gentoo"
echo "3) Abort"

read DISTRO


case "$DISTRO" in

    # case Ubuntu
    0)
        echo "Installing for Ubuntu"
        echo "Installing Dependencies"
        apt-get install python-lxml python-django python-mutagen apache2 sqlite3 libapache2-mod-wsgi python-pysqlite2 ttf-dejavu ffmpeg
        echo "Setting up Apache"
        APACHE=$STANDARD_HTTP_USER
        echo "Removing previous installations"
        for elem in ${CREATE_DIRS[@]}; do
            if [[ -e $elem ]]; then
                rm -r $elem
            fi
        done
        cp -r dist/server_cfg/ $LAUDIO_CONF_DIR
        rm -rf /etc/apache2/conf.d/laudio_apache.conf 
        ln -s /etc/laudio/apache/laudio.conf /etc/apache2/conf.d/laudio_apache.conf 
        echo "Creating Directories and installing laudio"
        for elem in ${CREATE_DIRS[@]}; do
            if ! [[ -e $elem ]]; then
                mkdir -p $elem
            fi
            chown -R $APACHE:$APACHE $elem
            chmod -R 0755 $elem
        done
        cp -r src/laudio $INSTALL_DIR
        cp src/laudio/laudio.cfg $LAUDIO_CONF_DIR
        chown -R $APACHE:$APACHE $INSTALL_DIR
        chmod -R 0755 $INSTALL_DIR
        
        echo "Symlinking fonts"
        ln -s /usr/share/fonts/truetype/ttf-dejavu/DejaVuSans-Bold.ttf $INSTALL_DIR/laudio/static/upload/themes/default/font/DejaVuSans-Bold.ttf
        ln -s /usr/share/fonts/truetype/ttf-dejavu/DejaVuSansCondensed.ttf $INSTALL_DIR/laudio/static/upload/themes/default/font/DejaVuSansCondensed.ttf
        ln -s /var/music $INSTALL_DIR/laudio/static/audio
        
        echo "Creating Database"
        python $INSTALL_DIR/laudio/manage.py syncdb --noinput
        chown -R $APACHE:$APACHE $DATABASE_FILE
        chmod -R 0755 $DATABASE_FILE

        echo "Restarting apache"
        /etc/init.d/apache2 restart
    ;;

    # case Arch Linux
    1)
        echo "Installing for Arch Linux"
        echo "Installing Dependencies"
        pacman -S django python2-lxml mutagen apache python2-pysqlite sqlite3 mod_wsgi ttf-dejavu ffmpeg
        echo "Setting up Apache"  
        APACHE=$ARCH_HTTP_USER
        # check if the entry is already there
        conf=`grep -e laudio_apache.conf /etc/httpd/conf/httpd.conf`
        if [ "$conf" = "" ]; then
            echo "Include conf/extra/laudio_apache.conf" >> /etc/httpd/conf/httpd.conf
        fi
        # check if the mod_wsgi is enabled
        conf=`grep -e LoadModule wsgi_module /etc/httpd/conf/httpd.conf`
        if [ "$conf" = "" ]; then
            echo "LoadModule wsgi_module modules/mod_wsgi.so" >> /etc/httpd/conf/httpd.conf
        fi
        echo "Removing previous installations"
        for elem in ${CREATE_DIRS[@]}; do
            if [[ -e $elem ]]; then
                rm -r $elem
            fi
        done
        mv dist/server_cfg/apache $LAUDIO_CONF_DIR
        mv dist/server_cfg/lighttpd $LAUDIO_CONF_DIR
        rm -rf /etc/httpd/conf/extra/laudio_apache.conf 
        ln -s /etc/laudio/apache/laudio.conf /etc/httpd/conf/extra/laudio_apache.conf 
        echo "Creating Directories and installing laudio"
        for elem in ${CREATE_DIRS[@]}; do
            if ! [[ -e $elem ]]; then
                mkdir -p $elem
            fi
            chown -R $APACHE:$APACHE $elem
            chmod -R 0755 $elem
        done
        mv laudio $INSTALL_DIR 
        chown -R $APACHE:$APACHE $INSTALL_DIR
        chmod -R 0755 $INSTALL_DIR
        
        echo "Creating Database"
        python2 $INSTALL_DIR/laudio/manage.py syncdb --noinput
        chown -R $APACHE:$APACHE $DATABASE_FILE
        chmod -R 0755 $DATABASE_FILE

        echo "Restarting Apache"
        /etc/rc.d/httpd restart

        echo "If you want to start Laudio at boot, add httpd to your DAEMONS in"
        echo "/etc/rc.conf"
    ;;

    # case Gentoo
    2)
        echo "Installing for Gentoo"
        echo "Installing Dependencies"
        emerge -av dev-python/django dev-python/lxml media-libs/mutagen dev-python/pysqlite dev-db/sqlite www-apache/mod_wsgi www-servers/apache ttf-dejavu ffmpeg
        echo "Setting up Apache"
        APACHE=$STANDARD_HTTP_USER
        echo "Removing previous installations"
        for elem in ${CREATE_DIRS[@]}; do
            if [[ -e $elem ]]; then
                rm -r $elem
            fi
        done
        mv dist/server_cfg/apache $LAUDIO_CONF_DIR
        mv dist/server_cfg/lighttpd $LAUDIO_CONF_DIR
        rm -rf /etc/apache2/vhosts.d/laudio_apache.conf
        ln -s /etc/laudio/apache/laudio.conf /etc/apache2/vhosts.d/laudio_apache.conf 
        echo "Creating Directories and installing laudio"
        for elem in ${CREATE_DIRS[@]}; do
            if ! [[ -e $elem ]]; then
                mkdir -p $elem
            fi
            chown -R $APACHE:$APACHE $elem
            chmod -R 0755 $elem
        done
        mv laudio $INSTALL_DIR
        chown -R $APACHE:$APACHE $INSTALL_DIR
        chmod -R 0755 $INSTALL_DIR
        
        echo "Creating Database"
        python $INSTALL_DIR/laudio/manage.py syncdb --noinput
        chown -R $APACHE:$APACHE $DATABASE_FILE
        chmod -R 0755 $DATABASE_FILE

        echo "Restarting apache"
        /etc/init.d/apache2 restart
        echo "If you want to start Laudio at boot, add apache2 to your default"
        echo "runlevel: rc-update add apache2 default"
    ;;

    *)
        echo "Error: Unknown distribution, aborting"
        exit 1    
    ;;
esac

exit 0


