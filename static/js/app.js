// Main app script for LinkedIn Company Scraper

document.addEventListener('DOMContentLoaded', function() {
    // Handle form submission with loading state
    const scraperForm = document.querySelector('form[action="/scrape"]');
    if (scraperForm) {
        scraperForm.addEventListener('submit', function(event) {
            const submitButton = this.querySelector('button[type="submit"]');
            
            // Show loading state
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Scraping...';
            submitButton.disabled = true;
            
            // Add a hidden field with timestamp
            const timestampField = document.createElement('input');
            timestampField.type = 'hidden';
            timestampField.name = 'timestamp';
            timestampField.value = new Date().toISOString();
            this.appendChild(timestampField);
        });
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers for company descriptions
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, {
            trigger: 'focus',
            html: true
        });
    });
    
    // Handle filter input for results table
    const filterInput = document.getElementById('filterResults');
    if (filterInput) {
        filterInput.addEventListener('input', function() {
            const filterValue = this.value.toLowerCase();
            const rows = document.querySelectorAll('.table tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(filterValue)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Autofocus on search input when modal is shown
    const searchModal = document.getElementById('searchModal');
    if (searchModal) {
        searchModal.addEventListener('shown.bs.modal', function () {
            document.getElementById('filterResults').focus();
        });
    }
});
