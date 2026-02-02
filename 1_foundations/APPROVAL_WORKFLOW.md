# 🔐 User Approval & Credential Generation Workflow

## Overview
This document describes the complete workflow for approving users and granting them unlimited access with secure login credentials.

---

## 📋 **Complete Flow**

### 1️⃣ **User Registration & Contact Request**
- User visits the chatbot as a visitor
- Gets 5 free queries
- When limit is reached, provides email and reason via chat:
  ```
  Email: user@example.com
  Reason: I want to discuss job opportunities
  ```
- System saves to both `contacts` and `upgrade_requests` tables
- Admin receives PushOver notification with user details

### 2️⃣ **Admin Reviews Pending Requests**
```bash
cd agents/1_foundations
uv run python admin_approve.py
```

**Menu Options:**
1. List pending upgrade requests → See all pending approvals
2. Approve a user → Grant unlimited access
3. Show user statistics → View system stats
4. Exit

### 3️⃣ **Approval Process**

When you approve a user (Option 2):

**Input:**
```
Enter username to approve: visitor_031f6f15
```

**System Actions:**
1. ✅ Validates user exists
2. 📧 Retrieves user email
3. 🔑 Generates secure credentials:
   - **Username:** `{email_prefix}_{random_4_chars}`
   - **Password:** `{secure_random_12_chars}`
4. 💾 Updates database:
   - Changes tier from `visitor` to `unlimited`
   - Sets query_limit to `-1` (unlimited)
   - Updates status to `approved`
   - Stores new username & hashed password
5. 📝 Logs credentials to `credentials_log` table
6. 📱 Sends PushOver notification with credentials
7. 📺 Displays credentials in terminal

**Output Example:**
```
================================================================================
✅ User 'visitor_031f6f15' has been approved and granted unlimited access!
================================================================================

🔑 NEW LOGIN CREDENTIALS:
   Username: xeroxatpro_6205
   Password: HhSIUCgUlR_ai68C
   Email: xeroxatpro@gmail.com

📧 Make sure to send these credentials to: xeroxatpro@gmail.com

⚠️  IMPORTANT: Save these credentials! They won't be shown again.
================================================================================
```

### 4️⃣ **Sending Credentials to User**

**You need to manually email the user:**

```
Subject: Your Unlimited Access to [Your Name]'s Chatbot

Hi [User Name],

Great news! Your request for unlimited access has been approved! 🎉

Here are your login credentials:

🔑 Username: xeroxatpro_6205
🔒 Password: HhSIUCgUlR_ai68C

📍 Login URL: http://localhost:7860

To access unlimited queries:
1. Go to the chatbot
2. Click on "🔐 Login / Sign Up" tab
3. Click "🔑 Approved User Login"
4. Enter your credentials
5. Start chatting with unlimited queries!

Thank you for your interest!

Best regards,
[Your Name]
```

### 5️⃣ **User Login**

User accesses the chatbot:
1. Opens `http://localhost:7860`
2. Clicks "🔐 Login / Sign Up" tab
3. Enters:
   - Username: `xeroxatpro_6205`
   - Password: `HhSIUCgUlR_ai68C`
4. Clicks "LOGIN"
5. Gets unlimited access! ✅

---

## 🗄️ **Database Tables**

### `users` Table
Stores all user accounts (visitors & approved)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,          -- Changes from visitor_xxx to email_xxx
    password_hash TEXT,             -- SHA-256 hashed password
    email TEXT,
    tier TEXT DEFAULT 'visitor',    -- 'visitor' or 'unlimited'
    query_count INTEGER DEFAULT 0,
    query_limit INTEGER DEFAULT 5,  -- -1 for unlimited
    status TEXT DEFAULT 'pending',  -- 'pending' or 'approved'
    contact_submitted INTEGER,
    created_at TIMESTAMP,
    approved_at TIMESTAMP,
    notes TEXT
);
```

### `upgrade_requests` Table
Tracks all upgrade requests
```sql
CREATE TABLE upgrade_requests (
    id INTEGER PRIMARY KEY,
    username TEXT,                  -- Original visitor username
    email TEXT,
    intent TEXT,                    -- Why they want access
    status TEXT DEFAULT 'pending',  -- 'pending' or 'approved'
    created_at TIMESTAMP,
    processed_at TIMESTAMP
);
```

### `credentials_log` Table (NEW!)
**Securely logs all generated credentials**
```sql
CREATE TABLE credentials_log (
    id INTEGER PRIMARY KEY,
    old_username TEXT,              -- Original visitor_xxx
    new_username TEXT,              -- New email_xxx username
    password_plain TEXT,            -- ⚠️ Plain password (for admin only!)
    email TEXT,
    created_at TIMESTAMP,
    sent_to_user BOOLEAN DEFAULT FALSE
);
```

**⚠️ Security Note:** The `credentials_log` table stores plain-text passwords for admin reference. In production:
- Only admins should have database access
- Consider encrypting passwords in this table
- Delete records after sending to users
- Or don't store passwords at all (user must reset if forgotten)

---

## 🔒 **Security Features**

### Password Security
- ✅ **Strong passwords:** 12 characters, URL-safe random
- ✅ **Hashed storage:** SHA-256 in `users` table
- ✅ **Unique usernames:** Email prefix + random suffix
- ⚠️ **Plain storage:** In `credentials_log` (admin only)

### Access Control
- ✅ **Tier-based:** Visitors (5 queries) vs Unlimited
- ✅ **Query tracking:** Count tracked per user
- ✅ **Session management:** Track user sessions
- ✅ **IP tracking:** Prevent visitor account spam

---

## 📊 **Admin Commands**

### List All Credentials Generated
```bash
sqlite3 career_bot.db "
SELECT old_username, new_username, password_plain, email, created_at 
FROM credentials_log 
ORDER BY created_at DESC;
"
```

### Check Approved Users
```bash
sqlite3 career_bot.db "
SELECT username, email, tier, status, approved_at 
FROM users 
WHERE tier = 'unlimited' 
ORDER BY approved_at DESC;
"
```

### View Pending Requests
```bash
sqlite3 career_bot.db "
SELECT ur.username, ur.email, ur.intent, ur.created_at, u.query_count 
FROM upgrade_requests ur 
JOIN users u ON ur.username = u.username 
WHERE ur.status = 'pending';
"
```

---

## 🚀 **Quick Start for Admins**

### Daily Workflow:
```bash
# 1. Check for new PushOver notifications on your phone

# 2. Run admin panel
cd agents/1_foundations
uv run python admin_approve.py

# 3. Choose option 1 - List pending requests

# 4. Choose option 2 - Approve a user
# Enter username: visitor_xxx

# 5. Copy credentials from terminal

# 6. Send email to user with credentials

# 7. Mark as sent (optional):
sqlite3 career_bot.db "
UPDATE credentials_log 
SET sent_to_user = TRUE 
WHERE new_username = 'xeroxatpro_6205';
"
```

---

## 📧 **Email Template**

Save this template for quick use:

```
Subject: ✅ Your Unlimited Access is Approved!

Hi there,

Great news! Your request for unlimited access to my AI chatbot has been approved! 🎉

**Your Login Credentials:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔑 Username: [NEW_USERNAME]
🔒 Password: [NEW_PASSWORD]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**How to Login:**
1. Visit: http://localhost:7860
2. Click "🔐 Login / Sign Up" tab
3. Select "🔑 Approved User Login"
4. Enter your credentials
5. Start chatting! 💬

**What You Get:**
✅ Unlimited questions
✅ Full conversation history
✅ Priority support
✅ Access to all features

**Important:**
⚠️ Keep your credentials secure
⚠️ Don't share your password
⚠️ Bookmark the login page

Looking forward to our conversation!

Best regards,
[Your Name]
```

---

## 🔧 **Troubleshooting**

### User Can't Login
1. Verify credentials in `credentials_log` table
2. Check user status: `SELECT * FROM users WHERE username = 'xxx';`
3. Ensure password_hash was generated
4. Check app is running on port 7860

### Credentials Not Showing
1. Ensure `admin_approve.py` imports `UserManager` correctly
2. Check PushOver notification was sent
3. Verify `credentials_log` table exists

### Duplicate Usernames
- System adds random suffix to prevent collisions
- Format: `{email_prefix}_{random_hex}`
- Example: `john_a5f3`, `john_b7e2`

---

## 📈 **Future Enhancements**

- [ ] Automated email sending (SendGrid/MailGun)
- [ ] Password reset functionality
- [ ] Self-service password change
- [ ] 2FA authentication
- [ ] API key generation for programmatic access
- [ ] Usage analytics dashboard
- [ ] Credential expiry/rotation

---

**Created:** November 14, 2025
**Last Updated:** November 14, 2025
**Version:** 1.0
