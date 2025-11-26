-- ==========================================
--   COMPANY TRANSACTIONS SAMPLE DATABASE
-- ==========================================

-- Drop tables if they exist (for re-runs)
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS merchants;
DROP TABLE IF EXISTS customers;

-- ===========================
-- 1. CUSTOMERS
-- ===========================

CREATE TABLE customers (
    id            INTEGER PRIMARY KEY,
    full_name     VARCHAR(100) NOT NULL,
    email         VARCHAR(150) UNIQUE NOT NULL,
    country       VARCHAR(50) NOT NULL,
    segment       VARCHAR(30) NOT NULL,   -- 'retail', 'smb', 'enterprise'
    created_at    TIMESTAMP NOT NULL
);

INSERT INTO customers (id, full_name, email, country, segment, created_at) VALUES
(1,  'Amit Patel',      'amit.patel@example.com',      'USA',      'retail',    '2023-01-10 09:15:00'),
(2,  'Jay Shah',        'jay.shah@example.com',        'USA',      'retail',    '2023-02-05 11:20:00'),
(3,  'Riya Mehta',      'riya.mehta@example.com',      'India',    'retail',    '2023-03-18 15:45:00'),
(4,  'Emily Chen',      'emily.chen@example.com',      'Canada',   'smb',       '2023-03-21 10:00:00'),
(5,  'Carlos Lopez',    'carlos.lopez@example.com',    'Mexico',   'retail',    '2023-04-02 13:30:00'),
(6,  'Sarah Johnson',   'sarah.johnson@example.com',   'USA',      'retail',    '2023-04-15 08:25:00'),
(7,  'Michael Brown',   'michael.brown@example.com',   'UK',       'smb',       '2023-05-01 16:10:00'),
(8,  'Priya Nair',      'priya.nair@example.com',      'India',    'smb',       '2023-05-22 12:05:00'),
(9,  'Lucas Silva',     'lucas.silva@example.com',     'Brazil',   'retail',    '2023-06-03 09:50:00'),
(10, 'Olivia Martin',   'olivia.martin@example.com',   'France',   'enterprise','2023-06-30 14:40:00');

-- ===========================
-- 2. ACCOUNTS
-- ===========================

CREATE TABLE accounts (
    id           INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(id),
    account_type VARCHAR(30) NOT NULL,     -- 'checking', 'credit', 'savings'
    currency     VARCHAR(10) NOT NULL,     -- 'USD','INR','CAD',...
    status       VARCHAR(20) NOT NULL,     -- 'active','frozen','closed'
    opened_at    TIMESTAMP NOT NULL
);

INSERT INTO accounts (id, customer_id, account_type, currency, status, opened_at) VALUES
(101, 1, 'checking', 'USD', 'active', '2023-01-10 09:20:00'),
(102, 1, 'credit',   'USD', 'active', '2023-02-15 10:00:00'),
(103, 2, 'checking', 'USD', 'active', '2023-02-05 11:30:00'),
(104, 3, 'checking', 'INR', 'active', '2023-03-19 09:00:00'),
(105, 3, 'savings',  'INR', 'active', '2023-03-25 10:10:00'),
(106, 4, 'checking', 'CAD', 'active', '2023-03-21 10:10:00'),
(107, 5, 'checking', 'MXN', 'frozen', '2023-04-05 17:00:00'),
(108, 6, 'credit',   'USD', 'active', '2023-04-16 09:00:00'),
(109, 7, 'checking', 'GBP', 'active', '2023-05-01 16:20:00'),
(110, 8, 'checking', 'INR', 'active', '2023-05-22 12:15:00'),
(111, 9, 'checking', 'BRL', 'active', '2023-06-03 10:00:00'),
(112,10, 'checking', 'EUR', 'active', '2023-06-30 14:50:00');

-- ===========================
-- 3. MERCHANTS
-- ===========================

CREATE TABLE merchants (
    id        INTEGER PRIMARY KEY,
    name      VARCHAR(120) NOT NULL,
    category  VARCHAR(50)  NOT NULL, -- 'grocery','restaurant','travel','saas',...
    country   VARCHAR(50)  NOT NULL
);

INSERT INTO merchants (id, name, category, country) VALUES
(201, 'FreshMart Supermarket',     'grocery',     'USA'),
(202, 'QuickEats Fast Food',       'restaurant',  'USA'),
(203, 'Skyline Airlines',          'travel',      'USA'),
(204, 'CloudBills SaaS',           'saas',        'Canada'),
(205, 'Bollywood Cinema',          'entertainment','India'),
(206, 'Tech World Electronics',    'electronics', 'USA'),
(207, 'BookHive Online Store',     'ecommerce',   'UK'),
(208, 'GreenCab Taxi',             'transport',   'India'),
(209, 'Café Bonjour',              'restaurant',  'France'),
(210, 'SunnyResort Hotels',        'hotel',       'Mexico');

-- ===========================
-- 4. TRANSACTIONS
-- ===========================

CREATE TABLE transactions (
    id              INTEGER PRIMARY KEY,
    account_id      INTEGER NOT NULL REFERENCES accounts(id),
    merchant_id     INTEGER REFERENCES merchants(id),
    txn_time        TIMESTAMP NOT NULL,
    amount          DECIMAL(12,2) NOT NULL,
    currency        VARCHAR(10) NOT NULL,
    txn_type        VARCHAR(20) NOT NULL,   -- 'purchase','refund','fee','transfer_in','transfer_out','chargeback'
    channel         VARCHAR(20) NOT NULL,   -- 'pos','online','atm','manual'
    status          VARCHAR(20) NOT NULL,   -- 'pending','settled','declined','reversed','chargeback'
    related_txn_id  INTEGER REFERENCES transactions(id)   -- for refunds/chargebacks
);

-- Amit (customer 1) – USD spend
INSERT INTO transactions (id, account_id, merchant_id, txn_time, amount, currency, txn_type, channel, status, related_txn_id) VALUES
(1001, 101, 201, '2023-07-01 09:15:00',  82.45, 'USD', 'purchase', 'pos',    'settled',  NULL),
(1002, 101, 202, '2023-07-02 12:30:00',  15.99, 'USD', 'purchase', 'pos',    'settled',  NULL),
(1003, 102, 203, '2023-07-05 18:00:00', 420.00, 'USD', 'purchase', 'online', 'settled',  NULL),
(1004, 102, 203, '2023-07-06 09:00:00', -50.00, 'USD', 'refund',   'online', 'settled',  1003),
(1005, 101, NULL,'2023-07-07 08:00:00',   5.00, 'USD', 'fee',      'manual', 'settled',  NULL);

-- Jay (customer 2) – small transactions + one declined
INSERT INTO transactions VALUES
(1006, 103, 202, '2023-07-01 10:05:00',  12.50, 'USD', 'purchase',  'pos',    'settled',   NULL),
(1007, 103, 206, '2023-07-03 14:22:00', 249.99, 'USD', 'purchase',  'online', 'declined',  NULL),
(1008, 103, 206, '2023-07-03 14:30:00', 249.99, 'USD', 'purchase',  'online', 'settled',   NULL);

-- Riya (customer 3) – INR, with taxi & cinema
INSERT INTO transactions VALUES
(1009, 104, 205, '2023-07-01 19:45:00',  450.00, 'INR', 'purchase', 'pos',    'settled',   NULL),
(1010, 104, 208, '2023-07-02 08:30:00',  220.00, 'INR', 'purchase', 'online', 'settled',   NULL),
(1011, 105, NULL,'2023-07-03 09:00:00', 1500.00, 'INR', 'transfer_in','manual','settled',  NULL);

-- Emily (customer 4) – pays SaaS subscription
INSERT INTO transactions VALUES
(1012, 106, 204, '2023-07-01 00:10:00',  59.00, 'CAD', 'purchase',  'online', 'settled',   NULL),
(1013, 106, 204, '2023-08-01 00:15:00',  59.00, 'CAD', 'purchase',  'online', 'settled',   NULL);

-- Carlos (customer 5) – frozen account, chargeback
INSERT INTO transactions VALUES
(1014, 107, 210, '2023-07-10 16:00:00', 3500.00, 'MXN', 'purchase',   'online',    'settled',      NULL),
(1015, 107, 210, '2023-07-20 09:00:00', 3500.00, 'MXN', 'chargeback','manual',    'chargeback',   1014);

-- Sarah (customer 6) – credit card, restaurant
INSERT INTO transactions VALUES
(1016, 108, 202, '2023-07-04 19:30:00',   32.75, 'USD', 'purchase',  'pos',       'settled',   NULL),
(1017, 108, 202, '2023-07-04 21:00:00',  -10.00, 'USD', 'refund',    'pos',       'settled',   1016);

-- Michael (customer 7) – UK ecommerce
INSERT INTO transactions VALUES
(1018, 109, 207, '2023-07-12 11:11:00',   48.99, 'GBP', 'purchase',  'online',    'settled',   NULL),
(1019, 109, 207, '2023-07-15 09:00:00',   12.49, 'GBP', 'purchase',  'online',    'settled',   NULL);

-- Priya (customer 8) – India
INSERT INTO transactions VALUES
(1020, 110, 205, '2023-07-09 18:00:00',  350.00, 'INR', 'purchase',  'pos',       'settled',   NULL),
(1021, 110, 208, '2023-07-10 08:45:00',  180.00, 'INR', 'purchase',  'online',    'settled',   NULL);

-- Lucas (customer 9) – Brazil
INSERT INTO transactions VALUES
(1022, 111, 201, '2023-07-05 13:30:00',  120.00, 'BRL', 'purchase',  'pos',       'settled',   NULL),
(1023, 111, NULL,'2023-07-06 09:00:00',   15.00, 'BRL', 'fee',       'manual',    'settled',   NULL);

-- Olivia (customer 10) – France
INSERT INTO transactions VALUES
(1024, 112, 209, '2023-07-07 20:10:00',   42.30, 'EUR', 'purchase',  'pos',       'settled',   NULL),
(1025, 112, 209, '2023-07-08 08:05:00',   10.00, 'EUR', 'purchase',  'pos',       'pending',   NULL);
