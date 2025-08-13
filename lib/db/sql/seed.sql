-- lib/db/sql/seed.sql

-- Suppliers
INSERT INTO suppliers (name) VALUES
    ('TimberCo'),
    ('Sawmill Solutions'),
    ('Lumber Ltd');

-- Customers
INSERT INTO customers (name) VALUES
    ('Alice Smith'),
    ('Bob Jones'),
    ('Charlie Timber');

-- Sales
INSERT INTO sales (customer_id, invoice_number, customer_name, net_amount, vat_percent, payment_method, timestamp)
VALUES
    (1, 'Alice001', 'Alice Smith', 1000.00, 0.20, 'BACS', '2025-06-01 10:00:00'),
    (2, 'Bob001', 'Bob Jones', 250.00, 0.0, 'Cheque', '2025-06-02 11:00:00'),
    (2, 'Bob002', 'Bob Jones', 150.00, 0.20, 'Contra', '2025-06-03 12:30:00'),
    (3, 'Charlie001', 'Charlie Timber', 80.00, 0.0, 'Direct Debit', '2025-06-04 14:23:56');

-- Purchases
INSERT INTO purchases (
    supplier_id, supplier_invoice_code, internal_invoice_number, supplier_name,
    net_amount, vat_percent, goods, utilities, motor_expenses, sundries, miscellaneous,
    payment_method, timestamp, capital_spend
)
VALUES
    (1, 'TimCo001', 'P001', 'TimberCo', 800.00, 0.20, 600.00, 100.00, 50.00, 50.00, 0.00, 'Card', '2025-06-01 09:00:00', 0),
    (2, 'SawSol001', 'P002', 'Sawmill Solutions', 1200.00, 0.20, 1000.00, 100.00, 50.00, 50.00, 0.00, 'BACS', '2025-06-02 14:00:00', 1),
    (2, 'SawSol002', 'P003', 'Sawmill Solutions', 1234.56, 0.0, 100.00, 134.00, 500.28, 500.28, 0.00, 'Cheque', '2025-06-03 17:00:00', 0),
    (3, 'LumLtd001', 'P004', 'LumberLtd', 500.00, 0.0, 100.00, 200.00, 200.00, 0.00, 0.00, 'Direct Debit', '2025-06-03 17:00:00', 0);