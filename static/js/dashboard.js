// document.addEventListener('DOMContentLoaded', function() {
//     // ---------------- Dashboard Initialization ----------------
//     initCharts();
//     initializeDashboard();

//     // Real-time updates for dashboard stats and alerts
//     setInterval(updateDashboardStats, 15000); // 15s interval
//     setInterval(updateAlerts, 20000); // 20s interval for alerts

//     // ---------------- Update Dashboard Stats ----------------
//     function updateDashboardStats() {
//         fetch('/api/dashboard/stats')
//             .then(res => res.json())
//             .then(data => {
//                 const { 
//                     total_devices: total, 
//                     online_devices: online, 
//                     blocked_devices: blocked,
//                     family_profiles: familyProfiles // NEW
//                 } = data;

//                 const offline = total - online - blocked;

//                 // Update cards
//                 updateCard('total-devices', total);
//                 updateCard('online-devices', online);
//                 updateCard('blocked-devices', blocked);
//                 updateCard('family-profiles', familyProfiles); // NEW

//                 // Update devices chart
//                 if (window.devicesChart) {
//                     window.devicesChart.data.datasets[0].data = [online, blocked, offline];
//                     window.devicesChart.update();
//                 }

//                 // Optionally update family chart
//                 if (window.familyChart) {
//                     window.familyChart.data.datasets[0].data = [familyProfiles];
//                     window.familyChart.update();
//                 }
//             })
//             .catch(err => console.error('Dashboard stats update failed:', err));
//     }

//     function updateCard(id, value) {
//         const el = document.getElementById(id);
//         if (el) el.textContent = value ?? 0;
//     }

//     // ---------------- Update Alerts ----------------
//     function updateAlerts() {
//         const alertContainer = document.querySelector('.alert-list');
//         if (!alertContainer) return;

//         fetch('/customer/alerts')
//             .then(res => res.text())
//             .then(html => {
//                 alertContainer.innerHTML = html;
//             })
//             .catch(err => console.error('Failed to fetch alerts:', err));
//     }

//     // ---------------- Initialize Charts ----------------
//     function initCharts() {
//         const total = parseIntSafe('total-devices');
//         const online = parseIntSafe('online-devices');
//         const blocked = parseIntSafe('blocked-devices');
//         const offline = total - online - blocked;

//         const familyProfiles = parseIntSafe('family-profiles'); // NEW

//         // Devices chart
//         if (document.getElementById('devicesChart')) {
//             const ctx = document.getElementById('devicesChart').getContext('2d');
//             window.devicesChart = new Chart(ctx, {
//                 type: 'doughnut',
//                 data: {
//                     labels: ['Online', 'Blocked', 'Offline'],
//                     datasets: [{
//                         data: [online, blocked, offline],
//                         backgroundColor: ['#28a745', '#ffc107', '#dc3545'],
//                         borderWidth: 1
//                     }]
//                 },
//                 options: {
//                     responsive: true,
//                     maintainAspectRatio: false,
//                     plugins: {
//                         legend: { position: 'bottom' },
//                         tooltip: {
//                             callbacks: {
//                                 label: ctx => {
//                                     const label = ctx.label || '';
//                                     const value = ctx.raw || 0;
//                                     const totalValue = ctx.dataset.data.reduce((a,b) => a+b,0) || 1;
//                                     const perc = Math.round((value/totalValue)*100);
//                                     return `${label}: ${value} (${perc}%)`;
//                                 }
//                             }
//                         }
//                     }
//                 }
//             });
//         }

//         // Activity chart
//         if (document.getElementById('activityChart')) {
//             const ctx = document.getElementById('activityChart').getContext('2d');
//             window.activityChart = new Chart(ctx, {
//                 type: 'line',
//                 data: {
//                     labels: ['Jan','Feb','Mar','Apr','May','Jun'],
//                     datasets: [{
//                         label: 'Alerts',
//                         data: [12,19,3,5,2,3],
//                         backgroundColor: 'rgba(0,123,255,0.2)',
//                         borderColor: 'rgba(0,123,255,1)',
//                         borderWidth: 1,
//                         tension: 0.4
//                     }]
//                 },
//                 options: {
//                     responsive: true,
//                     maintainAspectRatio: false,
//                     scales: { y: { beginAtZero: true } }
//                 }
//             });
//         }

//         // Optional: Family Profiles chart
//         if (document.getElementById('familyChart')) {
//             const ctx = document.getElementById('familyChart').getContext('2d');
//             window.familyChart = new Chart(ctx, {
//                 type: 'bar',
//                 data: {
//                     labels: ['Family Profiles'],
//                     datasets: [{
//                         label: 'Total',
//                         data: [familyProfiles],
//                         backgroundColor: ['#17a2b8']
//                     }]
//                 },
//                 options: {
//                     responsive: true,
//                     maintainAspectRatio: false
//                 }
//             });
//         }
//     }

//     function parseIntSafe(id) {
//         const el = document.getElementById(id);
//         return el ? parseInt(el.textContent) || 0 : 0;
//     }

//     // ---------------- Other Dashboard Functions ----------------
//     function initializeDashboard() {
//         // Sidebar toggle
//         const sidebarToggle = document.getElementById('sidebarToggle');
//         if (sidebarToggle) {
//             sidebarToggle.addEventListener('click', () => {
//                 document.body.classList.toggle('sidebar-toggled');
//                 const sidebar = document.querySelector('.sidebar');
//                 if (sidebar) sidebar.classList.toggle('toggled');
//             });
//         }

//         // Auto-close bootstrap alerts
//         document.querySelectorAll('.alert-dismissible').forEach(alert => {
//             setTimeout(() => {
//                 const bsAlert = new bootstrap.Alert(alert);
//                 bsAlert.close();
//             }, 5000);
//         });
//     }
// });
