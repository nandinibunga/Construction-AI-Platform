document.addEventListener('DOMContentLoaded', function() {
    // Table Search Functionality
    const searchInput = document.getElementById('searchInput');
    if(searchInput) {
        searchInput.addEventListener('input', filterTable);
    }

    // Initialize Charts
    initializeCharts();

    // Timeline Animation
    animateTimelines();
});

function filterTable(e) {
    const filter = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
    });
}

function initializeCharts() {
    // Risk Distribution Chart
    const ctx = document.getElementById('riskChart')?.getContext('2d');
    if(ctx) {
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['High Risk', 'Medium Risk', 'Low Risk'],
                datasets: [{
                    data: [30, 50, 20],
                    backgroundColor: ['#e74a3b', '#f6c23e', '#1cc88a']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: { enabled: false }
                }
            }
        });
    }
}

function animateTimelines() {
    const timelines = document.querySelectorAll('.timeline-bar');
    timelines.forEach(timeline => {
        timeline.style.opacity = '0';
        setTimeout(() => {
            timeline.style.transition = 'opacity 0.5s ease-out';
            timeline.style.opacity = '1';
        }, 100);
    });
}

// Real-time Updates
setInterval(() => {
    fetch('/api/projects')
        .then(response => response.json())
        .then(data => updateCharts(data));
}, 300000);

function updateCharts(data) {
    // Implement chart update logic here
}
