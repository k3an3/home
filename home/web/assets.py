import os

from flask_assets import Bundle

IOT_JS_DIR = 'home/web/static/js/iot'

common_css = Bundle(
    'dist/css/bootstrap.min.css',
    'dist/css/bootstrap-slider.min.css',
    'dist/css/jquery-ui.min.css',
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
    Bundle(
        'js/index.js',
        filters='jsmin',
        output='public/js/index.js'
    ),
)

display_css = Bundle(
    'dist/css/bootstrap.min.css',
    Bundle(
        'css/display.css',
        filters='cssmin',
        output='public/css/display.css'
    ),
)

display_js = Bundle(
    'dist/js/jquery.min.js',
    'dist/js/socketio.min.js',
    'dist/js/bootstrap.min.js',
    Bundle(
        'js/display.js',
        filters='jsmin',
        output='public/js/display.js',
    )
)

auth_js = Bundle(
    'dist/js/socketio.min.js',
    Bundle(
        'js/check.js',
        'js/main.js',
        'js/sw.js',
        [os.path.join(IOT_JS_DIR, f) for f in os.listdir('home/web/static/js/iot')],
        filters='jsmin',
        output='public/js/common.js'
    ),
)
