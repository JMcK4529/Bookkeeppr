-- lib/db/sql/cleanup.sql

DELETE FROM purchases;
DELETE FROM sales;
DELETE FROM customers;
DELETE FROM suppliers;

-- Reset AUTOINCREMENT sequences (SQLite only)
DELETE FROM sqlite_sequence WHERE name IN ('purchases', 'sales', 'customers', 'suppliers');