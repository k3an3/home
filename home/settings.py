# General
LOCATION = "Des Moines"
SOLAR_DEPRESSION = 'civil'
SECRET_KEY = 'changetosomethinglongandcomplex'
DEBUG = False
GOOGLE_API_KEY = 'your_key_here'
LOG_FILE = 'home.log'
BASE_URL = 'https://105ww.xyz/'
SECURITY_FOOTAGE_DIRS = ('/media/external/cam1', '/media/external/cam2')
TEMPLATE_DIR = 'iot'
DEVICE_HISTORY = 10
PUBLIC_GROUPS = ('living_room', 'general')
USE_LDAP = False
LDAP_PORT = 389
LDAP_SSL = False
LDAP_FILTER = "uid={},"
LDAP_ADMIN_GID = 0
SPOTIFY_API_KEY = 'your_key_here'

try:
    from home.settings_local import *
except ImportError:
    pass
