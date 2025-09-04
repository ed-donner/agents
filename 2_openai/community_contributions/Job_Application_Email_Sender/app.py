import os
import io
import base64
import asyncio
import streamlit as st
import sendgrid
from sendgrid.helpers.mail import (
    Mail, Email, To, Content,
    Attachment, FileContent, FileName, FileType, Disposition
)
from dotenv import load_dotenv
from typing import Dict
from agents import Agent, Runner, function_tool

# -------------------------
# Custom CSS for Professional UI Design
# -------------------------
st.markdown("""
<style>
    /* Main background gradient */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin: 1rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    /* App background */
    .stApp {
        background: linear-gradient(45deg, #f093fb 0%, #f5576c 25%, #4facfe 50%, #00f2fe 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Sidebar styling with complementary gradient */
    .css-1d391kg {
        background: linear-gradient(135deg, #8360c3 0%, #2ebf91 25%, #36d1dc 50%, #5b86e5 75%, #667eea 100%);
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        border: 1px solid rgba(255,255,255,0.1);
        animation: sidebarGradient 20s ease infinite;
    }
    
    @keyframes sidebarGradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .css-1d391kg {
        background-size: 300% 300%;
    }
    
    /* Sidebar header styling */
    .css-1d391kg h1 {
        color: #FFD700 !important;
        text-align: center;
        font-size: 1.8rem;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        margin-bottom: 1rem;
        padding: 0.5rem;
        background: linear-gradient(45deg, rgba(255,215,0,0.2), rgba(255,165,0,0.2));
        border-radius: 10px;
        border: 1px solid rgba(255,215,0,0.3);
    }
    
    /* Sidebar text styling */
    .css-1d391kg .css-1cpxqw2 {
        color: #ffffff !important;
        font-weight: 600;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    
    /* Sidebar input fields */
    .css-1d391kg .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.95) !important;
        border: 2px solid rgba(52, 152, 219, 0.5) !important;
        border-radius: 10px !important;
        color: #2c3e50 !important;
        caret-color: #2c3e50 !important;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(52, 152, 219, 0.2);
    }
    
    .css-1d391kg .stTextInput > div > div > input:focus {
        border-color: #FFD700 !important;
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.4);
        transform: translateY(-1px);
    }
    
    /* Sidebar labels */
    .css-1d391kg label {
        color: #FFD700 !important;
        font-weight: 700;
        font-size: 1rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        margin-bottom: 0.5rem;
    }
    
    /* Sidebar success message */
    .css-1d391kg .stAlert {
        background: linear-gradient(45deg, #27ae60, #2ecc71) !important;
        border: 1px solid rgba(39, 174, 96, 0.5);
        border-radius: 10px;
        color: white !important;
        font-weight: 600;
        text-align: center;
        box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
    }
    
    /* Sidebar divider */
    .css-1d391kg hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #FFD700, transparent);
        margin: 1.5rem 0;
    }
    
    /* Title styling - Solid black text */
    .main-title {
        text-align: center;
        color: #2c3e50 !important;
        font-size: 3rem;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(255,255,255,0.8);
        margin-bottom: 0.5rem;
    }
    
    .sub-title {
        text-align: center;
        color: #2c3e50 !important;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
        font-weight: 500;
    }
    
    /* Input field styling - Fixed cursor color */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: rgba(255, 255, 255, 0.95);
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 12px;
        color: #2c3e50;
        caret-color: #2c3e50 !important;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #4facfe;
        box-shadow: 0 0 20px rgba(79, 172, 254, 0.3);
        transform: translateY(-2px);
        caret-color: #2c3e50 !important;
    }
    
    /* Labels - Solid black */
    .css-16huue1, .css-1629p8f {
        color: #2c3e50 !important;
        font-weight: 600;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
        font-size: 1.1rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 700;
        font-size: 1.1rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 35px rgba(102, 126, 234, 0.6);
        background: linear-gradient(45deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(45deg, #FFD700, #FFA500);
        border-radius: 10px;
    }
    
    /* Success/Error messages */
    .stAlert {
        border-radius: 15px;
        border: none;
        backdrop-filter: blur(10px);
        background: rgba(255, 255, 255, 0.1);
        color: #2c3e50 !important;
        font-weight: 600;
    }
    
    /* Success message styling */
    .stSuccess {
        background: linear-gradient(45deg, #56ab2f, #a8e6cf) !important;
        box-shadow: 0 8px 25px rgba(86, 171, 47, 0.3);
        color: white !important;
    }
    
    /* Error message styling */
    .stError {
        background: linear-gradient(45deg, #ff416c, #ff4b2b) !important;
        box-shadow: 0 8px 25px rgba(255, 65, 108, 0.3);
        color: white !important;
    }
    
    /* Warning message styling */
    .stWarning {
        background: linear-gradient(45deg, #f093fb, #f5576c) !important;
        box-shadow: 0 8px 25px rgba(240, 147, 251, 0.3);
        color: white !important;
    }
    
    /* File uploader */
    .css-1cpxqw2 {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        border: 2px dashed rgba(255, 255, 255, 0.3);
        transition: all 0.3s ease;
    }
    
    .css-1cpxqw2:hover {
        border-color: #4facfe;
        background: rgba(79, 172, 254, 0.1);
    }
    
    /* Section headers - Solid black */
    .section-header {
        color: #2c3e50 !important;
        font-size: 1.8rem;
        font-weight: 700;
        text-align: center;
        margin: 2rem 0 1rem 0;
        text-shadow: 2px 2px 4px rgba(255,255,255,0.8);
    }
    
    /* Cards for previews and logs */
    .preview-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .log-entry {
        background: linear-gradient(45deg, rgba(255,255,255,0.9), rgba(255,255,255,0.8));
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #4facfe;
        backdrop-filter: blur(5px);
        color: #2c3e50 !important;
    }
    
    /* Download link styling */
    a {
        color: #4facfe !important;
        text-decoration: none;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    a:hover {
        color: #667eea !important;
        text-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
    }
    
    /* Spinner customization */
    .stSpinner > div {
        border-color: #4facfe transparent #4facfe transparent !important;
    }
    
    /* Text areas for preview - Fixed cursor color */
    .preview-textarea textarea {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #2c3e50 !important;
        caret-color: #2c3e50 !important;
        border-radius: 10px !important;
        border: 2px solid rgba(79, 172, 254, 0.3) !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* All text elements to solid black */
    .stMarkdown, .stText {
        color: #2c3e50 !important;
    }
    
    /* Footer styling */
    .footer-text {
        text-align: center;
        color: #2c3e50 !important;
        font-size: 0.9rem;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
    }
    
    /* Help text styling */
    .css-1cpxqw2 small {
        color: rgba(44, 62, 80, 0.7) !important;
        font-style: italic;
    }
    
    /* Preview card text */
    .preview-card * {
        color: #2c3e50 !important;
    }
    
    /* Additional cursor fixes for all input types */
    input, textarea, select {
        caret-color: #2c3e50 !important;
    }
    
    input:focus, textarea:focus, select:focus {
        caret-color: #2c3e50 !important;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(45deg, #667eea, #764ba2);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(45deg, #764ba2, #667eea);
    }
</style>
""", unsafe_allow_html=True)

# ... rest of your code remains the same ...


# -------------------------
# Helpers: safe asyncio runner for Streamlit
# -------------------------
def run_asyncio_tasks(coros):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        new_loop = asyncio.new_event_loop()
        return new_loop.run_until_complete(asyncio.gather(*coros))
    else:
        return loop.run_until_complete(asyncio.gather(*coros))

# -------------------------
# Load env
# -------------------------
load_dotenv()

# -------------------------
# Streamlit sidebar: API Keys
# -------------------------
st.sidebar.markdown("# 🔑 Configuration")
st.sidebar.markdown("---")
openai_api_key = st.sidebar.text_input("🤖 OpenAI API Key", type="password", help="Enter your OpenAI API key to enable AI features")
sendgrid_api_key = st.sidebar.text_input("📧 SendGrid API Key", type="password", help="Enter your SendGrid API key to send emails")

if not openai_api_key or not sendgrid_api_key:
    st.markdown("### ⚠️ Configuration Required")
    st.warning("Please enter both OpenAI and SendGrid API Keys in the sidebar to continue.")
    st.stop()
else:
    os.environ["OPENAI_API_KEY"] = openai_api_key
    os.environ["SENDGRID_API_KEY"] = sendgrid_api_key
    st.sidebar.success("✅ Configuration Complete!")

# -------------------------
# Applicant Agents (3 styles)
# -------------------------
instructions1 = "You are a professional job applicant. You write formal, serious application emails tailored to recruiters."
instructions2 = "You are a witty, engaging job applicant. You write friendly, engaging application emails that stand out."
instructions3 = "You are a concise, busy applicant. You write short, to-the-point application emails."

applicant1 = Agent(name="Professional Applicant", instructions=instructions1, model="gpt-4o-mini")
applicant2 = Agent(name="Engaging Applicant", instructions=instructions2, model="gpt-4o-mini")
applicant3 = Agent(name="Concise Applicant", instructions=instructions3, model="gpt-4o-mini")

# -------------------------
# Subject + HTML Agents
# -------------------------
subject_writer = Agent(
    name="Email subject writer",
    instructions="Write a subject line for a recruiter email that increases chances of response.",
    model="gpt-4o-mini",
)

html_converter = Agent(
    name="HTML email body converter",
    instructions="Convert a recruiter email text into a professional HTML email layout. "
                 "If a LinkedIn URL is present, make it clickable with an <a href> link. "
                 "Keep the HTML clean and mobile-friendly.",
    model="gpt-4o-mini",
)

# -------------------------
# Send Email Function Tool
# -------------------------
@function_tool
def send_html_email(
    sender: str,
    recipient: str,
    subject: str,
    html_body: str,
    resume_file: str = None,
) -> Dict[str, str]:
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email(sender)
    to_email = To(recipient)
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content)

    if resume_file:
        decoded_bytes = base64.b64decode(resume_file.encode())
        attachment = Attachment(
            FileContent(base64.b64encode(decoded_bytes).decode()),
            FileName("Resume.pdf"),
            FileType("application/pdf"),
            Disposition("attachment")
        )
        mail.attachment = attachment

    sg.client.mail.send.post(request_body=mail.get())
    return {"status": "success", "to": recipient, "subject": subject}

# -------------------------
# Separate callable function for direct use
# -------------------------
def send_email_direct(sender: str, recipient: str, subject: str, html_body: str, resume_file: str = None) -> Dict[str, str]:
    """Direct callable version of send_html_email for use with asyncio.to_thread"""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email(sender)
    to_email = To(recipient)
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content)

    if resume_file:
        decoded_bytes = base64.b64decode(resume_file.encode())
        attachment = Attachment(
            FileContent(base64.b64encode(decoded_bytes).decode()),
            FileName("Resume.pdf"),
            FileType("application/pdf"),
            Disposition("attachment")
        )
        mail.attachment = attachment

    sg.client.mail.send.post(request_body=mail.get())
    return {"status": "success", "to": recipient, "subject": subject}

# -------------------------
# Email Manager agent
# -------------------------
emailer_agent = Agent(
    name="Email Manager",
    instructions="""You are an Email Manager. You receive a draft and should:
1) Use the subject_writer tool to create a subject.
2) Use the html_converter tool to format the body into HTML (make LinkedIn clickable).
3) Use the send_html_email tool when asked to send (with resume).
""",
    tools=[
        subject_writer.as_tool("subject_writer", "Write recruiter email subject"),
        html_converter.as_tool("html_converter", "Convert recruiter email to HTML"),
        send_html_email  # ✅ pass FunctionTool directly
    ],
    model="gpt-4o-mini",
    handoff_description="Convert job application draft to HTML and send it",
)

# -------------------------
# Application Manager (drafts-only)
# -------------------------
tools_for_drafts = [
    applicant1.as_tool("applicant1", "Write a professional job application email"),
    applicant2.as_tool("applicant2", "Write an engaging job application email"),
    applicant3.as_tool("applicant3", "Write a concise job application email"),
]
application_manager_drafts = Agent(
    name="Application Manager (drafts only)",
    instructions="""
    You are an Application Manager. Generate three candidate application email drafts
    using provided applicant tools and return the single best draft (no sending).
    """,
    tools=tools_for_drafts,
    model="gpt-4o-mini",
)

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Job Application Email Sender", page_icon="📧", layout="wide")

# Main title with enhanced styling
st.markdown('<h1 class="main-title">📧 Job Application Email Sender</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Generate personalized job application emails with AI and send them automatically to multiple recruiters</p>', unsafe_allow_html=True)

# Create columns for better layout
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<h2 class="section-header">👤 Applicant Information</h2>', unsafe_allow_html=True)
    
    # Create sub-columns for form fields
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        applicant_name = st.text_input("📝 Full Name", help="Your complete name as it appears on your resume")
        applicant_email = st.text_input("📧 Email Address", help="The email address you want to send from")
        phone_number = st.text_input("📱 Phone Number", help="Your contact phone number")
    
    with info_col2:
        linkedin_link = st.text_input("🔗 LinkedIn Profile", help="Full LinkedIn profile URL (https://...)")
        role = st.text_input("🎯 Target Role", help="The position you're applying for")
        company = st.text_input("🏢 Company Name", help="The company you're applying to")
    
    extra_note = st.text_area("📋 Additional Notes", help="Any extra information to include in your application", height=100)

with col2:
    st.markdown('<h2 class="section-header">🎯 Recruiter Details</h2>', unsafe_allow_html=True)
    
    recruiter_names = st.text_area("👥 Recruiter Names", 
                                 placeholder="John Smith, Sarah Johnson, Mike Wilson", 
                                 help="Enter recruiter names separated by commas",
                                 height=100)
    
    recruiter_emails = st.text_area("📬 Recruiter Emails", 
                                   placeholder="john@company.com, sarah@company.com, mike@company.com", 
                                   help="Enter recruiter emails separated by commas (same order as names)",
                                   height=100)
    
    st.markdown('<h2 class="section-header">📎 Resume Upload</h2>', unsafe_allow_html=True)
    resume_file = st.file_uploader("📄 Upload Resume (PDF)", type=["pdf"], 
                                  help="Upload your resume in PDF format to attach to emails")

# Process resume file
if resume_file:
    encoded_resume = base64.b64encode(resume_file.read()).decode()
    st.session_state.resume_encoded = encoded_resume
    st.success(f"✅ Resume uploaded: {resume_file.name}")
else:
    st.session_state.resume_encoded = None

# Session state
if "drafts" not in st.session_state:
    st.session_state.drafts = {}
if "logs" not in st.session_state:
    st.session_state.logs = []

# -------------------------
# Template for drafts
# -------------------------
template = (
    "Write a recruiter cold email addressed to Dear {name}.\n\n"
    "Applicant: {applicant_name}\n"
    "Phone: {phone_number}\n"
    "LinkedIn: {linkedin_link}\n"
    "Role: {role}\n"
    "Company: {company}\n"
    "Extra Note: {extra_note}\n"
    "Sender Email: {applicant_email}\n"
    "Recruiter Email: {recruiter_email}\n\n"
    "(Resume will be attached separately; do not include resume contents in the body.)"
)

# -------------------------
# Async worker: produce draft for one recruiter
# -------------------------
async def produce_draft_for_recruiter(name, email):
    message = template.format(
        name=name,
        applicant_name=applicant_name,
        phone_number=phone_number,
        linkedin_link=linkedin_link,
        role=role,
        company=company,
        extra_note=extra_note,
        applicant_email=applicant_email,
        recruiter_email=email,
    )
    result = await Runner.run(application_manager_drafts, message)
    return email, result.final_output

# -------------------------
# Generate Button with enhanced styling
# -------------------------
st.markdown("---")
generate_col1, generate_col2, generate_col3 = st.columns([1, 2, 1])

with generate_col2:
    if st.button("🚀 Generate & Send Emails", key="generate_button"):
        if not applicant_name or not applicant_email or not recruiter_names or not recruiter_emails or not role:
            st.error("⚠️ Please fill in all required fields to continue.")
        else:
            recruiter_names_list = [n.strip() for n in recruiter_names.split(",") if n.strip()]
            recruiter_emails_list = [e.strip() for e in recruiter_emails.split(",") if e.strip()]

            if len(recruiter_names_list) != len(recruiter_emails_list):
                st.error("⚠️ Number of recruiter names and emails must match.")
            else:
                recruiters = list(zip(recruiter_names_list, recruiter_emails_list))
                st.session_state.drafts = {}
                st.session_state.logs = []

                progress_bar = st.progress(0)
                status_text = st.empty()
                total = len(recruiters)

                coros = [produce_draft_for_recruiter(n, e) for n, e in recruiters]

                with st.spinner("⏳ Generating personalized email drafts..."):
                    results = run_asyncio_tasks(coros)
                    for i, (email, draft) in enumerate(results, start=1):
                        st.session_state.drafts[email] = draft
                        progress_bar.progress(i / total)
                        status_text.text(f"✨ Generated draft for {email} ({i}/{total})")

                status_text.text("✅ All drafts generated! Now sending emails automatically...")
                st.success("🎉 Drafts generated successfully — emails are being sent automatically.")

                # Auto-send emails
                async def send_for_recipient_auto(recipient, draft, sender, resume_b64=None):
                    subj_coro = Runner.run(subject_writer, draft)
                    html_coro = Runner.run(html_converter, draft)
                    subj_res, html_res = await asyncio.gather(subj_coro, html_coro)
                    subject = subj_res.final_output
                    html = html_res.final_output
                    sent = await asyncio.to_thread(
                        send_email_direct, sender, recipient, subject, html, resume_b64
                    )
                    return {"to": recipient, "subject": subject, "sent": sent}

                send_coros = [
                    send_for_recipient_auto(recipient, draft, applicant_email, st.session_state.resume_encoded)
                    for recipient, draft in st.session_state.drafts.items()
                ]

                with st.spinner("📤 Sending emails to all recruiters..."):
                    send_results = run_asyncio_tasks(send_coros)
                    for r in send_results:
                        st.session_state.logs.append(r)

                st.success("🎊 All emails sent successfully by Application Manager! Check the results below.")

# -------------------------
# Preview & Logs with enhanced styling
# -------------------------
if st.session_state.drafts:
    st.markdown("---")
    st.markdown('<h2 class="section-header">📄 Email Previews</h2>', unsafe_allow_html=True)
    
    for i, (recipient, draft) in enumerate(st.session_state.drafts.items()):
        with st.container():
            st.markdown(f'<div class="preview-card">', unsafe_allow_html=True)
            st.markdown(f"**📧 To:** `{recipient}`")
            
            # Create columns for preview and download
            preview_col1, preview_col2 = st.columns([4, 1])
            
            with preview_col1:
                st.text_area("Email Content", draft, height=200, key=f"preview_{recipient}", 
                           help="This is the generated email content that will be sent")
            
            with preview_col2:
                b64 = base64.b64encode(draft.encode()).decode()
                href = f'<a href="data:file/txt;base64,{b64}" download="draft_{recipient.replace("@", "_at_")}.txt">📥 Download Draft</a>'
                st.markdown(f"<br><br>{href}", unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.logs:
    st.markdown("---")
    st.markdown('<h2 class="section-header">📜 Send Logs</h2>', unsafe_allow_html=True)
    
    for i, log in enumerate(st.session_state.logs):
        to = log.get("to")
        subject = log.get("subject")
        sent = log.get("sent")
        
        with st.container():
            st.markdown(f'<div class="log-entry">', unsafe_allow_html=True)
            st.markdown(f"**📩 Email #{i+1}**")
            st.markdown(f"**📧 Recipient:** `{to}`")
            st.markdown(f"**📋 Subject:** {subject}")
            st.markdown(f"**✅ Status:** {sent}")
            st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown('<p class="footer-text">Built with ❤️ using Streamlit and OpenAI • Powered by SendGrid</p>', unsafe_allow_html=True)
