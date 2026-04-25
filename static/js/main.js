// Main Website JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');

    if (mobileMenuBtn && navLinks) {
        mobileMenuBtn.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Form validation
    const contactForm = document.querySelector('.contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            const phoneInput = this.querySelector('#phone');
            const emailInput = this.querySelector('#email');
            
            // Phone validation (basic)
            if (phoneInput && phoneInput.value) {
                const phonePattern = /^[\d\s\+\-\(\)]+$/;
                if (!phonePattern.test(phoneInput.value)) {
                    e.preventDefault();
                    alert('Пожалуйста, введите корректный номер телефона');
                    phoneInput.focus();
                    return;
                }
            }

            // Email validation
            if (emailInput && emailInput.value) {
                const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailPattern.test(emailInput.value)) {
                    e.preventDefault();
                    alert('Пожалуйста, введите корректный email адрес');
                    emailInput.focus();
                    return;
                }
            }
        });
    }

    // Auto-hide flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-20px)';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });

    // Navbar scroll effect
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.style.boxShadow = '0 4px 20px rgba(0,0,0,0.15)';
            } else {
                navbar.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
            }
        });
    }

    // Portfolio item click - show details
    const portfolioItems = document.querySelectorAll('.portfolio-item');
    portfolioItems.forEach(function(item) {
        item.addEventListener('click', function() {
            // Could add modal or navigation here
            console.log('Portfolio item clicked');
        });
    });

    console.log('Event Decor website loaded successfully!');
});

// Phone mask input (optional enhancement)
function applyPhoneMask(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length > 0) {
        value = '+' + value;
        if (value.length > 1) {
            value = value.substring(0, 2) + ' ' + value.substring(2);
        }
        if (value.length > 6) {
            value = value.substring(0, 6) + ' ' + value.substring(6, 9) + '-' + value.substring(9, 11) + '-' + value.substring(11, 13);
        } else if (value.length > 4) {
            value = value.substring(0, 6) + ' ' + value.substring(6);
        }
    }
    input.value = value;
}
