"""Quinico Local Configuration File

   Required Configuration
    - Database username
    - Database password
      (note: database host/port can be ignored if its local and using the standard port)
    - Secret key
    - Full path to template directory

   Optional configuration
    - Everything else
   
"""

### Required ###

DATABASES = {
    'default': {
        'ENGINE'   : 'django.db.backends.mysql',
        'NAME'     : 'quinico',
        'USER'     : '$__db_user__$',       
        'PASSWORD' : '$__db_pass__$', 
        'HOST'     : '$__db_host__$', 
        'PORT'     : '$__db_port__$', 
    }
}
SECRET_KEY = '$__secret_key__$'
TEMPLATE_DIRS = (
    '$__app_dir__$/templates'
)

# Application Path
APP_DIR = '$__app_dir__$'

# Email Host Settings
SMTP_HOST = '$__smtp_host__$'
SMTP_SENDER = '$__smtp_sender__$'
SMTP_RECIPIENT = '$__smtp_recipient__$'

# Notification of SMTP errors (True/False)
# Because Quinico accesses many external services, if errors are occurring,
# it would be irresponsible to ignore them (so on by default)
SMTP_NOTIFY_ERROR = True

### Optional ###

# The following are already set in the project settings.py configuration
# file but may be overridden here

#TIME_ZONE = ''
