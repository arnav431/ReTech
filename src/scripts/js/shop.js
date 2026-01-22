// Shop functionality
class ShopManager {
    constructor() {
        this.products = [];
        this.categories = [];
        this.filteredProducts = [];
        this.currentCategory = 'all';
        this.searchQuery = '';
        this.cart = JSON.parse(localStorage.getItem('cart')) || [];
        this.favorites = JSON.parse(localStorage.getItem('favorites')) || [];
        
        this.init();
    }

    async init() {
        await this.loadProducts();
        this.setupEventListeners();
        this.renderProducts();
        this.renderCategories();
        this.updateCartCount();
        this.updateFavoritesCount();
    }

    async loadProducts() {
        try {
            const response = await fetch('/api/shop/products');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.products = data.products;
                this.categories = data.categories;
                this.filteredProducts = [...this.products];
            } else {
                console.error('Failed to load products:', data.message);
                // Fallback to static data
                this.loadStaticProducts();
            }
        } catch (error) {
            console.error('Error loading products:', error);
            this.loadStaticProducts();
        }
    }

    loadStaticProducts() {
        // Fallback static data
        this.products = [
            {
                id: "custom-pc-1",
                name: "i7 12th gen with GeForce rtx3080 Custom PC",
                brand: "Custom PC",
                category: "Desktop",
                description: "High-End Gaming Desktop with RTX 3080",
                price: 89999,
                original_price: 159999,
                discount_percentage: 40,
                image: "/src/images/Tower-PC.png",
                condition: "New",
                stock: 5,
                rating: 4.8,
                reviews: 12
            },
            {
                id: "amd-ryzen-5950x",
                name: "AMD Ryzen 9 5950X",
                brand: "AMD",
                category: "Processor",
                description: "High-Performance Desktop Processor",
                price: 31999,
                original_price: 37999,
                discount_percentage: 15,
                image: "/src/images/Amd-Ryzen-9-5950X-Processor.png",
                condition: "New",
                stock: 8,
                rating: 4.9,
                reviews: 25
            }
            // Add more products as needed
        ];
        this.filteredProducts = [...this.products];
    }

    setupEventListeners() {
        // Search functionality
        const searchInput = document.querySelector('.search-bar');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchQuery = e.target.value.toLowerCase();
                this.filterProducts();
            });
        }

        // Category filtering
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('category-btn')) {
                e.preventDefault();
                const category = e.target.dataset.category;
                this.filterByCategory(category);
            }
        });

        // Add to cart functionality
        document.addEventListener('click', (e) => {
            if (e.target.closest('.add-to-cart-btn')) {
                e.preventDefault();
                const productId = e.target.closest('.add-to-cart-btn').dataset.productId;
                this.addToCart(productId);
            }
        });

        // Add to favorites functionality
        document.addEventListener('click', (e) => {
            if (e.target.closest('.add-to-favorites-btn')) {
                e.preventDefault();
                const productId = e.target.closest('.add-to-favorites-btn').dataset.productId;
                this.toggleFavorite(productId);
            }
        });
    }

                filterProducts() {
                this.filteredProducts = this.products.filter(product => {
                    // Normalize category names for comparison (convert spaces to hyphens)
                    const normalizedProductCategory = product.category.toLowerCase().replace(/\s+/g, '-');
                    const matchesCategory = this.currentCategory === 'all' || 
                                          normalizedProductCategory === this.currentCategory.toLowerCase();
                    const matchesSearch = product.name.toLowerCase().includes(this.searchQuery) ||
                                        product.description.toLowerCase().includes(this.searchQuery) ||
                                        product.brand.toLowerCase().includes(this.searchQuery);
                    
                    return matchesCategory && matchesSearch;
                });
                
                this.renderProducts();
            }

    filterByCategory(category) {
        this.currentCategory = category;
        
        // Update active category button
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.classList.remove('bg-[#88d889]', 'text-white');
            btn.classList.add('bg-[#88d889]/10', 'text-[#88d889]');
        });
        
        const activeBtn = document.querySelector(`[data-category="${category}"]`);
        if (activeBtn) {
            activeBtn.classList.remove('bg-[#88d889]/10', 'text-[#88d889]');
            activeBtn.classList.add('bg-[#88d889]', 'text-white');
        }
        
        this.filterProducts();
    }

    renderProducts() {
        const productsContainer = document.querySelector('.product-grid');
        if (!productsContainer) return;

        if (this.filteredProducts.length === 0) {
            productsContainer.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="text-gray-500 dark:text-gray-400">
                        <svg class="mx-auto h-12 w-12 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0112 15c-2.34 0-4.47-.881-6.08-2.33" />
                        </svg>
                        <p class="text-lg font-medium">No products found</p>
                        <p class="text-sm">Try adjusting your search or filter criteria</p>
                    </div>
                </div>
            `;
            return;
        }

        productsContainer.innerHTML = this.filteredProducts.map(product => this.renderProductCard(product)).join('');
    }

    renderProductCard(product) {
        const isFavorite = this.favorites.includes(product.id);
        const isInCart = this.cart.some(item => item.id === product.id);
        
        return `
            <div class="product-card rounded-lg overflow-hidden h-[460px] flex flex-col border-2 dark:border-gray-700 border-gray-200 bg-white dark:bg-gray-800 cursor-pointer hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-[#88d889]" data-product-id="${product.id}" tabindex="0" role="button" onclick="window.location.href='/product/${product.id}'" onkeydown="if(event.key==='Enter'){window.location.href='/product/${product.id}'}">
                <div class="relative">
                    ${product.discount_percentage > 0 ? 
                        `<span class="absolute top-2 right-2 bg-[#88d889] text-white text-xs font-bold px-2 py-1 rounded">-${product.discount_percentage}%</span>` : ''
                    }
                    <img src="${product.image}" alt="${product.name}" class="w-full h-56 object-contain p-4"/>
                </div>
                <div class="p-4 flex-1 flex flex-col justify-between">
                    <div>
                        <div class="text-xs text-[#88d889] font-medium mb-1">${product.brand}</div>
                        <h3 class="font-semibold mb-2 text-gray-800 dark:text-white">${product.name}</h3>
                        <p class="text-sm text-gray-600 dark:text-gray-400">${product.description}</p>
                        <div class="flex items-center mt-2">
                            <div class="flex text-yellow-400">
                                ${this.generateStarRating(product.rating)}
                            </div>
                            <span class="text-xs text-gray-500 dark:text-gray-400 ml-1">(${product.reviews})</span>
                        </div>
                    </div>
                    <div class="flex justify-between items-center mt-4">
                        <div>
                            <span class="text-lg font-bold">₹${product.price.toLocaleString()}</span>
                            ${product.original_price > product.price ? 
                                `<span class="text-sm text-gray-500 dark:text-gray-400 line-through ml-2">₹${product.original_price.toLocaleString()}</span>` : ''
                            }
                        </div>
                        <div class="flex gap-2">
                            <button class="add-to-favorites-btn bg-[#88d889] text-white p-2 rounded-full hover:bg-[#7ac97b] transition-colors ${isFavorite ? 'bg-red-500 hover:bg-red-600' : ''}" data-product-id="${product.id}" title="${isFavorite ? 'Remove from favorites' : 'Add to favorites'}">
                                <i class="fa-solid fa-heart h-5 w-5" fill="${isFavorite ? 'currentColor' : 'none'}" viewBox="0 0 24 24" stroke="currentColor"></i> 
                            </button>
                            <button class="add-to-cart-btn bg-[#88d889] text-white p-2 rounded-full hover:bg-[#7ac97b] transition-colors ${isInCart ? 'bg-blue-500 hover:bg-blue-600' : ''}" data-product-id="${product.id}" title="${isInCart ? 'Already in cart' : 'Add to cart'}">
                                <i class="fa-solid fa-cart-shopping h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    generateStarRating(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 !== 0;
        let stars = '';
        
        for (let i = 0; i < fullStars; i++) {
            stars += '<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/></svg>';
        }
        
        if (hasHalfStar) {
            stars += '<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><defs><linearGradient id="half-star"><stop offset="50%" stop-color="currentColor"/><stop offset="50%" stop-color="transparent"/></linearGradient></defs><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" fill="url(#half-star)"/></svg>';
        }
        
        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
        for (let i = 0; i < emptyStars; i++) {
            stars += '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/></svg>';
        }
        
        return stars;
    }

    renderCategories() {
        const categoriesContainer = document.querySelector('.categories-container');
        if (!categoriesContainer) return;

        const categoryButtons = this.categories.map(category => `
            <button class="category-btn bg-[#88d889]/10 hover:bg-[#88d889]/20 text-[#88d889] px-4 py-2 rounded-full whitespace-nowrap ${category.id === 'all' ? 'bg-[#88d889] text-white' : ''}" data-category="${category.id}">
                <i class="fa-solid ${category.icon} mr-2"></i>
                ${category.name}
            </button>
        `).join('');

        categoriesContainer.innerHTML = categoryButtons;
    }

    addToCart(productId) {
        const product = this.products.find(p => p.id === productId);
        if (!product) return;

        const existingItem = this.cart.find(item => item.id === productId);
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            this.cart.push({
                id: productId,
                name: product.name,
                price: product.price,
                image: product.image,
                quantity: 1
            });
        }

        localStorage.setItem('cart', JSON.stringify(this.cart));
        this.updateCartCount();
        this.showNotification('Product added to cart!', 'success');
        
        // Update button appearance
        const button = document.querySelector(`[data-product-id="${productId}"].add-to-cart-btn`);
        if (button) {
            button.classList.add('bg-blue-500', 'hover:bg-blue-600');
            button.title = 'Already in cart';
        }
    }

    toggleFavorite(productId) {
        const index = this.favorites.indexOf(productId);
        if (index > -1) {
            this.favorites.splice(index, 1);
        } else {
            this.favorites.push(productId);
        }

        localStorage.setItem('favorites', JSON.stringify(this.favorites));
        this.updateFavoritesCount();
        this.showNotification(
            index > -1 ? 'Removed from favorites!' : 'Added to favorites!', 
            'success'
        );
        
        // Re-render products to update favorite buttons
        this.renderProducts();
    }

    updateCartCount() {
        const cartCount = this.cart.reduce((total, item) => total + item.quantity, 0);
        // You can add a cart counter element to display this
        console.log('Cart count:', cartCount);
    }

    updateFavoritesCount() {
        console.log('Favorites count:', this.favorites.length);
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-20 right-4 z-[99999] px-6 py-3 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full ${
            type === 'success' ? 'bg-green-500 text-white' : 'bg-blue-500 text-white'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Flash Sale Countdown Timer
class FlashSaleTimer {
    constructor() {
        this.init();
    }

    init() {
        this.updateTimer();
        setInterval(() => this.updateTimer(), 1000);
    }

    updateTimer() {
        const now = new Date();
        const currentDay = now.getDay(); // 0 = Sunday, 1 = Monday, etc.
        const currentTime = now.getTime();
        
        // Calculate next Sunday at 00:00:00
        let daysUntilSunday = (7 - currentDay) % 7;
        if (daysUntilSunday === 0 && now.getHours() >= 0 && now.getMinutes() >= 0) {
            // It's Sunday and past midnight, so next Sunday is in 7 days
            daysUntilSunday = 7;
        }
        
        const nextSunday = new Date();
        nextSunday.setDate(now.getDate() + daysUntilSunday);
        nextSunday.setHours(0, 0, 0, 0);
        
        // Calculate time until next Sunday
        const timeUntilNextSunday = nextSunday.getTime() - currentTime;
        
        // Check if it's currently Sunday (flash sale day)
        const isSunday = currentDay === 0;
        const isFlashSaleTime = isSunday && now.getHours() >= 0 && now.getHours() < 24;
        
        if (isFlashSaleTime) {
            // Flash sale is live
            this.showFlashSaleLive();
        } else {
            // Show countdown to next flash sale
            this.showCountdown(timeUntilNextSunday);
        }
    }

    showFlashSaleLive() {
        const statusElement = document.getElementById('flash-sale-status');
        const countdownElement = document.getElementById('flash-sale-countdown');
        const liveElement = document.getElementById('flash-sale-live');
        
        if (statusElement) statusElement.textContent = 'Flash sale is live!';
        if (countdownElement) countdownElement.style.display = 'none';
        if (liveElement) liveElement.style.display = 'block';
    }

    showCountdown(timeRemaining) {
        const statusElement = document.getElementById('flash-sale-status');
        const countdownElement = document.getElementById('flash-sale-countdown');
        const liveElement = document.getElementById('flash-sale-live');
        
        if (statusElement) statusElement.textContent = 'Next sale starts in:';
        if (countdownElement) countdownElement.style.display = 'flex';
        if (liveElement) liveElement.style.display = 'none';
        
        // Calculate days, hours, minutes, seconds
        const days = Math.floor(timeRemaining / (1000 * 60 * 60 * 24));
        const hours = Math.floor((timeRemaining % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((timeRemaining % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeRemaining % (1000 * 60)) / 1000);
        
        // Update countdown elements
        const daysElement = document.getElementById('days');
        const hoursElement = document.getElementById('hours');
        const minutesElement = document.getElementById('minutes');
        const secondsElement = document.getElementById('seconds');
        
        if (daysElement) daysElement.textContent = days.toString().padStart(2, '0');
        if (hoursElement) hoursElement.textContent = hours.toString().padStart(2, '0');
        if (minutesElement) minutesElement.textContent = minutes.toString().padStart(2, '0');
        if (secondsElement) secondsElement.textContent = seconds.toString().padStart(2, '0');
    }
}

// Popup positioning helper
function handlePopupPositioning() {
    const popups = document.querySelectorAll('.popup-alignment, .profile-popup');
    
    popups.forEach(popup => {
        const rect = popup.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        
        // Check if popup goes off-screen to the right
        if (rect.right > viewportWidth) {
            popup.style.left = 'auto';
            popup.style.right = '100%';
            popup.style.marginLeft = '0';
            popup.style.marginRight = '8px';
        }
    });
}

// Initialize shop when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ShopManager();
    new FlashSaleTimer();
    
    // Handle popup positioning
    handlePopupPositioning();
    
    // Recalculate on window resize
    window.addEventListener('resize', handlePopupPositioning);
}); 