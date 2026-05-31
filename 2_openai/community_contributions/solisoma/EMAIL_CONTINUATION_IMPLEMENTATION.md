# Email Continuation System - Implementation Guide

## 🎯 Goal
Enable users to continue conversations via email using **EXACT same pattern as `assesment.ipynb`**

---

## 🧠 Similar Pattern as in assesment.ipynb

```python
# Step 1: Create individual agents
clarification_agent = Agent(...)
question_generation_agent = Agent(...)
search_agent = Agent(...)
writer_agent = Agent(...)

# Step 2: Pass agents as tools to coordinator
planner_agent = Agent(
    name="DeepResearchCoordinator",
    instructions=PLANNER_INSTRUCTIONS,
    tools=[
        clarification_agent.as_tool(...),
        question_generation_agent.as_tool(...),
        search_agent.as_tool(...),
        writer_agent.as_tool(...)
    ]
)

# Step 3: Run coordinator - IT decides which agents to call
result = Runner.run(planner_agent, input=messages)
```

**Key: NO manual `Runner.run()` calls for sub-agents. Coordinator handles everything!**

---

## 🔄 Same Pattern for Email System

```python
# Step 1: Create individual agents
answer_agent = Agent(...)              # New: for quick questions
question_generation_agent = Agent(...) # Reuse from notebook
search_agent = Agent(...)              # Reuse from notebook  
writer_agent = Agent(...)              # Reuse from notebook

# Step 2: Pass agents as tools to coordinator
email_coordinator = Agent(
    name="EmailCoordinator",
    instructions=EMAIL_COORDINATOR_INSTRUCTIONS,
    tools=[
        answer_agent.as_tool(...),
        question_generation_agent.as_tool(...),
        search_agent.as_tool(...),
        writer_agent.as_tool(...)
    ]
)

# Step 3: Run coordinator - IT decides which agents to call
result = Runner.run(email_coordinator, input=user_message)
```

**Same philosophy: Coordinator decides everything, agents as tools!**

---

## 📋 Implementation Steps

### Step 1: SendGrid Webhook Setup

**Configure SendGrid:**

visit [How to setup webhook](https://www.twilio.com/docs/sendgrid/for-developers/tracking-events/getting-started-event-webhook) for full direction

**When sending emails, set:**
```python
reply_to = "reply@yourdomain.com"  # So replies come to webhook
```

---

### Step 2: Extract Email Data

**Webhook endpoint:**
```python
@app.post("/webhook/email")
async def handle_inbound_email(request: Request):
    form_data = await request.form()
    
    from_email = form_data.get("from")    # "User <user@email.com>"
    text_body = form_data.get("text")      # Email body
    
    # Extract clean data
    user_email = extract_email(from_email)  # "user@email.com"
    clean_content = remove_quoted_text(text_body)  # Only new content
    
    # Process with agent
    await process_with_agent(user_email, clean_content)
    
    return {"status": "received"}
```

**Helper functions:**
```python
def extract_email(from_field):
    # "John Doe <john@example.com>" → "john@example.com"
    # Use regex: r'<(.+?)>' or split on < >

def remove_quoted_text(body):
    # Remove lines starting with ">"
    # Remove "On [date]..." lines
    # Remove "---" separators
    # Return only new content
```

---

### Step 3: Create Individual Agents

**Agent 1: Answer simple questions**
```python
answer_agent = Agent(
    name="AnswerAgent",
    instructions="""
    Answer the user's question concisely and professionally.
    Keep response brief (2-3 paragraphs) for email.
    Be friendly and invite further questions.
    """,
    model="gpt-4o-mini"
)
```

**Agents 2-4: Reuse from assesment.ipynb**
```python
# Import or copy from your notebook
question_generation_agent = Agent(...)  # Same as notebook
search_agent = Agent(...)                # Same as notebook
writer_agent = Agent(...)                # Same as notebook
```

---

### Step 4: Create Email Coordinator

**Coordinator instructions:**
```python
EMAIL_COORDINATOR_INSTRUCTIONS = """
You are the Email Coordinator for Deep Research Assistant.

Analyze the user's email and decide which agents to call:

SCENARIO A - SIMPLE QUESTION:
User is asking for clarification or has a quick question.
ACTION: Call answer_agent, then stop

SCENARIO B - RESEARCH REQUEST:
User wants comprehensive research on a topic.
Keywords: "research", "investigate", "find out", "tell me about"
ACTION: Call agents sequentially:
1. question_generation_agent (create search queries)
2. search_agent (execute searches)
3. writer_agent (synthesize report)

YOU decide which scenario it is and which agents to call.
For research, skip clarification - generate queries directly.

Context available:
- User email: {user_email}
- User message: {message}
"""
```

**Pass agents as tools:**
```python
email_coordinator = Agent(
    name="EmailCoordinator",
    instructions=EMAIL_COORDINATOR_INSTRUCTIONS,
    tools=[
        answer_agent.as_tool(
            tool_name="answer_agent",
            tool_description="Answer simple questions quickly and concisely"
        ),
        question_generation_agent.as_tool(
            tool_name="question_generation_agent",
            tool_description="Generate diverse search queries for research topics"
        ),
        search_agent.as_tool(
            tool_name="search_agent",
            tool_description="Execute web searches and return summaries"
        ),
        writer_agent.as_tool(
            tool_name="writer_agent",
            tool_description="Synthesize search results into comprehensive report"
        )
    ],
    model="gpt-4o-mini"
)
```

---

### Step 5: Process Email with Agent

**Main processing function:**
```python
async def process_with_agent(user_email, content):
    """
    Let email_coordinator decide everything.
    NO manual if/else, NO manual Runner.run() for sub-agents!
    """
    try:
        # Build context
        context = f"""
        User email: {user_email}
        User message: {content}
        
        Analyze and decide which agents to call.
        """
        
        # Run coordinator - it handles everything
        result = await Runner.run(
            email_coordinator,
            message=context
        )
        
        # Extract final output (should always exist from Runner.run)
        response = result.final_output
        
        # Send email with response
        send_email(
            to=user_email,
            subject=determine_subject(content),
            body=format_email(response)
        )
        
    except Exception as e:
        print(f"Error: {str(e)}")
        send_error_email(user_email)
```

**Key: Just like your notebook, you only call `Runner.run()` on the coordinator!**

---

### Step 6: Email Sending

**Send email function:**
```python
def send_email(to, subject, body):
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    
    message = Mail(
        from_email=Email("research@yourdomain.com", "Deep Research Assistant"),
        to_emails=To(to),
        subject=subject,
        html_content=Content("text/html", body)
    )
    
    # Critical: Set reply-to for webhook loop
    message.reply_to = Email("reply@yourdomain.com")
    
    sg.client.mail.send.post(request_body=message.get())
```

**Email templates:**

**For questions:**
```html
<html>
<body>
    <p>Hi there,</p>
    <p>Thanks for your question!</p>
    <div style="padding: 15px; background: #f5f5f5; border-left: 4px solid #4CAF50;">
        {ANSWER}
    </div>
    <p>Need detailed research? Reply with "Research [topic]"</p>
    <p>Best regards,<br>Deep Research Assistant</p>
</body>
</html>
```

**For research:**
```html
<html>
<head>
    <style>
        .header { background: linear-gradient(135deg, #667eea, #764ba2); 
                  color: white; padding: 30px; text-align: center; }
        .report { padding: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Research Report</h1>
    </div>
    <div class="report">
        {MARKDOWN_REPORT_AS_HTML}
    </div>
    <p>Reply to this email with questions or new research topics!</p>
</body>
</html>
```

---

## 🎯 How It Works

### Scenario 1: Question
```
1. User emails: "What are the ethical concerns you mentioned?"
2. Webhook receives → extract & clean
3. email_coordinator receives message
4. Coordinator analyzes: "This is a question"
5. Coordinator calls: answer_agent.as_tool()
6. Answer agent generates response
7. Send email with answer (5-10 seconds)
✅ Done
```

### Scenario 2: Research Request
```
1. User emails: "Research quantum computing in cryptography"
2. Webhook receives → extract & clean
3. email_coordinator receives message
4. Coordinator analyzes: "This is research"
5. Coordinator calls agents sequentially:
   - question_generation_agent.as_tool() → queries
   - search_agent.as_tool() → summaries
   - writer_agent.as_tool() → report
6. Send email with full report (2-3 minutes)
✅ Done
```

**Key: Coordinator orchestrates everything. You never manually call `Runner.run()` on sub-agents!**

---

## 🔑 Key Differences from Gradio App

| Aspect | Gradio (assesment.ipynb) | Email Webhook |
|--------|--------------------------|---------------|
| **Pattern** | ✅ Coordinator + agents as tools | ✅ Same pattern |
| **Coordinator** | planner_agent | email_coordinator |
| **Sub-agents** | clarification, query, search, writer | answer, query, search, writer |
| **Clarification** | Always asks first | Skip (email context) |
| **Input** | Chat messages | Email content |
| **Output** | Gradio interface | Email response |

**Same agent orchestration philosophy, different input/output channels!**

---

## 📝 Complete Example

```python
# 1. Create agents
answer_agent = Agent(name="AnswerAgent", instructions="...", model="gpt-4o-mini")
# question_generation_agent, search_agent, writer_agent from notebook

# 2. Create coordinator with agents as tools
email_coordinator = Agent(
    name="EmailCoordinator",
    instructions=EMAIL_COORDINATOR_INSTRUCTIONS,
    tools=[
        answer_agent.as_tool(tool_name="answer_agent", tool_description="..."),
        question_generation_agent.as_tool(tool_name="question_generation_agent", tool_description="..."),
        search_agent.as_tool(tool_name="search_agent", tool_description="..."),
        writer_agent.as_tool(tool_name="writer_agent", tool_description="...")
    ],
    model="gpt-4o-mini"
)

# 3. Webhook receives email
@app.post("/webhook/email")
async def handle_inbound_email(request: Request):
    form_data = await request.form()
    user_email = extract_email(form_data.get("from"))
    clean_content = remove_quoted_text(form_data.get("text"))
    
    # 4. Process with coordinator
    await process_with_agent(user_email, clean_content)
    return {"status": "received"}

# 5. Coordinator decides and executes
async def process_with_agent(user_email, content):
    context = f"User: {user_email}\nMessage: {content}"
    
    # Single Runner.run() call - coordinator handles the rest
    result = await Runner.run(email_coordinator, message=context)
    
    # Runner.run() always returns result with final_output
    response = result.final_output
    send_email(to=user_email, subject="Re: Your Message", body=format_email(response))
```

---

## 💡 Key Principles

1. **Agents as tools** - Use `.as_tool()` to pass agents to coordinator
2. **Single orchestrator** - Only call `Runner.run()` on coordinator
3. **Agent decides** - Coordinator analyzes and calls the right agents
4. **Sequential flow** - For research: query → search → write happens automatically
5. **Reuse agents** - Same agents from `assesment.ipynb` for search/write
6. **No manual routing** - No if/else statements for classification

---

## 🆘 Troubleshooting

**Coordinator not calling agents:**
- Check agent instructions are clear about when to call which agent
- Ensure `.as_tool()` includes good `tool_description`
- Verify `tools=[]` parameter is set on coordinator

**Coordinator calling wrong agent:**
- Refine instructions with more examples
- Make tool descriptions more specific
- Test with edge cases

**Research not working:**
- Ensure question_generation, search, writer agents match notebook exactly
- Check coordinator instructions mention sequential calling
- Verify agents can be called without clarification

---

## 🎓 Summary

This implements email continuation using **your exact pattern from assesment.ipynb**:

**Your notebook:**
```
planner_agent → calls → [clarification, query, search, writer] as tools
```

**Email system:**
```
email_coordinator → calls → [answer, query, search, writer] as tools
```

**Same principles:**
- ✅ Create individual agents
- ✅ Pass agents as tools using `.as_tool()`
- ✅ Coordinator decides which agents to call
- ✅ Only one `Runner.run()` call (on coordinator)
- ✅ No manual orchestration

**Different parts:**
- Input: Email instead of chat
- Output: Email instead of Gradio
- Skip clarification for research (email provides context)

**Result: Clean, agent-driven email continuation system! 🚀📧**
