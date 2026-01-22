// Product page dynamic rendering
window.addEventListener('DOMContentLoaded', function() {
  // Get product data from template context
  const product = window.productData || {};

  // If product is injected as JSON, use it
  if (!product.id && window.PRODUCT_JSON) {
    Object.assign(product, window.PRODUCT_JSON);
  }

  // Set fields
  document.getElementById('product-image').src = product.image || '/src/images/default-product.png';
  document.getElementById('product-name').textContent = product.name || '';
  document.getElementById('product-brand').textContent = product.brand || '';
  document.getElementById('product-price').textContent = product.price ? `₹${product.price}` : '';
  document.getElementById('product-original-price').textContent = product.original_price ? `₹${product.original_price}` : '';
  document.getElementById('product-discount').textContent = product.discount_percentage ? `-${product.discount_percentage}%` : '';
  document.getElementById('product-rating').textContent = product.rating || '0';
  document.getElementById('product-reviews').textContent = product.reviews || '0';
  document.getElementById('product-condition').textContent = product.condition || '';
  document.getElementById('product-stock').textContent = product.stock || '';

  // Tags
  const tagsDiv = document.getElementById('product-tags');
  if (Array.isArray(product.tags)) {
    tagsDiv.innerHTML = '';
    product.tags.forEach(tag => {
      const span = document.createElement('span');
      span.className = 'bg-gray-200 text-gray-700 px-2 py-1 rounded text-xs mr-1 mb-1';
      span.textContent = tag;
      tagsDiv.appendChild(span);
    });
  }

  // Description
  document.getElementById('product-description').textContent = product.description || '';

  // Specs
  const specsList = document.getElementById('product-specs');
  if (product.specs && typeof product.specs === 'object') {
    specsList.innerHTML = '';
    Object.entries(product.specs).forEach(([key, value]) => {
      if (value) {
        const li = document.createElement('li');
        li.textContent = `${key.charAt(0).toUpperCase() + key.slice(1)}: ${value}`;
        specsList.appendChild(li);
      }
    });
  }
});
