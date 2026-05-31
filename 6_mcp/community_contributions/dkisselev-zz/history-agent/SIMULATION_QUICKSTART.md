================================================================================
                   HISTORICAL SIMULATION - QUICK START
================================================================================

================================================================================
STEP 1: Configure .env
================================================================================

Add these lines to your .env file:

SIMULATION_MODE=true
SIMULATION_START_DATE=2024-01-01
SIMULATION_END_DATE=2024-03-31
MASSIVE_API_KEY=your_api_key_here

Notes:
- Date range must be within last ~2 years (free tier limit)
- Shorter ranges test faster (start with 1 month)
- MASSIVE_API_KEY required for historical data
- Traders run once per trading day using daily close prices

================================================================================
STEP 2: Reset Accounts for Simulation
================================================================================

`uv run python reset.py simulation 2024-01-01`

This resets all traders to $10,000 starting balance.

================================================================================
STEP 3: Run Simulation
================================================================================

`uv run python trading_floor.py`

What happens:
1. Simulates trading day-by-day
2. Shows results at the end


FINAL RESULTS
================================================================================

1. Ray [✓ Active]
   Final Portfolio Value: $12,450.50
   P&L: $2,450.50
   ROI: 24.51%
   Total Trades: 87

2. Warren [✓ Active]
   Final Portfolio Value: $11,230.25
   P&L: $1,230.25
   ROI: 12.30%
   Total Trades: 42

3. George [✓ Active]
   Final Portfolio Value: $10,145.00
   P&L: $145.00
   ROI: 1.45%
   Total Trades: 156

4. Cathie [💀 BANKRUPT]
   Final Portfolio Value: $0.00
   P&L: -$10,000.00
   ROI: -100.00%
   Total Trades: 203

Summary: 3 survived, 1 went bankrupt
