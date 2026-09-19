/* Pi Market - Notifications utilitaires */
(function () {
    'use strict';

    function requestPermission() {
        if (!('Notification' in window)) return Promise.resolve(false);
        if (Notification.permission === 'granted') return Promise.resolve(true);
        if (Notification.permission === 'denied') return Promise.resolve(false);
        return Notification.requestPermission().then((p) => p === 'granted');
    }

    function show(title, body) {
        if (!('Notification' in window) || Notification.permission !== 'granted') return;
        try {
            new Notification(title, { body: body, icon: '/static/images/icon-192x192.png' });
        } catch (e) {
            /* Les notifications peuvent échouer silencieusement */
        }
    }

    window.PiNotifications = { requestPermission: requestPermission, show: show };
})();
