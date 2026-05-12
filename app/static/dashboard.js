// Load analytics charts on analytics page
document.addEventListener('DOMContentLoaded', function() {
    const analyticsContainer = document.getElementById('analytics-data');
    if (analyticsContainer) {
        fetch('/analytics/data')
            .then(response => response.json())
            .then(data => {
                // Pie chart
                const pieCtx = document.getElementById('expensePieChart').getContext('2d');
                new Chart(pieCtx, {
                    type: 'pie',
                    data: { labels: data.pie_labels, datasets: [{ data: data.pie_values, backgroundColor: ['#6c5ce7', '#00b894', '#fdcb6e', '#e17055', '#0984e3', '#d63031'] }] },
                    options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
                });
                
                // Bar chart (monthly)
                const barCtx = document.getElementById('monthlyBarChart').getContext('2d');
                new Chart(barCtx, {
                    type: 'bar',
                    data: { labels: data.monthly.map(m => m.month), datasets: [{ label: 'Income', data: data.monthly.map(m => m.income), backgroundColor: '#00b894' }, { label: 'Expense', data: data.monthly.map(m => m.expense), backgroundColor: '#d63031' }] },
                    options: { responsive: true, scales: { y: { beginAtZero: true } } }
                });
            });
    }
});