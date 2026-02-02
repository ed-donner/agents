# Enhanced Career Bot with Tiered Authentication

This is an upgraded version of the career bot with a sophisticated user management system and improved UI.

## ✨ New Features

### 🔐 Tiered Authentication System

1. **Visitor Accounts** (5 queries)
   - Auto-generated credentials
   - Limited to 5 questions
   - No signup required

2. **Unlimited Accounts** (∞ queries)
   - Requires approval
   - Full access to chatbot
   - Email notification to owner

### 💼 Workflow

```
1. Visitor creates account → Gets username/password
2. Uses 5 free queries → Learns about you
3. Requests upgrade → Provides email + intent
4. You receive Pushover notification → Review request
5. You approve → User gets unlimited access
6. You reach out → Build connection
```

## 🚀 Setup

### 1. Install Dependencies

```bash
pip install openai gradio pypdf python-dotenv numpy requests
```

### 2. Environment Variables

Create/update `.env` file:

```env
OPENAI_API_KEY=your_openai_key_here
PUSHOVER_TOKEN=your_pushover_token
PUSHOVER_USER=your_pushover_user_key
```

### 3. Run the Application

```bash
python app_new.py
```

The app will be available at: `http://localhost:7860`

## 📊 Database Structure

The system automatically creates these tables:

- **users**: User accounts with tiers (visitor/unlimited)
- **sessions**: Session tracking
- **upgrade_requests**: Pending approval requests
- **contacts**: Interested users
- **knowledge_base**: Q&A database
- **conversations**: Chat history
- **unknown_questions**: Unanswered questions

## 🎛️ Admin Panel

Use the admin script to manage user requests:

```bash
# Interactive mode
python admin_approve.py

# Approve specific user
python admin_approve.py visitor_abc123
```

### Admin Commands:

1. **List pending requests** - See all upgrade requests
2. **Approve a user** - Grant unlimited access
3. **Show statistics** - View user metrics
4. **Exit** - Close admin panel

## 📱 Pushover Integration

When a user requests unlimited access, you receive a notification with:

- Username
- Email address
- Intent/reason for reaching out

You can then:
1. Review the request
2. Approve via admin script
3. Reach out to the user

## 🎨 UI Features

### Tab 1: Login / Sign Up
- **Visitor Access**: Generate instant credentials
- **Existing User**: Login with username/password

### Tab 2: Chat
- Real-time query counter
- Conversation history
- Query limit warnings

### Tab 3: Request Unlimited Access
- Email input
- Intent description
- Status tracking

### Tab 4: About
- System information
- Access tier comparison
- How it works guide

## 🔒 Security Features

- **Password Hashing**: SHA-256 encryption
- **Session Management**: Track user sessions
- **Query Limits**: Prevent abuse
- **Email Validation**: Basic format checking
- **Intent Requirements**: Minimum 10 characters

## 📈 Query Limit Logic

```python
Visitor Tier:
- Initial: 5 queries
- Warning: After 3 queries (2 remaining)
- Blocked: After 5 queries
- Can request upgrade anytime

Unlimited Tier:
- Unlimited queries
- No warnings
- Approved status
```

## 🎯 User Experience Flow

### First-Time Visitor:
```
1. Click "Get Visitor Credentials"
2. Save username/password
3. Go to Chat tab
4. Log in with credentials
5. Ask questions (5 max)
6. See query counter
```

### Requesting Upgrade:
```
1. Reach query limit
2. Go to "Request Unlimited Access" tab
3. Enter email + intent
4. Submit request
5. Receive confirmation
6. Wait for approval
7. Continue chatting with unlimited access
```

### Owner (You):
```
1. Receive Pushover notification
2. Run admin script
3. Review user's intent
4. Approve or reject
5. Reach out to user
```

## 🛠️ Customization

### Change Query Limits:

In `app_new.py`, modify the `create_visitor_account` method:

```python
query_limit=5  # Change to your preferred limit
```

### Modify UI Theme:

```python
with gr.Blocks(theme=gr.themes.Soft(), ...) as demo:
```

Available themes: `Soft()`, `Base()`, `Glass()`, `Monochrome()`

### Add More Tiers:

You can extend the system with additional tiers:
- Student: 10 queries
- Professional: 50 queries
- Premium: Unlimited

## 📝 Testing

### Test Visitor Account:
```bash
# Run app
python app_new.py

# In browser:
1. Go to Login tab
2. Click "Get Visitor Credentials"
3. Copy credentials
4. Go to Chat tab
5. Ask questions
```

### Test Upgrade Flow:
```bash
# After using 5 queries:
1. Go to "Request Unlimited Access"
2. Enter test@example.com
3. Enter intent
4. Check Pushover notification
5. Run: python admin_approve.py visitor_xxxxx
```

## 🐛 Troubleshooting

### Database locked error:
```bash
# Close any open connections
rm career_bot.db
python app_new.py  # Recreates DB
```

### Login not working:
- Check username/password carefully
- Usernames are case-sensitive
- Make sure you created credentials first

### No Pushover notifications:
- Verify PUSHOVER_TOKEN and PUSHOVER_USER in .env
- Test with: `python -c "from app_new import push; push('test')"`

## 📊 Monitoring

### Check user activity:
```python
python admin_approve.py
# Choose option 3: Show user statistics
```

### View all users:
```bash
sqlite3 career_bot.db "SELECT * FROM users;"
```

### View pending requests:
```bash
sqlite3 career_bot.db "SELECT * FROM upgrade_requests WHERE status='pending';"
```

## 🎁 Benefits

### For Visitors:
- ✅ Try before committing
- ✅ No signup friction
- ✅ Clear upgrade path
- ✅ Know what they're asking for

### For You:
- ✅ Filter serious inquiries
- ✅ Know user intent upfront
- ✅ Reduce spam
- ✅ Build quality connections
- ✅ Track engagement

## 🔄 Migration from Old App

To migrate from `app.py` to `app_new.py`:

```bash
# Backup existing database
cp career_bot.db career_bot_backup.db

# Run new app (creates new tables)
python app_new.py
```

The new tables won't interfere with existing data.

## 📚 API Reference

### UserManager Class:
- `create_visitor_account()` - Generate visitor credentials
- `authenticate(username, password)` - Login user
- `check_query_limit(username)` - Check remaining queries
- `request_upgrade(username, email, intent)` - Request unlimited access
- `approve_upgrade(username)` - Grant unlimited access

### Me Class (Enhanced):
- `chat(message, history, username)` - Process chat with user context
- `system_prompt(..., user_tier, queries_remaining)` - Dynamic system prompt

## 🎯 Best Practices

1. **Respond quickly** to upgrade requests (within 24 hours)
2. **Review intent carefully** before approving
3. **Reach out to approved users** to build relationships
4. **Monitor query patterns** for abuse
5. **Update knowledge base** based on unknown questions

## 📞 Support

For issues or questions, check:
- Database logs: `sqlite3 career_bot.db`
- Application logs: Console output
- Admin panel: `python admin_approve.py`

---

**Powered by:** OpenAI GPT-4o-mini, Gradio, SQLite, and Pushover
