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
    invoice_number TEXT UNIQUE,
    net_amount REAL,
    vat_percent TEXT,
    payment_method TEXT,
    timestamp TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER,
    supplier_invoice_code TEXT,
    internal_invoice_number TEXT UNIQUE,
    net_amount REAL,
    vat_percent TEXT,
    goods REAL,
    utilities REAL,
    motor_expenses REAL,
    sundries REAL,
    payment_method TEXT,
    timestamp TEXT,
    capital_spend BOOLEAN,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);