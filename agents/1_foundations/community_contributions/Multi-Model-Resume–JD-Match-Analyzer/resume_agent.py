import streamlit as st
import os
from openai import OpenAI
from anthropic import Anthropic
import pdfplumber
from io import StringIO
from dotenv import load_dotenv
import pandas as pd
from multi_file_ingestion import load_and_split_resume

# Load environment variables
load_dotenv(override=True)
openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

openai = OpenAI()

# Streamlit UI
st.set_page_config(page_title="LLM Resume–JD Fit", layout="wide")
st.title("🧠 Multi-Model Resume–JD Match Analyzer")

# Inject custom CSS to reduce white space
st.markdown("""
    <style>
        .block-container {
            padding-top: 3rem; /* instead of 1rem */
            padding-bottom: 1rem;
        }
        .stMarkdown {
            margin-bottom: 0.5rem;
        }
        .logo-container img {
            width: 50px;
            height: auto;
            margin-right: 10px;
        }
        .header-row {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-top: 1rem; /* Add extra top margin here if needed */
        }
    </style>
""", unsafe_allow_html=True)

# File upload
resume_file = st.file_uploader("📄 Upload Resume (any file type)", type=None)
jd_file = st.file_uploader("📝 Upload Job Description (any file type)", type=None)

# Function to extract text from uploaded files
def extract_text(file):
    if file.name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    else:
        return StringIO(file.read().decode("utf-8")).read()


def extract_candidate_name(resume_text):
    prompt = f"""
You are an AI assistant specialized in resume analysis.

Your task is to get full name of the candidate from the resume.

Resume:
{resume_text}

Respond with only the candidate's full name.
""" 
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional resume evaluator."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content
        
        return content.strip()

    except Exception as e:
        return "Unknown"


# Function to build the prompt for LLMs
def build_prompt(resume_text, jd_text):
    prompt = f"""
You are an AI assistant specialized in resume analysis and recruitment. Analyze the given resume and compare it with the job description. 

Your task is to evaluate how well the resume aligns with the job description.


Provide a match percentage between 0 and 100, where 100 indicates a perfect fit.

Resume:
{resume_text}

Job Description:
{jd_text}

Respond with only the match percentage as an integer.
"""
    return prompt.strip()

# Function to get match percentage from OpenAI GPT-4
def get_openai_match(prompt):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional resume evaluator."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content
        digits = ''.join(filter(str.isdigit, content))
        return min(int(digits), 100) if digits else 0
    except Exception as e:
        st.error(f"OpenAI API Error: {e}")
        return 0

# Function to get match percentage from Anthropic Claude
def get_anthropic_match(prompt):
    try:
        model_name = "claude-3-7-sonnet-latest"
        claude = Anthropic()
        
        message = claude.messages.create(
            model=model_name,
            max_tokens=100,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        content = message.content[0].text
        digits = ''.join(filter(str.isdigit, content))
        return min(int(digits), 100) if digits else 0
    except Exception as e:
        st.error(f"Anthropic API Error: {e}")
        return 0

# Function to get match percentage from Google Gemini
def get_google_match(prompt):
    try:
        gemini = OpenAI(api_key=google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
        model_name = "gemini-2.0-flash"
        messages = [{"role": "user", "content": prompt}]
        response = gemini.chat.completions.create(model=model_name, messages=messages)
        content = response.choices[0].message.content
        digits = ''.join(filter(str.isdigit, content))
        return min(int(digits), 100) if digits else 0
    except Exception as e:
        st.error(f"Google Gemini API Error: {e}")
        return 0

# Function to get match percentage from Groq
def get_groq_match(prompt):
    try:
        groq = OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
        model_name = "llama-3.3-70b-versatile"
        messages = [{"role": "user", "content": prompt}]
        response = groq.chat.completions.create(model=model_name, messages=messages)
        answer = response.choices[0].message.content
        digits = ''.join(filter(str.isdigit, answer))
        return min(int(digits), 100) if digits else 0
    except Exception as e:
        st.error(f"Groq API Error: {e}")
        return 0

# Function to get match percentage from DeepSeek
def get_deepseek_match(prompt):
    try:
        deepseek = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1")
        model_name = "deepseek-chat"
        messages = [{"role": "user", "content": prompt}]
        response = deepseek.chat.completions.create(model=model_name, messages=messages)
        answer = response.choices[0].message.content
        digits = ''.join(filter(str.isdigit, answer))
        return min(int(digits), 100) if digits else 0
    except Exception as e:
        st.error(f"DeepSeek API Error: {e}")
        return 0

# Main action
if st.button("🔍 Analyze Resume Fit"):
    if resume_file and jd_file:
        with st.spinner("Analyzing..."):
            # resume_text = extract_text(resume_file)
            # jd_text = extract_text(jd_file)
            os.makedirs("temp_files", exist_ok=True)
            resume_path = os.path.join("temp_files", resume_file.name)
    
            with open(resume_path, "wb") as f:
                f.write(resume_file.getbuffer())
            resume_docs = load_and_split_resume(resume_path)
            resume_text = "\n".join([doc.page_content for doc in resume_docs])

            jd_path = os.path.join("temp_files", jd_file.name)  
            with open(jd_path, "wb") as f:
                f.write(jd_file.getbuffer())
            jd_docs = load_and_split_resume(jd_path)
            jd_text = "\n".join([doc.page_content for doc in jd_docs])

            candidate_name = extract_candidate_name(resume_text)
            prompt = build_prompt(resume_text, jd_text)

            # Get match percentages from all models
            scores = {
                "OpenAI GPT-4o Mini": get_openai_match(prompt),
                "Anthropic Claude": get_anthropic_match(prompt),
                "Google Gemini": get_google_match(prompt),
                "Groq": get_groq_match(prompt),
                "DeepSeek": get_deepseek_match(prompt),
            }

            # Calculate average score
            average_score = round(sum(scores.values()) / len(scores), 2)

            # Sort scores in descending order
            sorted_scores = sorted(scores.items(), reverse=False)

            # Display results
            st.success("✅ Analysis Complete")
            st.subheader("📊 Match Results (Ranked by Model)")

            # Show candidate name
            st.markdown(f"**👤 Candidate:** {candidate_name}")

            # Create and sort dataframe
            df = pd.DataFrame(sorted_scores, columns=["Model", "% Match"])
            df = df.sort_values("% Match", ascending=False).reset_index(drop=True)

            # Convert to HTML table
            def render_custom_table(dataframe):
                table_html = "<table style='border-collapse: collapse; width: auto;'>"
                # Table header
                table_html += "<thead><tr>"
                for col in dataframe.columns:
                    table_html += f"<th style='text-align: center; padding: 8px; border-bottom: 1px solid #ddd;'>{col}</th>"
                table_html += "</tr></thead>"

                # Table rows
                table_html += "<tbody>"
                for _, row in dataframe.iterrows():
                    table_html += "<tr>"
                    for val in row:
                        table_html += f"<td style='text-align: left; padding: 8px; border-bottom: 1px solid #eee;'>{val}</td>"
                    table_html += "</tr>"
                table_html += "</tbody></table>"
                return table_html

            # Display table
            st.markdown(render_custom_table(df), unsafe_allow_html=True)

            # Show average match
            st.metric(label="📈 Average Match %", value=f"{average_score:.2f}%")
    else:
        st.warning("Please upload both resume and job description.")
