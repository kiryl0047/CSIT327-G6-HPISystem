// Appointment Type Chart (Pie)
const appointmentTypeCtx = document.getElementById('appointmentTypeChart').getContext('2d');
new Chart(appointmentTypeCtx, {
  type: 'doughnut',
  data: {
    labels: ['Consultation', 'Follow-up', 'Checkup', 'Emergency'],
    datasets: [{
      data: [425, 312, 285, 225],
      backgroundColor: ['#1c2f6c', '#2e7d32', '#f57c00', '#d32f2f']
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom'
      }
    }
  }
});

// Appointment Trend Chart (Line)
const trendCtx = document.getElementById('appointmentTrendChart').getContext('2d');
new Chart(trendCtx, {
  type: 'line',
  data: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov'],
    datasets: [{
      label: 'Appointments',
      data: [980, 1050, 1100, 1150, 1200, 1180, 1220, 1250, 1230, 1210, 1247],
      borderColor: '#1c2f6c',
      backgroundColor: 'rgba(28, 47, 108, 0.1)',
      tension: 0.4,
      fill: true
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: true
      }
    }
  }
});

// Status Chart (Bar)
const statusCtx = document.getElementById('statusChart').getContext('2d');
new Chart(statusCtx, {
  type: 'bar',
  data: {
    labels: ['Pending', 'Assigned', 'Confirmed', 'Completed', 'Cancelled'],
    datasets: [{
      label: 'Count',
      data: [45, 82, 156, 892, 72],
      backgroundColor: ['#f57c00', '#1976d2', '#2e7d32', '#1c2f6c', '#d32f2f']
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: true
      }
    }
  }
});

// Department Chart (Horizontal Bar)
const departmentCtx = document.getElementById('departmentChart').getContext('2d');
new Chart(departmentCtx, {
  type: 'bar',
  data: {
    labels: ['Cardiology', 'General Practice', 'Emergency', 'Pediatrics', 'Orthopedics'],
    datasets: [{
      label: 'Appointments',
      data: [342, 458, 225, 189, 156],
      backgroundColor: '#1c2f6c'
    }]
  },
  options: {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      x: {
        beginAtZero: true
      }
    }
  }
});

function refreshData() {
  alert('Refreshing data with selected filters...');
  // In production, this would fetch new data from the server
}
