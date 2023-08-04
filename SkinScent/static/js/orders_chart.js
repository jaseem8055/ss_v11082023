$(document).ready(function() {
    // Fetch data from Django views using jQuery AJAX
    $.ajax({
        url: '/adminpanel/orders_data/',  // Replace this URL with your Django API endpoint
        method: 'GET',
        dataType: 'json',
        success: function(data) {
            const dates = data.dates;  // Array of date labels (e.g., ["2023-07-25", "2023-07-26", ...])
            const orderCounts = data.order_counts;  // Array of order counts per date (e.g., [5, 10, ...])

            // Use Moment.js to parse the dates
            const formattedDates = dates.map(date => moment(date));

            // Create the chart using Chart.js
            const ctx = document.getElementById('ordersChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: formattedDates,
                    datasets: [{
                        label: 'Number of Orders',
                        data: orderCounts,
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1,
                    }],
                },
                options: {
                    responsive: true,
                    scales: {
                        x: {
                            type: 'time',  // Use time scale
                            time: {
                                unit: 'day', // Display data per day, you can change this to 'week', 'month', etc.
                                displayFormats: {
                                    day: 'MMM D', // Format for displaying day labels (e.g., "Jul 26")
                                }
                            },
                            title: {
                                display: true,
                                text: 'Date',
                            },
                        },
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Number of Orders',
                            },
                        },
                    },
                },
            }); //new chart
        }, //success
        error: function(error) {
            console.error('Failed to fetch data:', error);
        }
    });
});
