# Changelog
## v0.14 (dev)
* Lock down API authentication edge cases
* Overhaul firewall controls
* FIDO2 support
* Overhaul login page
## v0.13
* Fix some frontend misbehavior
* Fix issue where Kasa bulb would jump to last brightness at beginning of fade
* Subclassed bulb and plug devices under new power class
* Change how devices are stored to improve performance
* Deprecated raven in favor of sentry_sdk
* Devices use UUIDs for unique identifiers instead of random string
* Add support for Etekcity brand smart plugs
* Allow both processes and threads to be used interchangeably for running tasks
* Use process/thread pools with worker limit. Fixes potential OOM bugs caused by 3rd-party modules
* Sonarcloud integration
* Additional features for computer-virt
* Fix logout link
* Fix closing the socket when using SimpleSocket
* Security fix for yaml parsing
* Support TP-Link Kasa bulbs
* Allow user to log out of all sessions
* Fix some bugs in weather module
* Additional API auth options
* The usual bugfixes and minor changes
## v0.12
* Control virt-manager through computer driver
* Added ability to manage users through web UI
* Added/fixed Docker compatibility
* Improved setuptools packaging
* Python 3.7 compatibility 
* Acknowledge when a clicked button has fired on the server
* LDAP fixes and 3rd-party auth integrations
* Some UI fixes
* Remove admin function visibility from unprivileged user sessions
* Prevent unprivileged users seeing all devices and actions
* Other bugfixes and minor improvements
## v0.11
* Merge several modules into single "computer" module for controlling computers over remote access protocols
* Multi-devices: a single device object acts as abstraction to multiple devices
* DDwrt Wi-Fi based presence detection
* Fix broken Chromecast controls (partially)
* Allow driver modules to define actions in a class attribute
* LDAP login logic fixes
* Multiple, configurable display panels with ACLs
* Fix bug preventing long-running WebSockets
* API client enforced ACLs, modifyable on admin panel
* Several admin functions served asynchronously
* Ping module push notifications only alert when devices go down
* Various admin features
* Improve logging inconsistencies
* Device config.yml now modifiable and validated from web
* WebSocket security fixes
* Sentry.io integration
* Celery tasks bound by soft time limit
* Prevent ping notifications from cascading
* Rough hooks for OAuth 2.0
* Weather module takes location through API instead of hardcoded location
* Numerous other features and bug/compatibility fixes

## v0.10
* Chainable actions
* Python package
* Improved security dashboard, secure video feeds and recordings
* Centrally managed and compressed assets
* Support for additional modules
* Jitter delay for actions
* Security fixes
* Ability to revert last command
* Automatic widget generation
* Widgets on homepage
* Support for display panel with info and controls
* API, widget ACLs based on zones/groups
* Optional LDAP user authentication
* Improved example config with documentation
* Allow IoT modules to be serialized that were previously unserializable
* Automatic frontend reload on updates
* WIP for tracking previous commands and reusing them
* Guest authentication via QR code
* Added mail, payments, Android MDM (WIP) modules
* Misc. fixes and improvements

## v0.9
* Task management with Celery or Multiprocessing
* Scheduled tasks with APScheduler
* Logging
* Additions to admin functionality
* Security dashboard
* Support for Ping, HTTP, Chromecast, Mopidy, WakeOnLAN, iptables-over-ssh, audio
* Public interface visibility option
* Retain history of sent commands
* Separate local YAML config
* Auto-update on code push
* Misc. fixes and improvements

## v0.8
* Major overhaul
* Support for Broadlink
* Dynamic code loading from YAML configuration file
* Basic admin interface
* API to trigger actions or device functions
* Browser push notifications

## v0.1
* Basic UI
* Websocket communication
* Basic securitycontroller and alerts
* Support for MagicHome Bulb, Motion for Linux
