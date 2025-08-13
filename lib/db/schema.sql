CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    customer_name TEXT,
    invoice_number TEXT UNIQUE,
    net_amount REAL,
    vat_percent REAL,
    payment_method TEXT,
    timestamp TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER,
    supplier_name TEXT,
    supplier_invoice_code TEXT,
    internal_invoice_number TEXT UNIQUE,
    net_amount REAL,
    vat_percent REAL,
    goods REAL,
    utilities REAL,
    motor_expenses REAL,
    sundries REAL,
    miscellaneous REAL,
    payment_method TEXT,
    timestamp TEXT,
    capital_spend BOOLEAN,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);