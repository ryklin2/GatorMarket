-- Create database
CREATE DATABASE IF NOT EXISTS gator_market;
USE gator_market;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    verification_status ENUM('unverified', 'verified') DEFAULT 'unverified',
    verification_token VARCHAR(255),
    verification_token_created_at DATETIME,
    phone_number VARCHAR(15),
    profile_picture_url VARCHAR(255),
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    user_role ENUM('user', 'moderator', 'admin') DEFAULT 'user',
    account_status ENUM('active', 'inactive/banned', 'deleted') DEFAULT 'active',
    bookmarked_products JSON DEFAULT NULL
);

-- Categories for organizing products
CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- Main produc listing table
CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    `condition` VARCHAR(50) NOT NULL,
    category_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('active', 'sold', 'deleted') DEFAULT 'active',
    approval_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- images associated with each product
CREATE TABLE IF NOT EXISTS product_images (
    image_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    image_url VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

-- product review system
CREATE TABLE IF NOT EXISTS reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    seller_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES users(user_id)
);

-- conversations initiated around specific product
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    subject VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    status ENUM('active', 'archived', 'completed') DEFAULT 'active',
    meeting_details TEXT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- link users to convos
CREATE TABLE IF NOT EXISTS conversation_participants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    user_id INT NOT NULL,
    role ENUM('buyer', 'seller') NOT NULL,
    last_read_at TIMESTAMP NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE KEY unique_participant (conversation_id, user_id)
);

-- messages exchanged in a convo
CREATE TABLE IF NOT EXISTS messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    sender_id INT NOT NULL,
    message_text TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    attachment_url VARCHAR(255) NULL,
    message_type ENUM('text', 'reminder_proposal', 'reminder_update', 'system') DEFAULT 'text',
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
    FOREIGN KEY (sender_id) REFERENCES users(user_id)
);

-- tracks products bookmarked by users (wishlisted items)
CREATE TABLE IF NOT EXISTS wishlist_tracking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notified BOOLEAN DEFAULT FALSE,
    archived BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    UNIQUE (user_id, product_id)
);

-- tracks users reporting other users
CREATE TABLE IF NOT EXISTS user_reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    reporter_id INT NOT NULL,
    reported_user_id INT NOT NULL,
    reason TEXT NOT NULL,
    additional_comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'reviewed', 'resolved') DEFAULT 'pending',
    FOREIGN KEY (reporter_id) REFERENCES users(user_id),
    FOREIGN KEY (reported_user_id) REFERENCES users(user_id)
);

-- create app-specific user for db access
CREATE USER IF NOT EXISTS 'csc648user'@'%' IDENTIFIED BY 'Csc648_P@ss!';
GRANT ALL PRIVILEGES ON gator_market.* TO 'csc648user'@'%';
FLUSH PRIVILEGES;

INSERT INTO categories (name) VALUES
('Computers'), ('Phones/Tablets'), ('Tech Accessories'), ('Books'), ('Clothes/Furniture');

INSERT INTO users (username, password_hash, email, first_name, last_name, user_role)
VALUES ('testuser', 'hashedpassword', 'test@example.com', 'Test', 'User', 'user');

INSERT INTO users (username, password_hash, email, first_name, last_name, user_role)
VALUES ('admin', '$2b$12$1xxxxxxxxxxxxxxxxxxxxuZLbwxnpY0o58unSvAPxnKCCGvt.PW2', 'admin@example.com', 'Admin', 'User', 'admin');

INSERT INTO users (username, password_hash, email, first_name, last_name, user_role)
VALUES ('admin2', 'Admin123!@#', 'admin@sfsu.edu', 'Admin', 'User', 'admin');

INSERT INTO products (user_id, name, description, price, `condition`, category_id, approval_status)
VALUES 
(1, 'MacBook Pro 13"', 'Used MacBook Pro 13-inch, great condition with charger included.', 700.00, 'Used - Good', 1, 'approved'),
(1, 'Dell XPS 15', 'Powerful laptop with Intel i7 processor and 16GB RAM.', 950.00, 'Used - Good', 1, 'approved'),
(1, 'Lenovo ThinkPad', 'Business laptop with durable build and fast performance.', 600.00, 'Used - Good', 1, 'approved'),

(1, 'Samsung Galaxy S22', '128 GB Green, minor scratches, great camera.', 475.00, 'Used - Acceptable', 2, 'approved'),
(1, 'iPhone 12', '128GB Black, minor scratches, fully functional.', 500.00, 'Used - Good', 2, 'approved'),
(1, 'iPad Mini', '10.5-inch tablet with stylus.', 300.00, 'Used - Acceptable', 2, 'approved'),

(1, 'Mechanical Keyboard', 'Logitech wireless mouse, lightly used.', 85.00, 'Used - Good', 3, 'approved'),
(1, 'Gaming Monitor', 'Seagate hard drive for extra storage.', 240.00, 'Used - Good', 3, 'approved'),
(1, 'AirPods Pro', 'With case, minor scratches.', 110.00, 'Used - Good', 3, 'approved'),

(1, 'Organic Chemistry Textbook', 'OChem textbook, CHEM 349, lightly used.', 45.00, 'Used - Good', 4, 'approved'),
(1, 'Crack The Coding Interview', 'PSY 100 textbook, good condition.', 65.00, 'Like New', 4, 'approved'),
(1, 'Data Structures & Algorithms', 'CS textbook, annotated.', 30.00, 'Used - Good', 4, 'approved'),

(1, 'SFSU Hoodie', 'Size M, worn once.', 25.00, 'Like New', 5, 'approved'),
(1, 'Dorm Chair', 'Comfortable dorm chair in great shape.', 20.00, 'Used - Good', 5, 'approved'),
(1, 'SFSU T-Shirt', 'Official SFSU merchandise, Size L.', 30.00, 'Brand New', 5, 'approved'),
(1, 'Desk Light', 'Solid wood desk, slightly worn.', 25.00, 'Used - Acceptable', 5, 'approved');

INSERT INTO product_images (product_id, image_url) VALUES
(1, '/static/images/macbook.jpg'),
(2, '/static/images/dellxps.jpg'),
(3, '/static/images/thinkpad.jpg'),

(4, '/static/images/samsung.jpg'),
(5, '/static/images/iphone.jpg'),
(6, '/static/images/ipad.jpg'),

(7, '/static/images/keyboard.jpg'),
(8, '/static/images/monitor.jpg'),
(9, '/static/images/airpods.jpg'),

(10, '/static/images/ochem.jpg'),
(11, '/static/images/interviewbook.jpg'),
(12, '/static/images/dsabook.jpg'),

(13, '/static/images/hoodie.jpg'),
(14, '/static/images/chair.jpg'),
(15, '/static/images/shirt.jpg'),
(16, '/static/images/desk_light.jpg');


INSERT INTO reviews (seller_id, rating, comment, created_at) VALUES
(1, 5, 'Amazing seller! Highly recommended.', NOW()),
(1, 4, 'Good communication and fast shipping.', NOW()),
(1, 5, 'Product exactly as described. Thank you!', NOW()),
(1, 3, 'Item was fine, but shipping was delayed.', NOW());

INSERT INTO conversations (product_id, subject, status)
SELECT 1, 'Interested in your product', 'active' FROM products WHERE product_id = 1 LIMIT 1;

INSERT INTO conversation_participants (conversation_id, user_id, role)
SELECT 1, 1, 'seller' FROM conversations WHERE conversation_id = 1 LIMIT 1;

INSERT INTO conversation_participants (conversation_id, user_id, role)
SELECT 1, (SELECT user_id FROM users WHERE user_id != 1 LIMIT 1), 'buyer' 
FROM conversations WHERE conversation_id = 1 LIMIT 1;

INSERT INTO messages (conversation_id, sender_id, message_text)
SELECT 1, (SELECT user_id FROM users WHERE user_id != 1 LIMIT 1), 'Hi, I am interested in your product. Is it still available?'
FROM conversations WHERE conversation_id = 1 LIMIT 1;