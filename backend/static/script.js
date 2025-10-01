// Example script for user interactions, form handling, or other UI behavior

// For example, confirm before logout if needed
document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', (e) => {
        if (!confirm('Are you sure you want to log out?')) {
          e.preventDefault();
        } else {
          // You can also make a logout API call here if needed
        }
      });
    }
  
    // Example: Password confirmation validation on register page
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
      registerForm.addEventListener('submit', (e) => {
        const password = document.getElementById('password');
        const confirmPassword = document.getElementById('confirm_password');
        if (password.value !== confirmPassword.value) {
          e.preventDefault();
          alert('Passwords do not match!');
        }
      });
    }
  });