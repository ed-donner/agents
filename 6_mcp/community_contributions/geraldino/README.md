# AI Trading Floor — Community Contribution
 
I extended the Week 6 classwork from Ed Donner's **Master AI Agents in 30 Days** course. All credit for the original trading floor architecture, agent design, and MCP integration goes to Ed.
 
The original project is an autonomous multi-agent stock trading system where four AI traders — each inspired by a legendary investor — run on a loop, conduct real web research, and execute real trades via MCP-connected tools. Each trader has its own persistent memory and alternates between trading and rebalancing cycles.
 
## What I added
 
**Risk Manager agent** — a separate LLM agent (GPT-4o Mini) that runs after every trading cycle and triggers only when a trader's portfolio drops ≥5% from their $10,000 starting capital. When breached, it reviews all four portfolios, identifies the losing positions, provides per-trader recommendations, sends a Pushover push notification to your phone, and emails a detailed HTML report via SendGrid. It does not execute trades, it's role is strictly advisory only.
 
**Smart skip logic** — if all portfolios are within the loss threshold, the Risk Manager LLM is never instantiated, this saves API costs.
 
## Additional `.env` setup
 
```env
RISK_THRESHOLD_PCT=5.0                 # loss % that triggers Risk Manager
PUSHOVER_USER=your_user_key            # push notification to your phone
PUSHOVER_TOKEN=your_app_token
SENDGRID_API_KEY=your_key              # email report
RISK_EMAIL_FROM=alerts@yourdomain.com  # must be verified in SendGrid
RISK_EMAIL_TO=you@gmail.com
```
 