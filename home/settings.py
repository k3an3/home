LOCATION = "Des Moines"
SOLAR_DEPRESSION = 'civil'
SECRET_KEY = 'changetosomethinglongandcomplex'
DEBUG = False
GOOGLE_API_KEY = 'your_key_here'
LOG_FILE = 'home.log'
SECURITY_FOOTAGE_DIRS = ('/media/external/cam1', '/media/external/cam2')

try:
    from home.settings_local import *
except ImportError:
    pass
