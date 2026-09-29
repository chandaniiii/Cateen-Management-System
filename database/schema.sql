-- Campus Canteen Management System
-- MySQL Relational Database Schema & Sample Seed Data

-- 1. Create Database if not exists
CREATE DATABASE IF NOT EXISTS `canteen_management` 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `canteen_management`;

-- 2. Drop existing tables in reverse foreign-key order
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `reviews`;
DROP TABLE IF EXISTS `order_items`;
DROP TABLE IF EXISTS `orders`;
DROP TABLE IF EXISTS `menu_items`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `users`;
SET FOREIGN_KEY_CHECKS = 1;

-- 3. Users Table
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(120) NOT NULL,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `password_hash` VARCHAR(256) NOT NULL,
    `student_id` VARCHAR(50) NULL,
    `phone` VARCHAR(20) NULL,
    `role` ENUM('student', 'staff', 'admin') NOT NULL DEFAULT 'student',
    `status` ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_users_email` (`email`),
    INDEX `idx_users_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Categories Table
CREATE TABLE `categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `description` TEXT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Menu Items Table
CREATE TABLE `menu_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `category_id` INT NOT NULL,
    `name` VARCHAR(120) NOT NULL,
    `description` TEXT NULL,
    `price` DECIMAL(10, 2) NOT NULL,
    `image` VARCHAR(255) NULL,
    `stock` INT NOT NULL DEFAULT 0,
    `minimum_stock` INT NOT NULL DEFAULT 5,
    `is_available` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_menu_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX `idx_menu_category` (`category_id`),
    INDEX `idx_menu_available` (`is_available`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Orders Table
CREATE TABLE `orders` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `total_amount` DECIMAL(10, 2) NOT NULL,
    `status` ENUM('pending', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled') NOT NULL DEFAULT 'pending',
    `payment_method` ENUM('cash', 'esewa', 'khalti', 'qr') NOT NULL DEFAULT 'cash',
    `payment_status` ENUM('pending', 'completed', 'failed') NOT NULL DEFAULT 'pending',
    `pickup_time` VARCHAR(50) NOT NULL DEFAULT 'ASAP',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_order_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX `idx_order_user` (`user_id`),
    INDEX `idx_order_status` (`status`),
    INDEX `idx_order_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Order Items Table
CREATE TABLE `order_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_id` INT NOT NULL,
    `menu_item_id` INT NOT NULL,
    `quantity` INT NOT NULL,
    `price` DECIMAL(10, 2) NOT NULL,
    CONSTRAINT `fk_item_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_item_menu` FOREIGN KEY (`menu_item_id`) REFERENCES `menu_items` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX `idx_item_order` (`order_id`),
    INDEX `idx_item_menu` (`menu_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Reviews Table
CREATE TABLE `reviews` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `menu_item_id` INT NOT NULL,
    `order_id` INT NULL,
    `rating` INT NOT NULL CHECK (`rating` >= 1 AND `rating` <= 5),
    `comment` TEXT NULL,
    `is_visible` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_review_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_review_menu` FOREIGN KEY (`menu_item_id`) REFERENCES `menu_items` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_review_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX `idx_review_menu` (`menu_item_id`),
    INDEX `idx_review_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =======================================================
-- 9. Sample Seed Data
-- =======================================================

-- Users (Initial Seed Data)
INSERT INTO `users` (`id`, `name`, `email`, `password_hash`, `student_id`, `phone`, `role`, `status`, `created_at`) VALUES
(1, 'Admin User', 'admin@canteen.com', 'scrypt:32768:8:1$u7F5G1Vw$db9bfef0fca02d0cf3b08cb0fc1bc2e8bf53d2bf3e8d7ef26f30a9960ff570dcf4564c7816eb883833f44384dbe8a74e50bb7f9754f7a39d8ebbc5a2c4e3a479', NULL, '9801111111', 'admin', 'active', NOW()),
(2, 'Canteen Staff', 'staff@canteen.com', 'scrypt:32768:8:1$u7F5G1Vw$db9bfef0fca02d0cf3b08cb0fc1bc2e8bf53d2bf3e8d7ef26f30a9960ff570dcf4564c7816eb883833f44384dbe8a74e50bb7f9754f7a39d8ebbc5a2c4e3a479', NULL, '9802222222', 'staff', 'active', NOW()),
(3, 'Aayush Sharma', 'student@college.com', 'scrypt:32768:8:1$u7F5G1Vw$db9bfef0fca02d0cf3b08cb0fc1bc2e8bf53d2bf3e8d7ef26f30a9960ff570dcf4564c7816eb883833f44384dbe8a74e50bb7f9754f7a39d8ebbc5a2c4e3a479', 'STU2024001', '9841234567', 'student', 'active', NOW()),
(4, 'Pooja Thapa', 'pooja@college.com', 'scrypt:32768:8:1$u7F5G1Vw$db9bfef0fca02d0cf3b08cb0fc1bc2e8bf53d2bf3e8d7ef26f30a9960ff570dcf4564c7816eb883833f44384dbe8a74e50bb7f9754f7a39d8ebbc5a2c4e3a479', 'STU2024045', '9812345678', 'student', 'active', NOW()),
(5, 'Bikash KC', 'bikash@college.com', 'scrypt:32768:8:1$u7F5G1Vw$db9bfef0fca02d0cf3b08cb0fc1bc2e8bf53d2bf3e8d7ef26f30a9960ff570dcf4564c7816eb883833f44384dbe8a74e50bb7f9754f7a39d8ebbc5a2c4e3a479', 'STU2024089', '9860123456', 'student', 'active', NOW());

-- Categories
INSERT INTO `categories` (`id`, `name`, `description`) VALUES
(1, 'Breakfast', 'Fresh morning meals, bakery, and light breakfast items'),
(2, 'Snacks', 'Quick crispy bites, fries, and afternoon appetizers'),
(3, 'Main Course', 'Hearty traditional and filling meals for lunch and dinner'),
(4, 'Fast Food', 'Burgers, pizzas, sandwiches, and student favorites'),
(5, 'Drinks', 'Hot teas, brewed coffee, cold beverages, and fresh lassi'),
(6, 'Desserts', 'Sweet treats and dessert delights to finish your meal');

-- Menu Items (Nepalese / College Canteen Pricing in NPR)
INSERT INTO `menu_items` (`id`, `category_id`, `name`, `description`, `price`, `image`, `stock`, `minimum_stock`, `is_available`, `created_at`) VALUES
(1, 3, 'Steam Momo (Buff/Veg)', 'Authentic freshly steamed dumplings served with hot spicy sesame tomato chutney', 120.00, '/static/images/momo.svg', 50, 10, TRUE, NOW()),
(2, 3, 'Veg / Chicken Chowmein', 'Wok-tossed noodles with shredded vegetables and special canteen spice blend', 100.00, '/static/images/chowmein.svg', 45, 10, TRUE, NOW()),
(3, 3, 'Egg Fried Rice', 'Aromatic stir-fried rice loaded with scrambled egg, garden peas, and spring onions', 110.00, '/static/images/fried-rice.svg', 35, 10, TRUE, NOW()),
(4, 3, 'Special Nepali Dal Bhat Set', 'Complete traditional thali with steamed rice, yellow lentils, seasonal tarkari, and pickle', 130.00, '/static/images/dal-bhat.svg', 30, 8, TRUE, NOW()),
(5, 2, 'Crispy Samosa (2 pcs)', 'Golden crisp pastry triangles filled with spiced cumin potatoes and green peas', 30.00, '/static/images/samosa.svg', 80, 15, TRUE, NOW()),
(6, 4, 'Grilled Veg Sandwich', 'Toasted triple-layer sandwich with cheese, crisp cucumber, tomato, and mint chutney', 80.00, '/static/images/sandwich.svg', 40, 10, TRUE, NOW()),
(7, 4, 'Crispy Chicken Burger', 'Juicy chicken patty layered with lettuce, cheese slice, and creamy mayo sauce', 150.00, '/static/images/burger.svg', 30, 8, TRUE, NOW()),
(8, 4, 'Cheese Pizza Slice', 'Oven-baked crust topped with rich herb tomato sauce and melted mozzarella cheese', 180.00, '/static/images/pizza.svg', 25, 8, TRUE, NOW()),
(9, 2, 'Golden French Fries', 'Crispy fried potato batons lightly salted and served with tomato ketchup', 90.00, '/static/images/fries.svg', 60, 12, TRUE, NOW()),
(10, 1, 'Aloo Paratha with Curd', 'Warm whole wheat stuffed flatbread served with fresh curd and spicy mixed pickle', 70.00, '/static/images/paratha.svg', 40, 10, TRUE, NOW()),
(11, 1, 'Masala Omelette & Toast', 'Fluffy 2-egg omelette with onions, green chillies, coriander, and toasted butter bread', 90.00, '/static/images/omelette.svg', 35, 8, TRUE, NOW()),
(12, 5, 'Hot Brewed Coffee', 'Rich freshly brewed aromatic milk coffee to power through study sessions', 80.00, '/static/images/coffee.svg', 100, 20, TRUE, NOW()),
(13, 5, 'Nepali Masala Chiya', 'Classic spiced milk tea infused with cardamom, ginger, and cloves', 40.00, '/static/images/chiya.svg', 120, 25, TRUE, NOW()),
(14, 5, 'Cold Drinks (300ml)', 'Chilled soda bottle (Coke, Fanta, Sprite)', 60.00, '/static/images/cold-drinks.svg', 80, 15, TRUE, NOW()),
(15, 5, 'Sweet Curd Lassi', 'Chilled creamy yogurt smoothie topped with sliced almonds', 70.00, '/static/images/lassi.svg', 50, 10, TRUE, NOW()),
(16, 6, 'Hot Gulab Jamun (2 pcs)', 'Soft golden milk dough balls soaked in warm saffron cardamom sugar syrup', 50.00, '/static/images/gulab-jamun.svg', 40, 10, TRUE, NOW()),
(17, 6, 'Vanilla / Chocolate Ice Cream', 'Creamy scoop of vanilla or rich chocolate ice cream', 60.00, '/static/images/ice-cream.svg', 45, 10, TRUE, NOW()),
(18, 2, 'Spicy Wai Wai Sadeko', 'Crunchy instant noodles tossed with chopped onions, tomatoes, lime, and chilli powder', 50.00, '/static/images/wai-wai.svg', 70, 15, TRUE, NOW());

-- Sample Orders
INSERT INTO `orders` (`id`, `user_id`, `total_amount`, `status`, `payment_method`, `payment_status`, `pickup_time`, `created_at`) VALUES
(101, 3, 200.00, 'completed', 'esewa', 'completed', 'ASAP', DATE_SUB(NOW(), INTERVAL 3 DAY)),
(102, 3, 150.00, 'completed', 'khalti', 'completed', '1:00 PM', DATE_SUB(NOW(), INTERVAL 2 DAY)),
(103, 4, 300.00, 'completed', 'qr', 'completed', '12:00 PM', DATE_SUB(NOW(), INTERVAL 1 DAY)),
(104, 3, 160.00, 'ready', 'cash', 'pending', 'ASAP', DATE_SUB(NOW(), INTERVAL 25 MINUTE)),
(105, 5, 220.00, 'preparing', 'esewa', 'completed', '12:30 PM', DATE_SUB(NOW(), INTERVAL 15 MINUTE)),
(106, 4, 120.00, 'confirmed', 'qr', 'completed', '1:00 PM', DATE_SUB(NOW(), INTERVAL 5 MINUTE));

-- Sample Order Items
INSERT INTO `order_items` (`order_id`, `menu_item_id`, `quantity`, `price`) VALUES
(101, 1, 1, 120.00),
(101, 12, 1, 80.00),
(102, 7, 1, 150.00),
(103, 1, 1, 120.00),
(103, 8, 1, 180.00),
(104, 1, 1, 120.00),
(104, 13, 1, 40.00),
(105, 7, 1, 150.00),
(105, 15, 1, 70.00),
(106, 1, 1, 120.00);

-- Sample Reviews
INSERT INTO `reviews` (`user_id`, `menu_item_id`, `order_id`, `rating`, `comment`, `is_visible`, `created_at`) VALUES
(3, 1, 101, 5, 'Best momo on campus! Steaming hot and the achar has the perfect punch.', TRUE, DATE_SUB(NOW(), INTERVAL 3 DAY)),
(3, 12, 101, 4, 'Great coffee to keep me awake during lectures.', TRUE, DATE_SUB(NOW(), INTERVAL 3 DAY)),
(4, 8, 103, 5, 'Super cheesy and crispy crust. Great value for money!', TRUE, DATE_SUB(NOW(), INTERVAL 1 DAY)),
(5, 7, 102, 5, 'The chicken burger was delicious, fresh buns and crispy patty.', TRUE, DATE_SUB(NOW(), INTERVAL 2 DAY)),
(3, 13, 104, 5, 'Authentic Nepali Chiya, sweet and full of spices!', TRUE, DATE_SUB(NOW(), INTERVAL 1 HOUR));
