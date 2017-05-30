import os

from flask_assets import Bundle

IOT_JS_DIR = 'home/web/static/js/iot'

common_css = Bundle(
    'dist/css/bootstrap.min.css',
    'dist/css/bootstrap-slider.min.css',
    'dist/css/jquery-ui.css',
    Bundle(
        'css/main.css',
        filters='cssmin',
        output='public/css/common.css'
    ),
)

common_js = Bundle(
    'dist/js/jquery.min.js',
    'dist/js/jquery-ui.min.js',
    'dist/js/bootstrap.min.js',
    'dist/js/bootstrap-slider.min.js',
)

auth_js = Bundle(
    'dist/js/socketio.min.js',
    Bundle(
        'js/check.js',
        'js/index.js',
        'js/main.js',
        'js/sw.js',
        [os.path.join(IOT_JS_DIR, f) for f in os.listdir('home/web/static/js/iot')],
        filters='jsmin',
        output='public/js/common.js'
    ),
)
