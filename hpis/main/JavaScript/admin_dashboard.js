function showTab(tabName) {
  // Hide all tabs
  document.querySelectorAll('.tab-content').forEach(tab => {
    tab.style.display = 'none';
  });
  // Remove active from all buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  // Show selected tab
  document.getElementById(tabName).style.display = 'block';
  // Add active to clicked button
  event.target.classList.add('active');
}
