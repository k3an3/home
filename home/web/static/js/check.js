if ('serviceWorker' in navigator) {
	console.log('Service Worker is supported');
	navigator.serviceWorker.register('/static/js/sw.js').then(function(reg) {
		console.log(':^)', reg);
		reg.pushManager.subscribe({
			userVisibleOnly: true
		}).then(function(sub) {
			console.log('endpoint:', sub.endpoint);
			ws.emit('subscribe', sub);
		});
	}).catch(function(err) {
		console.log(':^(', err);
	});
}
