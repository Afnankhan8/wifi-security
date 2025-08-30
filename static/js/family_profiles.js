// static/js/family_profiles.js
document.addEventListener('DOMContentLoaded', function() {
    // Enable profile
    document.querySelectorAll('.enable-btn').forEach(button => {
        button.addEventListener('click', function() {
            const profileName = this.dataset.profile;
            fetch(`/api/family_profiles/${profileName}/enable`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    location.reload();
                } else {
                    alert('Error enabling profile');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error enabling profile');
            });
        });
    });

    // Disable profile
    document.querySelectorAll('.disable-btn').forEach(button => {
        button.addEventListener('click', function() {
            const profileName = this.dataset.profile;
            fetch(`/api/family_profiles/${profileName}/disable`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    location.reload();
                } else {
                    alert('Error disabling profile');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error disabling profile');
            });
        });
    });

    // Delete profile
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function() {
            const profileName = this.dataset.profile;
            if (confirm(`Are you sure you want to delete the profile "${profileName}"?`)) {
                fetch(`/api/family_profiles/${profileName}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        location.reload();
                    } else {
                        alert('Error deleting profile');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error deleting profile');
                });
            }
        });
    });
});