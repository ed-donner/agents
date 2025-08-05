"""
AI Interview Simulation
=======================

A sophisticated AI-to-AI interview simulation where:
1. User provides a job description
2. OpenAI acts as the interviewer asking tailored questions
3. Gemini acts as the candidate answering the questions
4. OpenAI evaluates Gemini's responses and provides feedback
5. The cycle continues for a full interview experience

This is perfect for learning interview patterns, question types, and ideal answer structures.

Author: Enhanced from Mock Interviewer concept
"""

from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import time

# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================

load_dotenv(override=True)

# Initialize AI clients
openai_client = OpenAI()
gemini_client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"), 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class InterviewQuestion:
    """Represents an interview question with AI responses"""
    question_number: int
    question_text: str
    category: str  # 'technical', 'behavioral', 'experience', 'problem-solving'
    gemini_answer: Optional[str] = None
    openai_score: Optional[int] = None
    openai_feedback: Optional[str] = None
    
@dataclass
class SimulationState:
    """Tracks the current state of the AI interview simulation"""
    job_description: str = ""
    candidate_profile: str = ""
    questions: List[InterviewQuestion] = field(default_factory=list)
    current_question_number: int = 0
    max_questions: int = 10
    simulation_started: bool = False
    simulation_ended: bool = False
    
    @property
    def questions_remaining(self) -> int:
        return max(0, self.max_questions - len(self.questions))
    
    @property
    def average_score(self) -> float:
        scored_questions = [q for q in self.questions if q.openai_score is not None]
        if not scored_questions:
            return 0.0
        return sum(q.openai_score for q in scored_questions) / len(scored_questions)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def push(text: str) -> None:
    """Send push notification via Pushover"""
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": os.getenv("PUSHOVER_TOKEN"),
                "user": os.getenv("PUSHOVER_USER"),
                "message": text,
            }
        )
        print(f"📱 Push notification sent: {text}")
    except Exception as e:
        print(f"❌ Failed to send push notification: {e}")

def format_simulation_summary(state: SimulationState) -> str:
    """Format a nice summary of the simulation results"""
    summary = f"""
## 🎭 AI Interview Simulation Complete!

**Job Role:** {state.job_description[:100]}...
**Questions Asked:** {len(state.questions)}
**Average Score:** {state.average_score:.1f}/10

### 📋 Question & Answer Summary:
"""
    
    for i, q in enumerate(state.questions, 1):
        summary += f"""
**Q{i}:** {q.question_text}
**Category:** {q.category}
**Gemini's Answer:** {q.gemini_answer[:200]}...
**Score:** {q.openai_score}/10
**Feedback:** {q.openai_feedback}
---
"""
    
    return summary

# ============================================================================
# AI INTERVIEW SIMULATION ENGINE
# ============================================================================

class AIInterviewSimulation:
    """
    Main class that orchestrates the AI-to-AI interview simulation
    """
    
    def __init__(self):
        """Initialize the simulation engine"""
        self.openai = OpenAI()
        self.simulation_state = SimulationState()
        
        # Load candidate profile for context
        self._load_candidate_profile()
        
        print("🎭 AI Interview Simulation initialized")
    
    def _load_candidate_profile(self) -> None:
        """Load candidate profile to provide context for questions"""
        try:
            # Load LinkedIn PDF
            reader = PdfReader("me/linkedin.pdf")
            linkedin_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    linkedin_text += text
            
            # Load summary
            with open("me/summary.txt", "r", encoding="utf-8") as f:
                summary_text = f.read()
            
            # Combine into candidate profile
            self.simulation_state.candidate_profile = f"""
CANDIDATE SUMMARY:
{summary_text}

LINKEDIN PROFILE:
{linkedin_text}
"""
            print("✅ Candidate profile loaded for context")
            
        except Exception as e:
            print(f"❌ Error loading candidate profile: {e}")
            self.simulation_state.candidate_profile = "Candidate profile unavailable"
    
    def generate_interview_question(self) -> InterviewQuestion:
        """
        Use OpenAI to generate the next interview question
        """
        question_number = len(self.simulation_state.questions) + 1
        
        # Build context for question generation
        previous_questions = [q.question_text for q in self.simulation_state.questions]
        previous_context = "\n".join([f"Q{i+1}: {q}" for i, q in enumerate(previous_questions)])
        
        question_prompt = f"""
You are a professional interviewer conducting a job interview. Generate the next interview question.

JOB DESCRIPTION:
{self.simulation_state.job_description}

CANDIDATE PROFILE:
{self.simulation_state.candidate_profile}

PREVIOUS QUESTIONS ASKED:
{previous_context}

INTERVIEW PROGRESS:
- Question #{question_number} of {self.simulation_state.max_questions}
- Questions remaining: {self.simulation_state.questions_remaining}

INSTRUCTIONS:
- Ask a relevant, insightful question based on the job requirements and candidate background
- Vary question types: technical, behavioral, experience-based, problem-solving
- Don't repeat previous questions
- Make it challenging but fair
- Consider the interview flow and build upon previous questions

Respond with ONLY valid JSON:
{{
    "question": "<your interview question>",
    "category": "<technical|behavioral|experience|problem-solving>",
    "reasoning": "<why this question is relevant>"
}}
"""
        
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": question_prompt}],
                temperature=0.7
            )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            
            # Handle potential markdown wrapping
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()
            
            result = json.loads(content)
            
            # Create InterviewQuestion object
            question = InterviewQuestion(
                question_number=question_number,
                question_text=result["question"],
                category=result["category"]
            )
            
            print(f"🤖 OpenAI generated question #{question_number}: {result['category']}")
            return question
            
        except Exception as e:
            print(f"❌ Failed to generate question: {e}")
            # Fallback question
            return InterviewQuestion(
                question_number=question_number,
                question_text="Tell me about your experience and how it relates to this role.",
                category="experience"
            )
    
    def get_gemini_answer(self, question: InterviewQuestion) -> str:
        """
        Use Gemini to answer the interview question
        """
        answer_prompt = f"""
You are a job candidate being interviewed for this position:

JOB DESCRIPTION:
{self.simulation_state.job_description}

YOUR BACKGROUND:
{self.simulation_state.candidate_profile}

The interviewer just asked you this question:
"{question.question_text}"

This is a {question.category} question.

INSTRUCTIONS:
- Answer as the candidate whose profile is provided above
- Be specific and use examples from your background
- Show enthusiasm and knowledge
- Keep answer focused and professional (2-3 paragraphs)
- Demonstrate how your experience relates to the job requirements
- Be authentic but highlight your strengths

Provide your answer:
"""
        
        try:
            response = gemini_client.chat.completions.create(
                model="gemini-2.0-flash",
                messages=[{"role": "user", "content": answer_prompt}],
                temperature=0.7
            )
            
            answer = response.choices[0].message.content.strip()
            print(f"🧠 Gemini provided answer ({len(answer)} chars)")
            return answer
            
        except Exception as e:
            print(f"❌ Failed to get Gemini answer: {e}")
            return "I would need to think more about this question to provide a comprehensive answer."
    
    def get_openai_evaluation(self, question: InterviewQuestion) -> Dict:
        """
        Use OpenAI to evaluate Gemini's answer
        """
        evaluation_prompt = f"""
You are an expert interview evaluator. Evaluate this candidate's answer.

JOB CONTEXT:
{self.simulation_state.job_description}

QUESTION ASKED ({question.category}):
{question.question_text}

CANDIDATE'S ANSWER:
{question.gemini_answer}

EVALUATION CRITERIA:
- Relevance to the question and job requirements
- Specific examples and details provided
- Communication clarity and structure
- Demonstration of skills/experience
- Enthusiasm and cultural fit indicators

Provide evaluation as JSON only:
{{
    "score": <number 1-10>,
    "feedback": "<detailed feedback explaining the score>",
    "strengths": "<what the candidate did well>",
    "improvements": "<areas for improvement>"
}}
"""
        
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": evaluation_prompt}],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Handle markdown wrapping
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()
            
            result = json.loads(content)
            print(f"📊 OpenAI evaluated answer - Score: {result['score']}/10")
            return result
            
        except Exception as e:
            print(f"❌ Failed to evaluate answer: {e}")
            return {
                "score": 5,
                "feedback": "Unable to evaluate due to technical error",
                "strengths": "Answer provided",
                "improvements": "Technical evaluation failed"
            }
    
    def run_single_qa_cycle(self) -> InterviewQuestion:
        """
        Run one complete question-answer-evaluation cycle
        """
        print(f"\n🔄 Starting Q&A cycle #{len(self.simulation_state.questions) + 1}")
        
        # Step 1: OpenAI generates question
        question = self.generate_interview_question()
        
        # Step 2: Gemini answers the question
        question.gemini_answer = self.get_gemini_answer(question)
        
        # Step 3: OpenAI evaluates the answer
        evaluation = self.get_openai_evaluation(question)
        question.openai_score = evaluation["score"]
        question.openai_feedback = evaluation["feedback"]
        
        # Add to simulation state
        self.simulation_state.questions.append(question)
        
        return question
    
    def chat(self, message: str, history: List) -> str:
        """
        Main chat function that handles the simulation
        """
        # Check if this is the job description input
        if not self.simulation_state.simulation_started:
            if len(message.strip()) > 50:  # Assume job descriptions are substantial
                self.simulation_state.job_description = message
                self.simulation_state.simulation_started = True
                print(f"📋 Job description received: {len(message)} characters")
                
                # Just acknowledge the job description - don't start automatically
                return f"""🎭 **AI Interview Simulation Ready!**

✅ **Job description received** ({len(message)} characters)

The simulation will now observe an AI-to-AI interview where:
- 🤖 **OpenAI** acts as the professional interviewer
- 🧠 **Gemini** acts as the candidate 
- 📊 **OpenAI** evaluates each response

**Ready to begin!** Type **"start"** or **"begin"** to watch the first question and answer cycle."""
        
        # Handle simulation commands
        if "start" in message.lower() or "begin" in message.lower():
            if not self.simulation_state.job_description:
                return "❌ Please provide a job description first."
            
            # Start with first question
            question = self.run_single_qa_cycle()
            
            # Check if this was the only question
            if self.simulation_state.questions_remaining <= 0:
                return f"""🎭 **AI Interview Simulation Started!**

{self.format_single_qa_result(question)}

🎯 **Interview Simulation Complete!**

{self.get_final_summary()}

Type **"summary"** for detailed analysis."""
            else:
                return f"""🎭 **AI Interview Simulation Started!**

{self.format_single_qa_result(question)}

**Questions remaining:** {self.simulation_state.questions_remaining}
Type **"next"** to continue to the next question..."""
        
        elif "next" in message.lower() or "continue" in message.lower():
            if self.simulation_state.questions_remaining <= 0:
                return f"""❌ **Interview Complete!** No more questions remaining.

{self.get_final_summary()}

Type **"summary"** for detailed analysis."""
            
            question = self.run_single_qa_cycle()
            
            # Check if this was the last question
            if self.simulation_state.questions_remaining <= 0:
                return f"""{self.format_single_qa_result(question)}

🎯 **Interview Simulation Complete!**

{self.get_final_summary()}

Type **"summary"** for detailed analysis."""
            else:
                return f"""{self.format_single_qa_result(question)}

**Questions remaining:** {self.simulation_state.questions_remaining}
Type **"next"** to continue to the next question..."""
        
        elif "summary" in message.lower() or "results" in message.lower():
            if not self.simulation_state.questions:
                return "❌ No interview simulation has been run yet."
            return format_simulation_summary(self.simulation_state)
        
        elif "start interview" in message.lower() or "begin" in message.lower():
            if not self.simulation_state.job_description:
                return "❌ Please provide a job description first."
            
            # Reset simulation
            self.simulation_state.questions = []
            self.simulation_state.simulation_ended = False
            
            # Start with first question
            question = self.run_single_qa_cycle()
            return f"""🎭 **Starting Fresh Interview Simulation...**

{self.format_single_qa_result(question)}

**Questions remaining:** {self.simulation_state.questions_remaining}
Type **"next"** to continue to the next question..."""
        
        else:
            if self.simulation_state.simulation_started:
                return """🎭 **AI Interview Simulation In Progress**

Available commands:
- **"start"** or **"begin"** - Start the interview simulation
- **"next"** - Continue to next question (after starting)
- **"summary"** - Show current results
- **"start interview"** - Restart simulation

The simulation will show you each question and answer in real-time!"""
            else:
                return """🎭 **AI Interview Simulation Ready**

**Step 1:** Paste a job description to set up the simulation
**Step 2:** Type **"start"** or **"begin"** to watch the AI interview begin

The system will then show you each question and answer cycle automatically!"""
    
    def run_full_simulation_legacy(self) -> str:
        """Legacy method - kept for reference but not used in new chat flow"""
        if not self.simulation_state.job_description:
            return "❌ Please provide a job description first."
        
        # Clear previous results
        self.simulation_state.questions = []
        
        results = "🎭 **Running Complete AI Interview Simulation...**\n\n"
        
        # Run all Q&A cycles
        for i in range(self.simulation_state.max_questions):
            if self.simulation_state.questions_remaining <= 0:
                break
                
            results += f"### Question {i+1}\n"
            question = self.run_single_qa_cycle()
            results += self.format_single_qa_result(question) + "\n"
            
            # Add a small delay to make it feel more natural
            time.sleep(0.5)
        
        # Mark simulation as ended
        self.simulation_state.simulation_ended = True
        
        # Add final summary
        results += f"\n🎯 **Simulation Complete!**\n"
        results += f"**Average Score:** {self.simulation_state.average_score:.1f}/10\n"
        results += f"**Total Questions:** {len(self.simulation_state.questions)}\n\n"
        results += "Use 'Summary' command for detailed analysis."
        
        # Send push notification
        summary_msg = f"AI Interview Simulation Complete! Average Score: {self.simulation_state.average_score:.1f}/10"
        push(summary_msg)
        
        return results
    
    def get_final_summary(self) -> str:
        """Get a concise final summary for the chat interface"""
        return f"""**Final Results:**
- **Questions Asked:** {len(self.simulation_state.questions)}
- **Average Score:** {self.simulation_state.average_score:.1f}/10
- **Simulation Status:** Complete ✅"""
    
    def format_single_qa_result(self, question: InterviewQuestion) -> str:
        """Format a single Q&A cycle result for chat display"""
        return f"""### Question {question.question_number} ({question.category})

**🤖 Interviewer:** {question.question_text}

**🧠 Candidate (Gemini):** {question.gemini_answer}

**📊 Score:** {question.openai_score}/10  
**💭 Feedback:** {question.openai_feedback}"""

# ============================================================================
# GRADIO INTERFACE
# ============================================================================

def create_simulation_interface():
    """Create and configure the Gradio interface"""
    
    simulator = AIInterviewSimulation()
    
    # Custom CSS
    css = """
    .gradio-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .chat-message {
        padding: 10px;
        margin: 5px 0;
        border-radius: 10px;
        line-height: 1.6;
    }
    """
    
    # Create interface
    interface = gr.ChatInterface(
        fn=simulator.chat,
        type="messages",
        title="🎭 AI Interview Simulation",
        description="""
        **Watch AI Interview AI!**
        
        📋 **Step 1:** Paste a job description to start
        🤖 **Step 2:** OpenAI will generate interview questions
        🧠 **Step 3:** Gemini will answer as the candidate
        📊 **Step 4:** OpenAI will evaluate and score the responses
        
        Perfect for learning interview patterns, question types, and ideal answer structures!
        """,
        examples=[
            "Software Engineer position requiring Python, React, and cloud technologies. We're looking for someone with 3+ years experience in full-stack development and strong problem-solving skills...",
            "Data Scientist role focusing on machine learning, statistical analysis, and Python/R programming. Experience with ML pipelines, data visualization, and cloud platforms preferred...",
            "Product Manager position requiring technical background, stakeholder management, and agile methodologies. 5+ years experience in tech products and team leadership..."
        ],
        css=css,
        theme=gr.themes.Soft()
    )
    
    return interface

# ============================================================================
# SCRIPT EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("🎭 Starting AI Interview Simulation...")
    print("📝 Make sure you have:")
    print("   - me/linkedin.pdf (candidate profile for context)")
    print("   - me/summary.txt (candidate summary for context)")
    print("   - OPENAI_API_KEY in .env")
    print("   - GOOGLE_API_KEY in .env")
    print("   - PUSHOVER_TOKEN and PUSHOVER_USER in .env (optional)")
    print("-" * 50)
    
    try:
        interface = create_simulation_interface()
        interface.launch(
            share=False,  # Set to True for public sharing
            debug=True,   # Enable debug mode for development
            show_error=True
        )
    except Exception as e:
        print(f"❌ Failed to launch application: {e}")
        print("Please check your environment setup and try again.")
