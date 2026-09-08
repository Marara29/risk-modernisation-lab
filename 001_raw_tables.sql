CREATE TABLE customer_records (
    customer_record_id TEXT PRIMARY KEY,
    name TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    created_at DATE
);

CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    customer_record_id TEXT,
    open_date DATE,
    credit_limit REAL,
    current_balance REAL,
    product_type TEXT,
    status TEXT
);

CREATE TABLE applications (
    application_id TEXT PRIMARY KEY,
    customer_record_id TEXT,
    application_date DATE,
    requested_limit REAL,
    annual_revenue REAL,
    years_in_business REAL,
    industry TEXT
);

CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT,
    transaction_timestamp DATETIME,
    amount REAL,
    merchant_id TEXT,
    merchant_category TEXT,
    country TEXT
);

CREATE TABLE payments (
    payment_id TEXT PRIMARY KEY,
    account_id TEXT,
    due_date DATE,
    payment_date DATE,
    amount_due REAL,
    amount_paid REAL
);

CREATE TABLE delinquencies (
    account_id TEXT,
    snapshot_date DATE,
    days_past_due INTEGER,
    outstanding_balance REAL
);

CREATE TABLE vendor_scores (
    account_id TEXT,
    score_date DATE,
    vendor_risk_score REAL,
    vendor_risk_band TEXT
);
