#!/usr/bin/env python3
"""
Admin script to approve upgrade requests
Usage: 
    python admin_approve.py <username>  # Approve specific user
    python admin_approve.py             # Interactive mode
"""

import sys
import sqlite3
from datetime import datetime
import os
import secrets
import string
import hashlib

def approve_user(username):
    """Approve a user's upgrade request"""
    db_path = "career_bot.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute('SELECT username, email, tier, status FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ User '{username}' not found!")
        conn.close()
        return False
    
    print(f"\n👤 User: {user[0]}")
    print(f"📧 Email: {user[1]}")
    print(f"🎫 Current Tier: {user[2]}")
    print(f"📊 Status: {user[3]}")
    
    # Check if already approved
    if user[2] == "unlimited":
        print(f"\n⚠️  User '{username}' already has unlimited access!")
        conn.close()
        return True
    
    # Get upgrade request details
    cursor.execute('''
        SELECT email, intent, created_at 
        FROM upgrade_requests 
        WHERE username = ? AND status = 'pending'
        ORDER BY created_at DESC
        LIMIT 1
    ''', (username,))
    
    request = cursor.fetchone()
    
    if request:
        print(f"\n📝 Upgrade Request:")
        print(f"   Email: {request[0]}")
        print(f"   Intent: {request[1]}")
        print(f"   Requested: {request[2]}")
    
    # Confirm approval
    confirm = input("\n✅ Approve this user? (yes/no): ").lower().strip()
    
    if confirm not in ['yes', 'y']:
        print("❌ Approval cancelled.")
        conn.close()
        return False
    
    # Close the connection before calling approve_upgrade
    conn.close()
    
    # Import UserManager from app_new
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app_new import UserManager, send_pushover_notification
    
    # Approve and generate credentials
    user_manager = UserManager(db_path)
    result = user_manager.approve_upgrade(username)
    
    if not result["success"]:
        print(f"\n❌ Error approving user: {result.get('error', 'Unknown error')}")
        return False
    
    new_username = result["username"]
    new_password = result["password"]
    user_email = result["email"]
    
    print(f"\n" + "=" * 80)
    print(f"✅ User '{username}' has been approved and granted unlimited access!")
    print(f"=" * 80)
    print(f"\n� NEW LOGIN CREDENTIALS:")
    print(f"   Username: {new_username}")
    print(f"   Password: {new_password}")
    print(f"   Email: {user_email}")
    print(f"\n📧 Make sure to send these credentials to: {user_email}")
    print(f"\n⚠️  IMPORTANT: Save these credentials! They won't be shown again.")
    print("=" * 80)
    
    # Send PushOver notification with credentials
    send_pushover_notification(
        title=f"✅ User Approved: {new_username}",
        message=f"""User approved for unlimited access!

📧 Email: {user_email}
🔑 Username: {new_username}
🔒 Password: {new_password}

Send these credentials to the user at: {user_email}

Login URL: http://localhost:7860""",
        priority=1
    )
    
    print(f"\n📱 PushOver notification sent with credentials!")
    
    return True

def list_pending_requests():
    """List all pending upgrade requests"""
    db_path = "career_bot.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.username, COALESCE(ur.email, u.email) as email, ur.intent, ur.created_at, u.query_count, u.query_limit
        FROM upgrade_requests ur
        JOIN users u ON ur.username = u.username
        WHERE ur.status = 'pending'
        ORDER BY ur.created_at DESC
    ''')
    
    requests = cursor.fetchall()
    conn.close()
    
    if not requests:
        print("\n✅ No pending upgrade requests!")
        return
    
    print(f"\n📋 Pending Upgrade Requests ({len(requests)}):")
    print("=" * 80)
    
    for i, req in enumerate(requests, 1):
        print(f"\n{i}. Username: {req[0]}")
        print(f"   Email: {req[1]}")
        print(f"   Intent: {req[2]}")
        print(f"   Requested: {req[3]}")
        print(f"   Usage: {req[4]}/{req[5]} queries")
        print("-" * 80)

def show_user_stats():
    """Show user statistics"""
    db_path = "career_bot.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Count users by tier
    cursor.execute('SELECT tier, COUNT(*) FROM users GROUP BY tier')
    tier_counts = cursor.fetchall()
    
    # Count pending requests
    cursor.execute('SELECT COUNT(*) FROM upgrade_requests WHERE status = "pending"')
    pending_count = cursor.fetchone()[0]
    
    # Recent users
    cursor.execute('''
        SELECT username, tier, query_count, query_limit, created_at
        FROM users
        ORDER BY created_at DESC
        LIMIT 5
    ''')
    recent_users = cursor.fetchall()
    
    conn.close()
    
    print("\n📊 User Statistics:")
    print("=" * 80)
    
    print("\n🎫 Users by Tier:")
    for tier, count in tier_counts:
        print(f"   {tier}: {count}")
    
    print(f"\n⏳ Pending Requests: {pending_count}")
    
    print("\n👥 Recent Users:")
    for user in recent_users:
        print(f"   {user[0]} - {user[1]} - {user[2]}/{user[3]} queries - Created: {user[4]}")

if __name__ == "__main__":
    print("=" * 80)
    print("🔧 USER APPROVAL ADMIN PANEL")
    print("=" * 80)
    
    if len(sys.argv) > 1:
        # Approve specific user
        username = sys.argv[1]
        approve_user(username)
    else:
        # Show menu
        while True:
            print("\n\nOptions:")
            print("1. List pending upgrade requests")
            print("2. Approve a user")
            print("3. Show user statistics")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                list_pending_requests()
            elif choice == "2":
                username = input("Enter username to approve: ").strip()
                if username:
                    approve_user(username)
            elif choice == "3":
                show_user_stats()
            elif choice == "4":
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")
