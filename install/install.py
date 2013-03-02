#!/usr/bin/python

#
# Copyright 2013 - Tom Alessi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Quinico Install Script
   
   Requirements
    - Quinico source downloaded from https://code.google.com/quinico

"""


import os
import random
import re
import shutil


def terminate(e):
    """Print an error and exit"""

    print '\n\n*** Error encountered: %s' % e
    print 'Install script will exit.  Please correct the issue and run the install/upgrade again.'
    exit(2)


def create_log(app_dir,apache_uid):
    """Create the Quinico log directory and initialize the log file"""

    # Create the directory
    print 'Creating log directory:%s/log' % app_dir
    if os.path.exists('%s/log' % app_dir):
        print 'Log directory already exists, removing it before recreating.'
        try:
            shutil.rmtree('%s/log' % app_dir)
        except Exception as e:
            terminate(e)
 
    try:
        os.makedirs('%s/log' % app_dir)
    except Exception as e:
        terminate(e)

    # Create the log file and set the permissions
    print 'Creating the initial log file:%s/log/quinico.log' % app_dir
    try:
        fl = open('%s/log/quinico.log' % app_dir,'w')
        os.chown('%s/log/quinico.log' % app_dir,int(apache_uid),-1)
    except Exception as e:
        terminate(e)


def create_pid(app_dir,apache_uid):
    """Create the Quinico jobs pid directory"""

    # Create the directory and set permissions
    print 'Creating pid directory and setting permissions:%s/jobs/pid' % app_dir
    if os.path.exists('%s/jobs/pid' % app_dir):
        print 'Pid directory already exists, removing it before recreating.'
        try:
            shutil.rmtree('%s/jobs/pid' % app_dir)
        except Exception as e:
            terminate(e)
 
    try:
        os.makedirs('%s/jobs/pid' % app_dir)
        os.chown('%s/jobs/pid' % app_dir,int(apache_uid),-1)
    except Exception as e:
        terminate(e)


def customize_settings(app_dir,dst_local):
    """Customize the Quinico settings.py file"""

    print 'Customizing %s/quinico/settings.py' % app_dir

    try:
        # Open the settings.py template file
        s_sp = open('%s/quinico/settings.py.tmpl' % app_dir).read()

        # Add the path to the Quinico local dir
        s_sp = s_sp.replace('$__local_dir__$',dst_local)

        # Add the path to the Quinico log dir
        s_sp = s_sp.replace('$__app_dir__$',app_dir)

        # Write out the new file
        f_sp = open('%s/quinico/settings.py' % app_dir,'w')
        f_sp.write(s_sp)
        f_sp.close() 
    except Exception as e:
        terminate(e)


def customize_local_settings(db_user,db_pass,db_host,db_port,dst_local,app_dir,
                             smtp_host,smtp_sender,smtp_recipient,apache_uid):
    """Customize the Quinico local_settings.py file"""

    try:
        # Open the local_settings.py file
        print 'Customizing %s/local_settings.py for your installation' % dst_local
        s_ls = open('%s/local_settings.py' % dst_local).read()

        # Add the database information
        s_ls = s_ls.replace('$__db_user__$',db_user)
        s_ls = s_ls.replace('$__db_pass__$',db_pass)
        s_ls = s_ls.replace('$__db_host__$',db_host)
        s_ls = s_ls.replace('$__db_port__$',db_port)

        # Add the SMTP information
        s_ls = s_ls.replace('$__smtp_host__$',smtp_host)
        s_ls = s_ls.replace('$__smtp_sender__$',smtp_sender)
        s_ls = s_ls.replace('$__smtp_recipient__$',smtp_recipient)

        # Add the template and application path information
        s_ls = s_ls.replace('$__app_dir__$',app_dir)

        # Add the secret key
        secret_key = "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)])
        s_ls = s_ls.replace('$__secret_key__$',secret_key)

        # Write out the new file
        f_ls = open('%s/local_settings.py' % dst_local,'w')
        f_ls.write(s_ls)
        f_ls.close() 

        # Set permissions to 600 and ownership apache_uid:root
        os.chown('%s/local_settings.py' % dst_local,int(apache_uid),-1)
        os.chmod('%s/local_settings.py' % dst_local,0600)
    except Exception as e:
        terminate(e)


def customize_wsgi_conf(app_dir,wsgi_dir,django_admin,dst_local):
    """Customize the Quinico wsgi.conf file"""

    print 'Customizing %s/wsgi.conf for your installation' % dst_local

    try:
        # Open the wsgi.conf file
        s_wc = open('%s/wsgi.conf' % dst_local).read()

        # Add the path to the local wsgi.py file
        s_wc = s_wc.replace('$__dst_local__$',dst_local)

        # Add the path to the Quinico html static assets
        s_wc = s_wc.replace('$__app_dir__$',app_dir)

        # Add the path to the DJango admin html static assets
        s_wc = s_wc.replace('$__django_admin__$',django_admin)

        # Add the path to the Apache mod_wsgi.so module
        s_wc = s_wc.replace('$__wsgi_dir__$',wsgi_dir)

        # Write out the new file
        f_wc = open('%s/wsgi.conf' % dst_local,'w')
        f_wc.write(s_wc)
        f_wc.close() 
    except Exception as e:
        terminate(e)


def customize_wsgi_py(app_dir,dst_local):
    """Customize the Quinico wsgi.conf file"""

    print 'Customizing %s/wsgi.py for your installation' % dst_local

    try:
        # Open the wsgi.py file
        s_wp = open('%s/wsgi.py' % dst_local).read()

        # Add the path to the Quinico project dir
        s_wp = s_wp.replace('$__app_dir__$',app_dir)

        # Write out the new file
        f_wp = open('%s/wsgi.py' % dst_local,'w')
        f_wp.write(s_wp)
        f_wp.close() 
    except Exception as e:
        terminate(e)


def apache_symlink(dst_local,web_conf):
    """Create a symlink in the apache configuration directory to wsgi.conf"""

    print 'Creating Apache symlink to %s/wsgi.conf' % dst_local

    # Create the symlink
    # If the symlink is already there, remove it
    try:
        if os.path.exists('%s/wsgi.conf' % web_conf):
            print '%s/wsgi.conf symlink exists, removing and recreating it' % dst_local
            os.unlink('%s/wsgi.conf' % web_conf)
        os.symlink('%s/wsgi.conf' % dst_local,'%s/wsgi.conf' % web_conf)
    except Exception as e:
        terminate(e)


def quinico_symlink(app_dir,quinico_src):
    """Create the generic quinico symlink to the source directory"""

    # If the symlink is already there, remove it
    print 'Creating quinico symlink: %squinico -> %s' % (app_dir,quinico_src)

    try:
        if os.path.exists('%squinico' % app_dir):
            if os.path.islink('%squinico' % app_dir):
                print 'quinico symlink exists, removing and recreating it'
                os.unlink('%squinico' % app_dir)

        # Create the symlink
        os.symlink(quinico_src,'%squinico' % app_dir)
    except Exception as e:
        terminate(e)


def split_directories(quinico_src):
    """Split the source directory from its path"""

    # Determine the source and application directory names
    src_match = re.search('^\/(\S+\/)*(\S+)$',quinico_src)
    
    if src_match is None:
        terminate('The quinico source directory could not be determined.')

    app_dir = src_match.group(1)
    app_dir = "/" + app_dir
    quinico_src_dir = src_match.group(2)
    print 'Quinico application directory: %s' % app_dir
    print 'Quinico source directory: %s' % quinico_src_dir

    return(app_dir,quinico_src_dir)


def copy_local(src_local,dst_local):
    """Copy the generic Quinico local.tmpl so that it can be customized"""

    # If the quinico-local directory already exists, remove it
    print 'Checking for existing quinico-local directory at %s' % dst_local
    if os.path.exists(dst_local):
        print '%s exists, removing and recopying it.' % dst_local
        try:
            shutil.rmtree(dst_local)
        except Exception as e:
            terminate(e)

    # Copy the local.tmpl directory to the new quinico-local directory
    print 'Copying %s to %s' % (src_local,dst_local)
    try:
        shutil.copytree(src_local,dst_local)
    except Exception as e:
        print 'Error occurred: %s' % e
        terminate(e)


def install():
    """Perform fresh install of Quinico"""

    print 'PERFORMING FRESH INSTALL:\n'  

    quinico_src=raw_input("1: Enter the path to the Quinico source\n#>").strip()
    local_dir=raw_input('2: Enter the desired local directory location\n#>').strip()
    web_conf=raw_input('3: Enter the Apache configuration directory\n#>').strip()
    db_user=raw_input('4: Enter the database username\n#>').strip()
    db_pass=raw_input('5: Enter the database password\n#>').strip()
    db_host=raw_input('6: Enter the database server fully qualified hostname or IP address\n#>').strip()
    db_port=raw_input('7: Enter the database port\n#>').strip()
    django_admin=raw_input('8: Enter the path to the DJango admin static files\n#>').strip()
    apache_uid=raw_input('9: Enter the uid of the apache user\n#>').strip()
    wsgi_dir=raw_input('10: Enter the path to the Apache mod_wsgi.so module\n#>').strip()
    smtp_host=raw_input('11: Enter the smtp server fully qualified hostname or IP address\n#>').strip()
    smtp_sender=raw_input('12: Enter the sender email address\n#>').strip()
    smtp_recipient=raw_input('13: Enter the recipient email address\n#>').strip()

    install_text = """You have entered the following options:
            - Quinico Source        : %s
            - Local Directory       : %s
            - Apache Conf Directory : %s
            - Database Username     : %s
            - Database Password     : ********
            - Database Host         : %s
            - Database Port         : %s
            - DJango Admin Location : %s
            - Apache UID            : %s
            - Path to mod_wsgi.so   : %s
            - SMTP Host             : %s
            - SMTP Sender           : %s
            - SMTP Recipient        : %s

         """ % (quinico_src,local_dir,web_conf,db_user,db_host,db_port,django_admin,
                apache_uid,wsgi_dir,smtp_host,smtp_sender,smtp_recipient)

    print install_text
    proceed=raw_input('Proceed with installation (y/n)\n#>').strip()

    if proceed == 'y':
        print 'proceeding...'
    else:
        print 'Exiting installation without modifying anything.'
        exit(0)

    # Write out the install file for debugging issues later
    install_file = open('install.txt','w')
    install_file.write(install_text)
    install_file.close() 

    # Determine the quinico source directory and path
    app_dir,quinico_src_dir = split_directories(quinico_src)

    # Create the generic quinico symlink
    quinico_symlink(app_dir,quinico_src)

    # Add 'quinico' to the app dir for the remainder of this script
    app_dir = app_dir + 'quinico'

    # Setup the log directory and file
    create_log(app_dir,apache_uid)

    # Setup the pid directory
    create_pid(app_dir,apache_uid)

    # Source and Destination local directories
    src_local = app_dir + '/local.tmpl'
    dst_local = local_dir + '/quinico-local'

    # Copy the local.tmpl directory out of the source directory so it can be customized
    copy_local(src_local,dst_local)

    # Customize the new local_setting.py file
    customize_local_settings(db_user,db_pass,db_host,db_port,dst_local,app_dir,
                             smtp_host,smtp_sender,smtp_recipient,apache_uid)

    # Customize the new wsgi.conf file
    customize_wsgi_conf(app_dir,wsgi_dir,django_admin,dst_local)

    # Customize the new wsgi.py file
    customize_wsgi_py(app_dir,dst_local)

    # Setup the Apache symlink
    apache_symlink(dst_local,web_conf)

    # Customize settings.py to add the path the local_settings.py file
    customize_settings(app_dir,dst_local)


def upgrade():
    """Perform an upgrade of Quinico"""

    print 'PERFORMING QUINICO UPGRADE:\n'  

    quinico_src=raw_input("1: Please enter the path to the Quinico source\n#>").strip()
    local_dir=raw_input('2: Please enter the existing local directory location\n#>').strip()
    apache_uid=raw_input('3: Please enter the uid of the apache user\n#>').strip()

    upgrade_text = """You have entered the following options:\n
            - Quinico Source        : %s
            - Local Directory       : %s
            - Apache UID            : %s

         """ % (quinico_src,local_dir,apache_uid)

    print upgrade_text
    proceed=raw_input('Proceed with upgrade (y/n)\n#>').strip()

    if proceed == 'y':
        print 'proceeding...'
    else:
        print 'Exiting upgrade without modifying anything.'
        exit(0)

    # Write out the upgrade file for debugging issues later
    upgrade_file = open('upgrade.txt','w')
    upgrade_file.write(upgrade_text)
    upgrade_file.close()

    # Determine the quinico source directory and path
    app_dir,quinico_src_dir = split_directories(quinico_src)

    # Create the generic quinico symlink
    quinico_symlink(app_dir,quinico_src)

    # Destination local directory
    dst_local = local_dir + '/quinico-local'

    # Add 'quinico' to the app dir for the remainder of this script
    app_dir = app_dir + 'quinico'

    # Setup the log directory and file
    create_log(app_dir,apache_uid)

    # Setup the pid directory
    create_pid(app_dir,apache_uid)

    # Customize settings.py to add the path the local_settings.py file
    customize_settings(app_dir,dst_local)


### Main Program Execution ###


type=raw_input("""
**************************************
** QUINICO AUTOMATED INSTALL SCRIPT **
**************************************

Before proceeding, please ensure that you have read the installation
documentation available at http://www.quinico.com and that you understand
the installation options and expected answers.

Please select an install option:
1.  Install - install a new instance of Quinico
2.  Upgrade - upgrade from an existing Quinico installation

#>""")



if type == "1":
    install()
elif type == "2":
    upgrade()
else:
    terminate(e)

