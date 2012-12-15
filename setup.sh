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

install_dir="/usr/share/laudio"
config_dir="/etc/laudio"
needed_dirs=(   "/usr/share/laudio" 
                "/var/lib/laudio" 
                "/var/log/laudio"
                "/etc/laudio"
                "/etc/laudio/apache"
                "/etc/laudio/lighttpd"
        )
database_path="/var/lib/laudio/laudio.db"

# Please fix if changed or wrong
debian_deps="python-lxml python-django python-mutagen apache2 sqlite3 libapache2-mod-wsgi python-pysqlite2 ttf-dejavu ffmpeg"

arch_deps="django python-lxml mutagen apache python-pysqlite sqlite3 mod_wsgi ttf-dejavu ffmpeg"

fedora_deps="Django python-lxml python-mutagen httpd python-sqlite3dbm mod_wsgi dejavu-fonts-common ffmpeg"

gentoo_deps="dev-python/django dev-python/lxml media-libs/mutagen dev-python/pysqlite dev-db/sqlite www-apache/mod_wsgi www-servers/apache ttf-dejavu ffmpeg"

general_deps="
    python (2.7) \n
    python-lxml \n
    python-django (1.4) \n
    python-mutagen \n
    apache2 \n
    sqlite3 \n
    libapache2-mod-wsgi \n
    python-pysqlite2 \n
    ttf-dejavu \n
    ffmpeg \n
"

# get apache user and group
apache_ug="www-data"
if grep -Fxq apache /etc/group; then
   apache_ug=apache
fi
if grep -Fxq httpd /etc/group; then
   apache_ug=httpd
fi

# check for distro
distro="unknown"
if [ -f /etc/system-release ]; then 
  if grep -Fq Fedora /etc/system-release; then
     distro="fedora"
  fi
fi
if [ -f /etc/debian_version ]; then
	distro="debian"
	# includes Ubuntu, et al.
fi
# TODO: check for other distros

# checks if we are root otherwise aborts the execution
function require_root {
   if [ "$(whoami)" != 'root' ]; then
       echo "You have no permission to run $0 as non-root user."
       exit 1;
   fi
}

# creates directories
function create_dirs {
   for elem in ${needed_dirs[@]}; do
      if ! [[ -e $elem ]]; then
         mkdir -p $elem
      fi
   done
}

# creates the database
function create_database {
   python2 $install_dir/src/manage.py syncdb --noinput
}

# developement setup, dont use this in production!
function setup_devel_rights {
   # set every needed directory writable for all users
   for elem in ${needed_dirs[@]}; do
      if [[ -e $elem ]]; then
         chmod -R 0777 $elem
      fi
   done
}

# FIXME: please check this again thouroughly
function setup_production_rights {
   for elem in ${needed_dirs[@]}; do
      if [[ -e $elem ]]; then
         chown -R $apache_ug:$apache_ug $elem
         chmod -R 0755 $elem
      fi
   done
}

# installs the dependencies on the required platform
function install_deps {
   if [[ "$distro" == "fedora" ]]; then 
      yum install $fedora_deps
   fi

   if [[ "$distro" == "debian" ]]; then 
      apt-get install "$debian_deps"
   fi

   if [[ "$distro" == "arch" ]]; then 
      pacman -Sy "$arch_deps"
   fi

   if [[ "$distro" == "gentoo" ]]; then 
      emerge -av "$gentoo_deps"
   fi

   if [[ "$distro" == "unknown" ]]; then 
      echo "Unknown Distribution! Please install the following dependencies"
      echo -e "$general_deps"
   fi
}

function install_configs {
   cp -R dist/server_cfg/apache $config_dir
   cp -R dist/server_cfg/lighttpd $config_dir
   
   if [ "$distro" -eq "fedora" ]; then 
      ln -s /etc/laudio/apache/laudio.conf /etc/httpd/conf.d/laudio_apache.conf 
   fi

   if [ "$distro" -eq "debian" ]; then 
      ln -s /etc/laudio/apache/laudio.conf /etc/apache2/conf.d/laudio_apache.conf 
   fi

   if [ "$distro" -eq "arch" ]; then 
      ln -s /etc/laudio/apache/laudio.conf /etc/httpd/conf/extra/laudio_apache.conf 
      echo "Include conf/extra/laudio_apache.conf" >> /etc/httpd/conf/httpd.conf
   fi

   if [ "$distro" -eq "gentoo" ]; then 
      ln -s /etc/laudio/apache/laudio.conf /etc/apache2/vhosts.d/laudio_apache.conf 
   fi

}

function symlink_fonts {
   # FIXME for different distros
   mkdir -p $install_dir/src/laudio/static/upload/themes/default/font
   ln -s /usr/share/fonts/truetype/ttf-dejavu/DejaVuSans-Bold.ttf $install_dir/src/laudio/static/upload/themes/default/font/DejaVuSans-Bold.ttf
   ln -s /usr/share/fonts/truetype/ttf-dejavu/DejaVuSansCondensed.ttf $install_dir/src/laudio/static/upload/themes/default/font/DejaVuSansCondensed.ttf
}

function restart_apache {
   if [ "$distro" -eq "fedora" ]; then 
      systemctl restart httpd.service
   fi

   if [ "$distro" -eq "debian" ]; then 
      /etc/init.d/apache2 restart
   fi

   if [ "$distro" -eq "arch" ]; then 
      /etc/rc.d/httpd restart
   fi

   if [ "$distro" -eq "gentoo" ]; then 
      /etc/init.d/apache2 restart
   fi

   if [ "$distro" -eq "unknown" ]; then 
      echo "Please restart your apache webserver!"
   fi
}


# developement setup, dont use this in production!
function devel_setup {
   require_root
   install_deps
   create_dirs
   setup_devel_rights
   create_database
   chmod 0777 $database_path
   echo $distro
}

function production_setup {
   require_root
   install_deps
   create_dirs
   setup_production_rights
   install_configs
   symlink_fonts
   create_database
   cp -R src $install_dir
   mkdir -p $install_dir/src/laudio/static/upload
   chmod 0755 $database_path
   chown $apache_ug:$apache_ug $database_path
   chown -R $apache_ug:$apache_ug $install_dir/src/laudio/static
   restart_apache
}


# check for -r command to build and run program
while getopts ":dp" opt; do
case $opt in
        d)
            echo "Installing developement environment" >&2
            devel_setup
            ;;

        p)
            echo "Installing laudio" >&2
            production_setup
            ;;

        \?)
            echo "Invalid option: -$OPTARG" >&2
            ;;

      esac
done

if [ $# -lt 1 ]; then
   echo "Use -d for developement setup and -p for normal installation"
fi
