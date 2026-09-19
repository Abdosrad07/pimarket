/**
 * Toast notification system for Pi Market
 * Usage: showToast('success', 'Message here');
 *        showToast('error', 'Error message');
 *        showToast('warning', 'Warning message');
 *        showToast('info', 'Info message');
 */
(function() {
    const ICONS = {
        success: 'bi-check-circle-fill',
        error:   'bi-x-circle-fill',
        warning: 'bi-exclamation-triangle-fill',
        info:    'bi-info-circle-fill'
    };
    const COLORS = {
        success: '#10b981',
        error:   '#ef4444',
        warning: '#f59e0b',
        info:    '#3b82f6'
    };

    function showToast(type, message, duration) {
        type = type || 'info';
        duration = duration || 4000;
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'toast-pi toast-' + type;
        toast.setAttribute('role', 'alert');
        toast.innerHTML =
            '<span class="toast-icon" style="color:' + (COLORS[type] || COLORS.info) + '">' +
                '<i class="bi ' + (ICONS[type] || ICONS.info) + '"></i>' +
            '</span>' +
            '<span class="toast-msg">' + message + '</span>' +
            '<button class="toast-close" aria-label="Fermer">&times;</button>';

        toast.querySelector('.toast-close').addEventListener('click', function() {
            dismissToast(toast);
        });

        container.appendChild(toast);

        // Auto-dismiss
        var timer = setTimeout(function() { dismissToast(toast); }, duration);

        // Pause on hover
        toast.addEventListener('mouseenter', function() { clearTimeout(timer); });
        toast.addEventListener('mouseleave', function() {
            timer = setTimeout(function() { dismissToast(toast); }, 2000);
        });
    }

    function dismissToast(toast) {
        if (!toast || toast.classList.contains('toast-exit')) return;
        toast.classList.add('toast-exit');
        setTimeout(function() { toast.remove(); }, 300);
    }

    // Make globally available
    window.showToast = showToast;
})();
