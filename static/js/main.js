document.addEventListener('DOMContentLoaded', function() {
    
    // --- CSRF Token Helper ---
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // --- Dark Mode Toggle ---
    const darkModeToggle = document.getElementById('darkModeToggle');
    const body = document.getElementById('body');
    
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Toggle body class
            body.classList.toggle('dark-mode');
            
            // Update icon
            const icon = this.querySelector('i');
            if (body.classList.contains('dark-mode')) {
                icon.classList.remove('bi-moon-stars-fill');
                icon.classList.add('bi-sun-fill');
                // Save preference
                localStorage.setItem('darkMode', 'true');
                document.cookie = "dark_mode=true; path=/; max-age=31536000"; // 1 year
            } else {
                icon.classList.remove('bi-sun-fill');
                icon.classList.add('bi-moon-stars-fill');
                // Save preference
                localStorage.setItem('darkMode', 'false');
                document.cookie = "dark_mode=false; path=/; max-age=31536000";
            }
        });
    }

    // --- Like Post (AJAX) ---
    const likeButtons = document.querySelectorAll('.like-btn');
    
    likeButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const postId = this.dataset.postId;
            const icon = this.querySelector('i');
            const card = this.closest('.post-card');
            const countSpan = card.querySelector('.likes-count');
            
            fetch(`/post/${postId}/like/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json'
                },
            })
            .then(response => {
                if(response.ok) return response.json();
                throw new Error('Network response was not ok.');
            })
            .then(data => {
                // Update count
                countSpan.textContent = data.total_likes;
                
                // Update styling & icon
                if (data.liked) {
                    this.classList.add('liked');
                    icon.classList.remove('bi-heart', 'text-secondary');
                    icon.classList.add('bi-heart-fill', 'text-danger');
                    // Add animation class
                    icon.classList.add('like-animation');
                    setTimeout(() => icon.classList.remove('like-animation'), 300);
                } else {
                    this.classList.remove('liked');
                    icon.classList.remove('bi-heart-fill', 'text-danger');
                    icon.classList.add('bi-heart', 'text-secondary');
                }
            })
            .catch(error => console.error('Error toggling like:', error));
        });
    });

    // --- Follow User (AJAX) ---
    const followButtons = document.querySelectorAll('.follow-btn');
    
    followButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const username = this.dataset.username;
            
            fetch(`/profile/${username}/follow/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json'
                },
            })
            .then(response => {
                if(response.ok) return response.json();
                throw new Error('Network response was not ok.');
            })
            .then(data => {
                // Update button text and style
                if (data.is_following) {
                    this.textContent = 'Unfollow';
                    this.classList.remove('btn-primary', 'btn-gradient');
                    this.classList.add('btn-outline-secondary');
                } else {
                    this.textContent = 'Follow';
                    this.classList.remove('btn-outline-secondary');
                    this.classList.add('btn-primary', 'btn-gradient');
                }
                
                // Update follower count on profile page if it exists
                const followersCountEl = document.getElementById('followers-count');
                if (followersCountEl) {
                    followersCountEl.textContent = data.followers_count;
                }
            })
            .catch(error => console.error('Error toggling follow:', error));
        });
    });

    // --- Image Upload Preview ---
    const imageInputs = document.querySelectorAll('input[type="file"]');
    
    imageInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    // Try to find specific preview container or fallback to generic
                    let preview = document.getElementById('image-preview');
                    let container = document.getElementById('image-preview-container');
                    let currentContainer = document.getElementById('current-image-container');
                    
                    if (preview) {
                        preview.src = e.target.result;
                        if (container) {
                            container.classList.remove('d-none');
                        }
                        if (currentContainer) {
                            currentContainer.classList.add('d-none'); // Hide old image
                        }
                    }
                }
                
                reader.readAsDataURL(this.files[0]);
            }
        });
    });

    // --- Auto-hide Alerts ---
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    if (alerts.length > 0) {
        setTimeout(() => {
            alerts.forEach(alert => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            });
        }, 4000);
    }
    
    // --- Navbar Scroll Effect ---
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }
    });
});
