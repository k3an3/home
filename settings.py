LOCATION = "Des Moines"
SOLAR_DEPRESSION = 'civil'
SECRET_KEY = 'changetosomethinglongandcomplex'
DEBUG = False
GOOGLE_API_KEY = 'your_key_here'
# Choices are 'celery', 'threading', 'multiprocessing'
ASYNC_HANDLER = 'celery'

try:
    from settings_local import *
except ImportError:
    pass
