        
        # Chat Section (First Tab - Default)
        with gr.Tab("💬 Chat"):
            # Welcome message directing to login
            welcome_text = f"""### 👋 Hello! Welcome to my AI Assistant

I'm here to help you learn about **{me.name}'s** professional experience, skills, and projects!

**To get started:**

Please visit the **'🔐 Login / Sign Up'** tab to create your free visitor account.

You'll get **5 free questions** to learn all about me! 🎉

Looking forward to our conversation! 😊"""
            
            login_status_display = gr.Markdown(welcome_text, visible=True)
            
            # Limit reached message
            limit_reached_display = gr.Markdown(visible=False)
            
            # Welcome message (shown after login)
            welcome_message = gr.Markdown(visible=False)
            
            gr.Markdown(f"### Ask me anything about {me.name}!")
            
            # Quick action cards
            with gr.Row(visible=False) as quick_actions:
                with gr.Column(scale=1):
                    gr.Markdown("**🚀 Quick Start**")
                    quick_btn1 = gr.Button("📊 Tell me about your experience", size="sm")
                    quick_btn2 = gr.Button("🛠️ What are your main skills?", size="sm")
                    quick_btn3 = gr.Button("💼 Show me your projects", size="sm")
                    quick_btn4 = gr.Button("🤝 How can we collaborate?", size="sm")
            
            chatbot = gr.Chatbot(type="messages", height=400)
            msg = gr.Textbox(
                label="Your message", 
                placeholder="Please visit the '🔐 Login / Sign Up' tab to get started...",
                interactive=False
            )
            
            with gr.Row():
                send_btn = gr.Button("Send", variant="primary", interactive=False)
                clear_btn = gr.Button("Clear")
            
            # Query counter display
            query_status = gr.Markdown()
            
            # Chat functions
            def respond(message, history, username):
                if not username or username == "visitor":
                    return history, "❌ Please login first! Go to the '🔐 Login / Sign Up' tab.", ""
                
                # Check if user has reached limit BEFORE processing
                user_manager = UserManager()
                can_query, current, limit = user_manager.check_query_limit(username)
                
                if not can_query:
                    return history, f"🚫 **Limit reached!** Please go to '⬆️ Request Unlimited Access' tab.", ""
                
                # Add user message to history
                history.append({"role": "user", "content": message})
                
                # Get bot response
                bot_response = me.chat(message, history, username)
                
                # Add bot response to history
                history.append({"role": "assistant", "content": bot_response})
                
                # Update query status
                can_query_after, current_after, limit_after = user_manager.check_query_limit(username)
                
                if limit_after == -1:
                    status_msg = f"✅ **Unlimited access** | Queries used: {current_after}"
                else:
                    remaining = limit_after - current_after
                    if remaining <= 0:
                        status_msg = f"🚫 **Limit reached!** Go to '⬆️ Request Unlimited Access' tab to continue."
                    elif remaining <= 2:
                        status_msg = f"⚠️ **{remaining} queries remaining** | Consider requesting unlimited access"
                    else:
                        status_msg = f"📊 **Queries:** {current_after}/{limit_after} | Remaining: {remaining}"
                
                return history, status_msg, ""
            
            # Enable/disable chat based on user status
            def update_chat_interface(username):
                if username and username != "visitor":
                    user_manager = UserManager()
                    user_data = user_manager.get_user_data(username)
                    
                    if user_data:
                        tier = user_data["tier"]
                        current = user_data["query_count"]
                        limit = user_data["query_limit"]
                        remaining = limit - current
                        
                        # Check if limit reached
                        if tier == "visitor" and remaining <= 0:
                            limit_msg = """### 🚫 Query Limit Reached

You've used all **5 free queries** as a visitor.

**To continue our conversation:**

Go to the **'Request Unlimited Access'** tab to:
- Provide your email address
- Share why you'd like to connect

I'll review your request and reach out to you soon!"""
                            
                            return (
                                gr.update(visible=False),
                                gr.update(value=limit_msg, visible=True),
                                gr.update(visible=False),
                                gr.update(visible=False),
                                gr.update(interactive=False, placeholder="Please request unlimited access to continue..."),
                                gr.update(interactive=False),
                                f"🚫 **Limit reached!** {current}/{limit} queries used",
                                []
                            )
                        
                        # Create welcome message
                        welcome_msg = ""
                        if tier == "unlimited":
                            welcome_msg = f"""### 👋 Welcome back!

You have **unlimited access**. Feel free to ask anything about my experience, skills, and projects!"""
                            status = "✅ **Unlimited access** | Ask away!"
                        else:
                            welcome_msg = f"""### 👋 Hello! I'm {me.name}'s AI assistant

I can help you learn about:
- 📊 **Professional Experience** - Career journey and achievements
- 🛠️ **Technical Skills** - Programming, AI/ML, Cloud technologies
- 💼 **Projects** - Notable work and contributions
- 🤝 **Collaboration** - How we can work together

**You have {remaining} questions available.** Use the quick start buttons below or type your own question!"""
                            status = f"✅ **Welcome!** | {remaining} queries remaining"
                        
                        # Start conversation with bot greeting
                        initial_history = [{
                            "role": "assistant", 
                            "content": f"Hello! 👋 I'm an AI assistant representing {me.name}. I'm here to answer your questions about professional experience, skills, projects, and potential collaborations. What would you like to know?"
                        }]
                        
                        return (
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(value=welcome_msg, visible=True),
                            gr.update(visible=True),
                            gr.update(interactive=True, placeholder="Ask me about my experience, skills, or projects..."),
                            gr.update(interactive=True),
                            status,
                            initial_history
                        )
                
                return (
                    gr.update(visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(interactive=False, placeholder="Please login first to start chatting..."),
                    gr.update(interactive=False),
                    "⚠️ Please login to start chatting",
                    []
                )
            
            # Quick action handlers
            def quick_action(question, history, username):
                return respond(question, history, username)
            
            quick_btn1.click(
                lambda h, u: quick_action("Tell me about your professional experience and background", h, u),
                inputs=[chatbot, current_username],
                outputs=[chatbot, query_status, msg]
            ).then(
                update_chat_interface,
                inputs=[current_username],
                outputs=[login_status_display, limit_reached_display, welcome_message, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            quick_btn2.click(
                lambda h, u: quick_action("What are your main technical skills and expertise?", h, u),
                inputs=[chatbot, current_username],
                outputs=[chatbot, query_status, msg]
            ).then(
                update_chat_interface,
                inputs=[current_username],
                outputs=[login_status_display, limit_reached_display, welcome_message, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            quick_btn3.click(
                lambda h, u: quick_action("Can you show me some of your notable projects?", h, u),
                inputs=[chatbot, current_username],
                outputs=[chatbot, query_status, msg]
            ).then(
                update_chat_interface,
                inputs=[current_username],
                outputs=[login_status_display, limit_reached_display, welcome_message, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            quick_btn4.click(
                lambda h, u: quick_action("I'm interested in collaboration opportunities. How can we work together?", h, u),
                inputs=[chatbot, current_username],
                outputs=[chatbot, query_status, msg]
            ).then(
                update_chat_interface,
                inputs=[current_username],
                outputs=[login_status_display, limit_reached_display, welcome_message, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            # Update chat interface when user logs in
            current_username.change(
                update_chat_interface,
                inputs=[current_username],
                outputs=[login_status_display, limit_reached_display, welcome_message, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            send_btn.click(
                respond,
                inputs=[msg, chatbot, current_username],
                outputs=[chatbot, query_status, msg]
            ).then(
                update_chat_interface,
                inputs=[current_username],
                outputs=[login_status_display, limit_reached_display, welcome_message, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            msg.submit(
                respond,
                inputs=[msg, chatbot, current_username],
                outputs=[chatbot, query_status, msg]
            ).then(
                update_chat_interface,
                inputs=[current_username],
                outputs=[login_status_display, limit_reached_display, welcome_message, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            clear_btn.click(lambda: ([], ""), outputs=[chatbot, query_status])
        
        # Login / Sign Up Section (Second Tab)
        with gr.Tab("🔐 Login / Sign Up"):
            gr.Markdown("### Choose your access level:")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### 🎫 Visitor Access (5 queries)")
                    visitor_btn = gr.Button("Get Visitor Credentials", variant="secondary")
                    visitor_output = gr.Markdown()
                
                with gr.Column():
                    gr.Markdown("#### 🔑 Approved User Login")
                    gr.Markdown("""
                    *Only for users who have been approved for unlimited access.*
                    
                    If you're a new visitor, use the button on the left.
                    """)
                    login_username = gr.Textbox(label="Username", placeholder="Enter your approved username")
                    login_password = gr.Textbox(label="Password", type="password", placeholder="Enter your password")
                    login_btn = gr.Button("Login", variant="primary")
                    login_output = gr.Markdown()
            
            
            def handle_login(username, password):
                success, message, user = login_user(username, password)
                if success:
                    return message, user, gr.update(), gr.update()
                return message, None, gr.update(), gr.update()
            
            def handle_visitor_creation(request: gr.Request):
                """Create visitor credentials with IP tracking and auto-login"""
                user_manager = UserManager()
                
                # Get client IP
                client_ip = None
                try:
                    if hasattr(request, 'client') and hasattr(request.client, 'host'):
                        client_ip = request.client.host
                except:
                    pass
                
                # Check IP limit
                if client_ip and user_manager.check_ip_visitor_limit(client_ip):
                    return """
⚠️ **Visitor account already created from this IP**

You've already created a visitor account in the last 24 hours from this IP address.

**What you can do:**
- Use your existing visitor credentials to login
- Wait 24 hours to create a new visitor account
- Request unlimited access if you've used your queries

If you lost your credentials, please contact support.
                    """, None
                
                username, password = user_manager.create_visitor_account(client_ip)
                
                credentials_text = f"""
# 🎉 Welcome! Your Visitor Credentials

**Username:** `{username}`  
**Password:** `{password}`  
**Query Limit:** 5 questions

⚠️ **Important:** Save these credentials! You'll need them to log back in.

---

✅ **You are now automatically logged in!**

**What you can do:**
✨ Ask about my background and experience
💼 Learn about my skills and projects  
🤝 Discuss collaboration opportunities
📧 Request unlimited access after your trial

**Next:** Go to the '💬 Chat' tab to start our conversation!
                """
                
                return credentials_text, username
            
            visitor_btn.click(
                handle_visitor_creation,
                outputs=[visitor_output, current_username]
            )
            
            login_btn.click(
                handle_login,
                inputs=[login_username, login_password],
                outputs=[login_output, current_username, login_username, login_password]
            )
        
        # Upgrade Request Section (Third Tab)
        with gr.Tab("⬆️ Request Unlimited Access"):
            gr.Markdown(f"""
            ### 🚀 Get Unlimited Access!
            
            Reached your query limit? Request unlimited access by providing:
            - Your email address
            - Your intent for reaching out to {me.name}
            
            {me.name} will review your request and reach out to you if approved.
            """)
            
            upgrade_username_display = gr.Textbox(label="Your Username (will be filled automatically)", interactive=False)
            upgrade_email = gr.Textbox(label="Email Address", placeholder="your.email@example.com")
            upgrade_intent = gr.Textbox(
                label="Why do you want to connect?",
                placeholder="I'm interested in discussing collaboration opportunities...",
                lines=5
            )
            upgrade_btn = gr.Button("Submit Request", variant="primary")
            upgrade_output = gr.Markdown()
            
            # Update username display when user logs in
            current_username.change(
                lambda x: x or "",
                inputs=[current_username],
                outputs=[upgrade_username_display]
            )
            
            upgrade_btn.click(
                request_unlimited_access,
                inputs=[current_username, upgrade_email, upgrade_intent],
                outputs=[upgrade_output]
            )
        
        # About Section
        with gr.Tab("ℹ️ About"):
            gr.Markdown(f"""
            ## About This Chatbot
            
            This AI assistant represents **{me.name}** and can answer questions about:
            - 📊 Professional background and experience
            - 🛠️ Technical skills and expertise
            - 🎓 Education and certifications
            - 💼 Projects and achievements
            
            ### Access Tiers:
            
            | Tier | Queries | Features |
            |------|---------|----------|
            | 🎫 Visitor | 5 | Basic Q&A access |
            | ✨ Unlimited | ∞ | Full access after approval |
            
            ### How It Works:
            1. Create a visitor account (5 free queries)
            2. Ask questions about {me.name}
            3. Request unlimited access by providing email + intent
            4. Get approved and enjoy unlimited conversations!
            
            ---
            
            **Powered by:** OpenAI GPT-4, RAG (Retrieval-Augmented Generation), and Gradio
            """)
    
    # Launch
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
