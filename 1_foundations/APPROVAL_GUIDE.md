# 🔐 User Approval Guide

## How to Approve Upgrade Requests

When a visitor requests unlimited access, you'll receive a **Pushover notification** with their details.

### Option 1: Command Line (Recommended)

Open terminal and run:

```bash
cd /path/to/agents/1_foundations
uv run python admin_approve.py visitor_xxxxx
```

Replace `visitor_xxxxx` with the actual username from the notification.

### Option 2: Interactive Mode

```bash
uv run python admin_approve.py
```

Then choose option 2 and enter the username.

### Option 3: Direct Database Access

If you prefer SQL:

```bash
sqlite3 career_bot.db

-- Check pending requests
SELECT u.username, u.email, ur.intent, ur.created_at 
FROM upgrade_requests ur
JOIN users u ON ur.username = u.username
WHERE ur.status = 'pending';

-- Approve a user
UPDATE users 
SET tier = 'unlimited', query_limit = -1, status = 'approved', approved_at = CURRENT_TIMESTAMP
WHERE username = 'visitor_xxxxx';

UPDATE upgrade_requests
SET status = 'approved', processed_at = CURRENT_TIMESTAMP
WHERE username = 'visitor_xxxxx' AND status = 'pending';

.quit
```

## Approval Workflow

### 1. Receive Notification 📱

```
🔔 UPGRADE REQUEST #123

Username: visitor_abc123
Email: john@example.com
Intent: I'm interested in discussing collaboration 
        opportunities for an AI project...

To approve, run:
python admin_approve.py visitor_abc123

Or use the admin panel.
```

### 2. Review the Request

Consider:
- ✅ Is the email valid?
- ✅ Is the intent legitimate and detailed?
- ✅ Have they shown genuine interest?
- ✅ Is this a potential collaboration/job opportunity?

### 3. Approve or Reject

**To Approve:**
```bash
uv run python admin_approve.py visitor_abc123
```

The script will show:
```
👤 User: visitor_abc123
📧 Email: john@example.com
🎫 Current Tier: visitor
📊 Status: pending

📝 Upgrade Request:
   Email: john@example.com
   Intent: I'm interested in...
   Requested: 2025-11-13 14:30:22

✅ Approve this user? (yes/no): yes

✅ User 'visitor_abc123' has been approved and granted unlimited access!
📧 Make sure to reach out to them at: john@example.com
```

**To Reject:**
- Simply don't approve
- Optionally, manually update the database to mark as 'rejected'

### 4. Reach Out

After approval:
1. User gets unlimited access immediately
2. Send them an email introducing yourself
3. Schedule a call/meeting if appropriate

## Batch Operations

### List All Pending Requests

```bash
uv run python admin_approve.py
# Choose option 1: List pending upgrade requests
```

### Approve Multiple Users

```bash
uv run python admin_approve.py visitor_001
uv run python admin_approve.py visitor_002
uv run python admin_approve.py visitor_003
```

Or use a bash loop:

```bash
for user in visitor_001 visitor_002 visitor_003; do
    uv run python admin_approve.py $user
done
```

## User Statistics

View user stats:

```bash
uv run python admin_approve.py
# Choose option 3: Show user statistics
```

Output:
```
📊 User Statistics:
================================================================================

🎫 Users by Tier:
   visitor: 15
   unlimited: 3

⏳ Pending Requests: 5

👥 Recent Users:
   visitor_abc123 - visitor - 3/5 queries - Created: 2025-11-13
   visitor_def456 - unlimited - 12/∞ queries - Created: 2025-11-12
   ...
```

## Security Considerations

### IP Tracking

The system prevents multiple visitor accounts from the same IP within 24 hours.

To check IP tracking:

```bash
sqlite3 career_bot.db "SELECT * FROM ip_tracking ORDER BY created_at DESC LIMIT 10;"
```

### Manual Override

If someone legitimately needs a second account:

```bash
sqlite3 career_bot.db
DELETE FROM ip_tracking WHERE ip_address = '192.168.1.100';
.quit
```

Then they can create a new visitor account.

## Troubleshooting

### Can't find admin_approve.py

```bash
cd /Users/gonenc_aydin/Desktop/The_Complete_AI_Agent_Course/agents/1_foundations
ls -la admin_approve.py
```

### Database locked error

Close any open connections:

```bash
pkill -f "app_new.py"
# Then try again
```

### User not found

Check if the username is correct:

```bash
sqlite3 career_bot.db "SELECT username FROM users WHERE username LIKE '%abc%';"
```

### Already approved

If you accidentally approve twice:

```
⚠️ User 'visitor_abc123' already has unlimited access!
```

This is safe - no action needed.

## Best Practices

### ✅ DO:

- Review requests within 24 hours
- Read the intent carefully
- Reach out to approved users promptly
- Keep track of interesting opportunities
- Monitor for abuse patterns

### ❌ DON'T:

- Auto-approve without reviewing
- Ignore legitimate requests
- Approve obvious spam/bots
- Forget to follow up with approved users

## Automation (Advanced)

### Auto-approve based on criteria

Create `auto_approve.py`:

```python
import sqlite3

def auto_approve_if_criteria_met():
    conn = sqlite3.connect('career_bot.db')
    cursor = conn.cursor()
    
    # Get pending requests
    cursor.execute('''
        SELECT username, email, intent 
        FROM upgrade_requests 
        WHERE status = 'pending'
    ''')
    
    for username, email, intent in cursor.fetchall():
        # Auto-approve if intent is detailed (>100 chars)
        # and email is from certain domains
        if len(intent) > 100 and any(domain in email for domain in ['company.com', 'startup.io']):
            # Approve
            from admin_approve import approve_user
            approve_user(username)
    
    conn.close()

if __name__ == "__main__":
    auto_approve_if_criteria_met()
```

Run periodically with cron:

```bash
# Add to crontab
crontab -e

# Run every hour
0 * * * * cd /path/to/agents/1_foundations && uv run python auto_approve.py
```

## Email Notifications (Future Enhancement)

To notify users when approved, integrate with email service:

```python
import smtplib
from email.mime.text import MIMEText

def notify_user_approved(email, username):
    msg = MIMEText(f"""
    Congratulations! Your upgrade request has been approved.
    
    You now have unlimited access to chat with my AI assistant.
    
    I look forward to connecting with you!
    
    Best regards,
    Gönenç Aydın
    """)
    
    msg['Subject'] = 'Your Access Has Been Approved!'
    msg['From'] = 'your@email.com'
    msg['To'] = email
    
    # Send email
    # ... (configure SMTP)
```

## Support

For questions or issues with the approval system:

1. Check the database: `sqlite3 career_bot.db`
2. Review logs in the terminal running app_new.py
3. Test with a dummy visitor account first

---

**Quick Reference:**

```bash
# Approve user
uv run python admin_approve.py visitor_xxxxx

# Interactive menu
uv run python admin_approve.py

# List pending
sqlite3 career_bot.db "SELECT * FROM upgrade_requests WHERE status='pending';"

# View all users
sqlite3 career_bot.db "SELECT username, tier, email FROM users;"
```
