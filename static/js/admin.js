// Admin Panel JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-20px)';
            setTimeout(function() {
                if (message.parentNode) {
                    message.remove();
                }
            }, 300);
        }, 5000);
    });

    // Confirm delete actions
    const deleteForms = document.querySelectorAll('form[onsubmit*="confirm"]');
    deleteForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!confirm('Вы уверены, что хотите удалить эту запись?')) {
                e.preventDefault();
            }
        });
    });

    // Form validation for portfolio form
    const portfolioForm = document.querySelector('.admin-form');
    if (portfolioForm) {
        const imageUrlInput = portfolioForm.querySelector('#image_url');
        if (imageUrlInput) {
            imageUrlInput.addEventListener('blur', function() {
                const url = this.value.trim();
                if (url && !isValidUrl(url)) {
                    this.setCustomValidity('Пожалуйста, введите корректный URL изображения');
                } else {
                    this.setCustomValidity('');
                }
            });
        }
    }

    // Table row highlight
    const tableRows = document.querySelectorAll('.admin-table tbody tr');
    tableRows.forEach(function(row) {
        row.addEventListener('mouseenter', function() {
            row.style.backgroundColor = '#f8f9fa';
        });
        row.addEventListener('mouseleave', function() {
            row.style.backgroundColor = '';
        });
    });

    // Status badge color helper
    const statusBadges = document.querySelectorAll('.status-badge');
    statusBadges.forEach(function(badge) {
        const status = badge.className.match(/status-(\w+)/);
        if (status) {
            badge.setAttribute('data-status', status[1]);
        }
    });

    // Dashboard stat animation
    const statNumbers = document.querySelectorAll('.stat-number');
    statNumbers.forEach(function(stat) {
        const finalValue = parseInt(stat.textContent);
        if (!isNaN(finalValue)) {
            animateValue(stat, 0, finalValue, 1000);
        }
    });

    // Sidebar active link handling
    const navLinks = document.querySelectorAll('.admin-nav-link');
    navLinks.forEach(function(link) {
        link.addEventListener('click', function() {
            navLinks.forEach(l => l.classList.remove('active'));
            // Don't remove active class from current page link
        });
    });

    console.log('Event Decor Admin Panel loaded successfully!');
});

// Helper function to validate URL
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

// Helper function for number animation
function animateValue(obj, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const value = Math.floor(progress * (end - start) + start);
        obj.textContent = value;
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Image preview helper (can be added to portfolio form)
function previewImage(input, previewElement) {
    const preview = document.getElementById(previewElement);
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Export table data as CSV (useful feature for orders)
function exportTableToCSV(tableSelector, filename) {
    const table = document.querySelector(tableSelector);
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');

    rows.forEach(function(row) {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        cols.forEach(function(col) {
            rowData.push('"' + col.textContent.trim().replace(/"/g, '""') + '"');
        });
        csv.push(rowData.join(','));
    });

    downloadCSV(csv.join('\n'), filename);
}

function downloadCSV(csv, filename) {
    const csvFile = new Blob([csv], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}
