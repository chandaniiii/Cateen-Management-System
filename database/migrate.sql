-- ==============================================================
-- Online Food Delivery System — Database Schema Migration
-- Preserves all existing tables, rows, users, menu items, and reviews
-- ==============================================================

-- 1. PostgreSQL Migration:
ALTER TABLE users ADD COLUMN IF NOT EXISTS address VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS city VARCHAR(100);

ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_type VARCHAR(20) DEFAULT 'delivery';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_address VARCHAR(255);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS city_area VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS landmark VARCHAR(150);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS phone_number VARCHAR(30);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_notes TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_charge NUMERIC(10, 2) DEFAULT 0.00;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS transaction_id VARCHAR(100);

UPDATE orders SET delivery_type = 'delivery' WHERE delivery_type IS NULL;
UPDATE orders SET delivery_charge = 0.00 WHERE delivery_charge IS NULL;

-- 2. MySQL Migration (Alternative):
-- ALTER TABLE `users` ADD COLUMN `address` VARCHAR(255) NULL;
-- ALTER TABLE `users` ADD COLUMN `city` VARCHAR(100) NULL;
-- ALTER TABLE `orders` ADD COLUMN `delivery_type` VARCHAR(20) NOT NULL DEFAULT 'delivery';
-- ALTER TABLE `orders` ADD COLUMN `delivery_address` VARCHAR(255) NULL;
-- ALTER TABLE `orders` ADD COLUMN `city_area` VARCHAR(100) NULL;
-- ALTER TABLE `orders` ADD COLUMN `landmark` VARCHAR(150) NULL;
-- ALTER TABLE `orders` ADD COLUMN `phone_number` VARCHAR(30) NULL;
-- ALTER TABLE `orders` ADD COLUMN `delivery_notes` TEXT NULL;
-- ALTER TABLE `orders` ADD COLUMN `delivery_charge` DECIMAL(10, 2) NOT NULL DEFAULT 0.00;
-- ALTER TABLE `orders` ADD COLUMN `transaction_id` VARCHAR(100) NULL;
