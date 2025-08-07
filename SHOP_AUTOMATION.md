# ReTech Shop Automation System

## Overview

The ReTech shop has been completely automated with a data-driven approach. All product information is now stored in a centralized JSON file and dynamically loaded when the shop page is accessed.

## Features

### 🛍️ Dynamic Product Loading
- **Centralized Data Storage**: All product information is stored in `src/data/products.json`
- **Real-time Updates**: Products are loaded dynamically from the JSON file
- **Fallback System**: If the JSON file is unavailable, the system falls back to Firebase or static data

### 🔍 Advanced Filtering & Search
- **Category Filtering**: Filter products by category (Desktop, Processor, Motherboard, etc.)
- **Real-time Search**: Search products by name, description, or brand
- **Dynamic Categories**: Categories are automatically generated from product data

### 🛒 Enhanced Shopping Features
- **Add to Cart**: Products can be added to cart with local storage persistence
- **Favorites System**: Users can add/remove products from favorites
- **Star Ratings**: Dynamic star rating display for each product
- **Price Display**: Shows current price and original price with discount percentage

### 📊 Admin Management
- **Product Management Interface**: Admin panel at `/admin/products`
- **Add New Products**: Form to add new products with all necessary fields
- **Delete Products**: Remove products from the catalog
- **Product Table**: View all products in a sortable table

## File Structure

```
src/
├── data/
│   └── products.json          # Central product database
├── scripts/
│   └── js/
│       └── shop.js           # Shop functionality JavaScript
├── templates/
│   ├── shop.html             # Updated shop page
│   └── admin/
│       └── products.html     # Admin interface
└── images/                   # Product images
```

## Product Data Structure

Each product in `products.json` contains:

```json
{
  "id": "unique-product-id",
  "name": "Product Name",
  "brand": "Brand Name",
  "category": "Category",
  "description": "Product description",
  "price": 9999,
  "original_price": 12999,
  "discount_percentage": 23,
  "image": "/src/images/product.png",
  "condition": "New",
  "stock": 10,
  "rating": 4.5,
  "reviews": 25,
  "specs": {
    "key": "value"
  },
  "tags": ["tag1", "tag2"]
}
```

## API Endpoints

### Shop Products
- `GET /api/shop/products` - Get all products with categories

### Admin Management
- `POST /api/admin/products` - Add new product
- `DELETE /api/admin/products/<id>` - Delete product

## Usage

### For Users
1. Navigate to `/shop`
2. Use the search bar to find products
3. Filter by category using the category buttons
4. Add products to cart or favorites
5. View product details and ratings

### For Administrators
1. Navigate to `/admin/products`
2. Use the form to add new products
3. View all products in the table
4. Delete products as needed

## Technical Implementation

### JavaScript Classes

#### ShopManager
- Handles product loading and filtering
- Manages cart and favorites
- Renders product cards dynamically
- Handles search and category filtering

#### AdminManager
- Manages product administration
- Handles form submissions
- Manages product table display
- Handles product deletion

### Backend Integration

The system integrates with both:
- **JSON File Storage**: Primary data source
- **Firebase**: Fallback data source
- **Static Data**: Emergency fallback

## Benefits

1. **Scalability**: Easy to add new products without code changes
2. **Maintainability**: Centralized data management
3. **Performance**: Fast loading with client-side rendering
4. **User Experience**: Smooth interactions with real-time updates
5. **Admin Control**: Easy product management interface

## Future Enhancements

- [ ] Product editing functionality
- [ ] Bulk product import/export
- [ ] Advanced filtering (price range, rating, etc.)
- [ ] Product variants (size, color, etc.)
- [ ] Inventory management
- [ ] Order processing integration

## Setup Instructions

1. Ensure the `src/data/products.json` file exists
2. Add product images to `src/images/`
3. Update product image paths in the JSON file
4. Access the shop at `/shop`
5. Access admin panel at `/admin/products`

## Troubleshooting

### Products Not Loading
- Check if `src/data/products.json` exists and is valid JSON
- Verify image paths in the JSON file
- Check browser console for JavaScript errors

### Admin Panel Issues
- Ensure you're logged in (admin panel requires authentication)
- Check if the JSON file is writable
- Verify all required fields are filled in the form

### Image Display Issues
- Verify image files exist in `src/images/`
- Check image paths in the JSON file
- Ensure image files are accessible via the web server 