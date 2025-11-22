-- Create positions table
CREATE TABLE IF NOT EXISTS swap_positions (
    position_id VARCHAR(50) PRIMARY KEY,
    trade_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    notional DECIMAL(15,2) NOT NULL,
    fixed_rate DECIMAL(6,4) NOT NULL,
    float_index VARCHAR(20) NOT NULL,
    pay_receive VARCHAR(10) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create market rates table
CREATE TABLE IF NOT EXISTS market_rates (
    rate_id SERIAL PRIMARY KEY,
    tenor VARCHAR(10) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    mid_rate DECIMAL(6,4) NOT NULL,
    bid_rate DECIMAL(6,4),
    ask_rate DECIMAL(6,4),
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50)
);

-- Create trade signals table
CREATE TABLE IF NOT EXISTS trade_signals (
    signal_id SERIAL PRIMARY KEY,
    position_id VARCHAR(50),
    signal_type VARCHAR(20),
    reason TEXT,
    current_pnl DECIMAL(15,2),
    recommended_action TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (position_id) REFERENCES swap_positions(position_id)
);

-- Create demo executions table for rate limiting
CREATE TABLE IF NOT EXISTS demo_executions (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    last_run TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ip_time ON demo_executions(ip_address, last_run);
