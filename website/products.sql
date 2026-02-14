-- =========================
-- Table: products
-- =========================
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,        -- e.g., 'Men', 'Women', 'Collections'
    price REAL NOT NULL,           -- numeric price
    color TEXT,                    -- e.g., 'Black', 'White', 'Grey'
    size TEXT,                     -- e.g., 'S', 'M', 'L', 'XL' (could also be comma-separated for multiple sizes)
    image_path TEXT NOT NULL,      -- path to product image
    description TEXT,              -- short description
    popularity INTEGER DEFAULT 0,  -- optional, for sorting by popular
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO products (name, category, price, color, size, image_path, description)
VALUES
('First Collective II Hoodie', 'Men', 1499, 'White', 'M,L,XL', 'images/products/white-hood.png', 'Premium quality hoodie made from organic cotton. Comfortable, stylish, and perfect for any season.'),
('Silk Dress', 'Women', 120, 'Red', 'S,M,L', 'images/products/white-tee.png', 'Elegant silk dress for all occasions.'),
('Classic Tee', 'Men', 320, 'White', 'M,L', 'images/products/white-tee.png', 'Comfortable classic tee made from organic cotton.'),
('Sport Shoes', 'Collections', 150, 'Black', 'M,L,XL', 'images/products/shoes.jpg', 'High-performance sports shoes for everyday use.');