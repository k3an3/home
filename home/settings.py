# General
from peewee import SqliteDatabase

LOCATION = "Des Moines"
SOLAR_DEPRESSION = 'civil'
SECRET_KEY = 'changetosomethinglongandcomplex'
DEBUG = False
GOOGLE_API_KEY = 'your_key_here'
LOG_FILE = 'home.log'
BASE_URL = 'https://localhost:5000/'
SECURITY_FOOTAGE_DIRS = ('/media/external/cam1', '/media/external/cam2')
TEMPLATE_DIR = 'iot'
PUBLIC_GROUPS = ('living_room', 'general')
USE_LDAP = False
LDAP_HOST = ''
LDAP_PORT = 389
LDAP_SSL = False
LDAP_FILTER = "uid={}"
LDAP_ADMIN_GROUP = 'cn=admins,dc=example,dc=com'
LDAP_BASE_DN = 'cn=users,dc=example,dc=com'
SPOTIFY_API_KEY = 'your_key_here'
ASYNC_MODE = 'multiprocessing'
MEDIA_TEST_URI = '/test.mp4'
SENTRY_URL = ''
SMTP_SERVER = ''
SMTP_PORT = 25
SMTP_USERNAME = ''
SMTP_PASSWORD = ''
db = SqliteDatabase('app.db')
BACKEND_PATH = 'redis://'
BROKER_PATH = 'redis://'
CUSTOM_AUTH_HANDLERS = []
MAX_THREADS = 100
MAX_PROCESSES = 32
# db = MySQLDatabase(host="localhost", database="home", user="home", passwd="home")

try:
    from home.settings_local import *
except ImportError:
    pass
