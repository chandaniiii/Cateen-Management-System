"""
Database Migration Script for Online Food Delivery System
Safely migrates existing database schema to include food delivery addresses,
delivery fees, transaction IDs, and customer profile delivery details without
deleting or resetting any existing records.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import db
from sqlalchemy import text


def run_migration():
    app = create_app()
    with app.app_context():
        engine = db.engine
        db_type = engine.dialect.name
        print(f"[*] Running database schema migration on dialect: {db_type}")

        if db_type == "postgresql":
            statements = [
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS address VARCHAR(255);",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS city VARCHAR(100);",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_type VARCHAR(20) DEFAULT 'delivery';",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_address VARCHAR(255);",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS city_area VARCHAR(100);",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS landmark VARCHAR(150);",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS phone_number VARCHAR(30);",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_notes TEXT;",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_charge NUMERIC(10, 2) DEFAULT 0.00;",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS transaction_id VARCHAR(100);",
                "UPDATE orders SET delivery_type = 'delivery' WHERE delivery_type IS NULL;",
                "UPDATE orders SET delivery_charge = 0.00 WHERE delivery_charge IS NULL;",
            ]
        elif db_type == "sqlite":
            statements = [
                "ALTER TABLE users ADD COLUMN address VARCHAR(255);",
                "ALTER TABLE users ADD COLUMN city VARCHAR(100);",
                "ALTER TABLE orders ADD COLUMN delivery_type VARCHAR(20) DEFAULT 'delivery';",
                "ALTER TABLE orders ADD COLUMN delivery_address VARCHAR(255);",
                "ALTER TABLE orders ADD COLUMN city_area VARCHAR(100);",
                "ALTER TABLE orders ADD COLUMN landmark VARCHAR(150);",
                "ALTER TABLE orders ADD COLUMN phone_number VARCHAR(30);",
                "ALTER TABLE orders ADD COLUMN delivery_notes TEXT;",
                "ALTER TABLE orders ADD COLUMN delivery_charge NUMERIC(10, 2) DEFAULT 0.00;",
                "ALTER TABLE orders ADD COLUMN transaction_id VARCHAR(100);",
            ]
        else:
            statements = [
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS address VARCHAR(255) NULL;",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS city VARCHAR(100) NULL;",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_type VARCHAR(20) NOT NULL DEFAULT 'delivery';",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_address VARCHAR(255) NULL;",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS city_area VARCHAR(100) NULL;",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS landmark VARCHAR(150) NULL;",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS phone_number VARCHAR(30) NULL;",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_notes TEXT NULL;",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_charge DECIMAL(10, 2) NOT NULL DEFAULT 0.00;",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS transaction_id VARCHAR(100) NULL;",
            ]

        with engine.connect() as conn:
            for stmt in statements:
                try:
                    conn.execute(text(stmt))
                    conn.commit()
                    print(f"  [✓] Executed: {stmt.strip()[:65]}...")
                except Exception as ex:
                    # Ignore duplicate column errors during safe migration
                    print(f"  [i] Skipped or already applied: {str(ex).splitlines()[0]}")

        print("[★] Database migration finished successfully!")


if __name__ == "__main__":
    run_migration()
