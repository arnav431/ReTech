// Handle Submit Listing button
// Sends pending product in session to backend for final save

document.addEventListener('DOMContentLoaded', function() {
  const submitBtn = document.getElementById('submit-listing-btn');
  submitBtn?.addEventListener('click', async function() {
    submitBtn.disabled = true;
    submitBtn.innerHTML = 'Submitting...';
    try {
      const res = await fetch('/api/submit-listing', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: '{}'
      });
      const result = await res.json();
      if(result.status === 'success') {
        alert('Listing submitted successfully!');
        window.location.href = '/shop';
      } else {
        alert(result.message || 'Failed to submit listing.');
      }
    } catch(e) {
      alert('Error: ' + e.message);
    }
    submitBtn.disabled = false;
    submitBtn.innerHTML = 'Submit Listing';
  });
});
