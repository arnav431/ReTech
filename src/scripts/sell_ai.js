// AI Generate Device Specs (AJAX)
document.addEventListener('DOMContentLoaded', function() {
  const aiBtn = document.querySelector('button:has(.fa-wand-magic-sparkles)');
  const descriptionBox = document.querySelector('textarea');
  const form = document.querySelector('form');

  aiBtn?.addEventListener('click', async function() {
    // Collect form data
    const data = {};
    form.querySelectorAll('input, select, textarea').forEach(el => {
      if (el.type === 'radio' && !el.checked) return;
      if (el.name) data[el.name] = el.value;
    });
    // Ensure expected_price is always included and as number
    if (form.querySelector('[name="expected_price"]')) {
      data.expected_price = parseFloat(form.querySelector('[name="expected_price"]').value || 0);
    }
    // Also collect original_price
    if (form.querySelector('[name="original_price"]')) {
      data.original_price = parseFloat(form.querySelector('[name="original_price"]').value || 0);
    }
    // Fallbacks for unnamed fields (by order in form)
    const fallbackMap = [
      'category','brand','model','condition','color','storage','description','device_age'
    ];
    let i = 0;
    for (const el of form.querySelectorAll('select, input[type=text], textarea, input[type=range]')) {
      if (!el.name && fallbackMap[i]) data[fallbackMap[i++]] = el.value;
    }
    // Send to backend
    aiBtn.disabled = true;
    aiBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';
    try {
      const res = await fetch('/api/generate-specs', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        credentials: 'include',
        body: JSON.stringify(data)
      });

      const contentType = res.headers.get('content-type') || '';
      if (res.status === 401) {
        throw new Error('Please log in to use AI generate.');
      }
      if (!contentType.includes('application/json')) {
        throw new Error('Unexpected response from server.');
      }

      const result = await res.json();
      if (result.status === 'success') {
        descriptionBox.value = result.description;
      } else {
        alert(result.message || 'Failed to generate specs.');
      }
    } catch(e) {
      alert('Error: ' + e.message);
    }
    aiBtn.disabled = false;
    aiBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> AI Generate';
  });
});
