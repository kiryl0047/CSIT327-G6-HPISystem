function showSection(sectionId, event) {
  if (event) {
    event.preventDefault();
  }

  // Hide all sections
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));

  // Show selected section
  document.getElementById(sectionId).classList.add('active');

  // Update sidebar active link
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  event.target.classList.add('active');
}

function validatePassword() {
  const pwd = document.getElementById('newPassword').value;

  document.getElementById('req-length').classList.toggle('valid', pwd.length >= 8);
  document.getElementById('req-uppercase').classList.toggle('valid', /[A-Z]/.test(pwd));
  document.getElementById('req-number').classList.toggle('valid', /\d/.test(pwd));
  document.getElementById('req-special').classList.toggle('valid', /[!@#$%^&*]/.test(pwd));
}

function showDeleteAccountModal() {
  document.getElementById('deleteAccountModal').classList.add('active');
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.remove('active');
}

// Close modal when clicking outside
document.querySelectorAll('.modal').forEach(modal => {
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.classList.remove('active');
    }
  });
});
