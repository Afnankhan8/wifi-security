document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Real-time updates for admin dashboard
    if (document.getElementById('devices-table')) {
        updateDevices();
        setInterval(updateDevices, 5000);
    }
    
    // Mark alerts as read when clicked
    document.querySelectorAll('.alert-item').forEach(item => {
        item.addEventListener('click', function() {
            const alertId = this.dataset.alertId;
            if (!this.classList.contains('read')) {
                fetch(`/api/alerts/${alertId}/read`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                }).then(response => {
                    if (response.ok) {
                        this.classList.add('read');
                        this.classList.remove('unread');
                        updateUnreadCount();
                    }
                });
            }
        });
    });
    
    // Initialize Select2 for select elements
    if ($('.select2').length > 0) {
        $('.select2').select2({
            width: '100%',
            theme: 'bootstrap-5'
        });
    }
    
    // Update unread alert count
    function updateUnreadCount() {
        const count = document.querySelectorAll('.alert-item.unread').length;
        const badge = document.getElementById('unread-alert-count');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }
    
    // Update devices table
    function updateDevices() {
        fetch('/api/devices')
            .then(response => response.json())
            .then(data => {
                const tableBody = document.querySelector('#devices-table tbody');
                if (!tableBody) return;
                
                tableBody.innerHTML = '';
                
                data.forEach(device => {
                    const row = document.createElement('tr');
                    
                    const statusClass = device.is_blocked ? 'blocked' : 
                                     (device.status === 'online' ? 'online' : 'offline');
                    
                    const lastSeen = device.last_seen ? new Date(device.last_seen) : null;
                    const lastSeenText = lastSeen ? lastSeen.toLocaleString() : 'Never';
                    
                    row.innerHTML = `
                        <td>${device.name || 'Unknown'}</td>
                        <td>${device.mac}</td>
                        <td>${device.ip || 'N/A'}</td>
                        <td>
                            <span class="status-indicator status-${statusClass}"></span>
                            ${statusClass.charAt(0).toUpperCase() + statusClass.slice(1)}
                        </td>
                        <td>${lastSeenText}</td>
                        <td>
                            ${device.is_blocked ? 
                                '<a href="/admin/unblock_device/' + device.mac + '" class="btn btn-success btn-sm">Unblock</a>' : 
                                '<a href="/admin/block_device/' + device.mac + '" class="btn btn-danger btn-sm">Block</a>'}
                        </td>
                    `;
                    
                    tableBody.appendChild(row);
                });
            });
    }
    
    // Initialize any charts if needed
    if (typeof initCharts === 'function') {
        initCharts();
    }
    
    // Update unread count on page load
    updateUnreadCount();
});

// Function to initialize charts (can be defined in dashboard.js)
function initCharts() {
    // Example chart initialization
    if (document.getElementById('devicesChart')) {
        const ctx = document.getElementById('devicesChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Online', 'Offline', 'Blocked'],
                datasets: [{
                    data: [
                        document.getElementById('online-count').textContent,
                        document.getElementById('offline-count').textContent,
                        document.getElementById('blocked-count').textContent
                    ],
                    backgroundColor: [
                        '#28a745',
                        '#dc3545',
                        '#ffc107'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}