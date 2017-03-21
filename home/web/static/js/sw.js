self.addEventListener('install', function(event) {
    self.skipWaiting();
    console.log('Installed', event);

});
self.addEventListener('activate', function(event) {
    console.log('Activated', event);

});
self.addEventListener('push', function(event) {
    var title = '105ww Home';
	data = event.data.json();
    event.waitUntil(
        self.registration.showNotification(title, data, {
            body: data.body,
            icon: '/static/img/home.png'
        }));
});
self.addEventListener('notificationclick', function(event) {
    console.log('Notification click: tag ', event.notification.tag);
    event.notification.close();
    var url = 'https://105ww.xyz';
    event.waitUntil(
        clients.matchAll({
            type: 'window'
        })
        .then(function(windowClients) {
            for (var i = 0; i < windowClients.length; i++) {
                var client = windowClients[i];
                if (client.url === url && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});
