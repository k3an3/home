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

try:
    from home.settings_local import *
except ImportError:
    pass
