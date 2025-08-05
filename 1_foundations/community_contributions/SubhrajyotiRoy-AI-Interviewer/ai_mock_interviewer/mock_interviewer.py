"""
Mock Interview Chatbot
======================

A sophisticated AI-powered mock interviewer that:
1. Takes a job description as input
2. Conducts a tailored interview based on candidate's LinkedIn profile
3. Asks max 10 questions covering technical, behavioral, and experience areas
4. Uses dual LLM system: OpenAI for conversation, Gemini for answer evaluation
5. Provides real-time scoring and final interview summary
6. Sends push notifications for unanswered questions

Author: Enhanced from Lab 3 & 4 concepts
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
class Question:
    """Represents an interview question with metadata"""
    text: str
    category: str  # 'technical', 'behavioral', 'experience', 'problem-solving'
    max_score: int = 10
    actual_score: Optional[int] = None
    answer: Optional[str] = None
    evaluation_feedback: Optional[str] = None

@dataclass
class InterviewState:
    """Tracks the current state of the interview"""
    job_description: str = ""
    questions_asked: List[Question] = field(default_factory=list)
    current_question_index: int = 0
    total_score: int = 0
    max_questions: int = 10
    interview_started: bool = False
    interview_ended: bool = False
    
    @property
    def questions_remaining(self) -> int:
        return max(0, self.max_questions - len(self.questions_asked))
    
    @property
    def final_score_percentage(self) -> float:
        if not self.questions_asked:
            return 0.0
        
        # Calculate based on total questions asked, each worth max_score points
        total_questions = len(self.questions_asked)
        total_possible = total_questions * 10  # Each question is worth 10 points max
        
        # Use the running total_score which accumulates actual scores
        return (self.total_score / total_possible) * 100 if total_possible > 0 else 0.0

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

# ============================================================================
# TOOL FUNCTIONS
# ============================================================================

def evaluate_answer(question: str, answer: str, job_context: str) -> Dict:
    """
    Uses Gemini to evaluate the candidate's answer and provide a score
    
    Args:
        question: The interview question that was asked
        answer: The candidate's response
        job_context: Relevant job description context
    
    Returns:
        Dict with score (0-10) and feedback
    """
    evaluation_prompt = f"""
    You are an expert interview evaluator. Please evaluate this candidate's answer.
    
    JOB CONTEXT: {job_context}
    
    QUESTION ASKED: {question}
    
    CANDIDATE'S ANSWER: {answer}
    
    Please provide:
    1. A score from 0-10 (10 being excellent, 0 being completely inadequate)
    2. Brief feedback explaining the score
    
    Consider:
    - Relevance to the question
    - Technical accuracy (if applicable)
    - Communication clarity
    - Depth of knowledge demonstrated
    - Alignment with job requirements
    
    IMPORTANT: Respond with ONLY valid JSON. Do not include markdown formatting, code blocks, or any other text.
    
    {{
        "score": <number 0-10>,
        "feedback": "<brief explanation of score>"
    }}
    """
    
    try:
        messages = [{"role": "user", "content": evaluation_prompt}]
        response = gemini_client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=messages
        )
        
        # Get the raw response content
        raw_content = response.choices[0].message.content.strip()
        print(f"🔍 Raw Gemini response: {raw_content[:100]}...")  # Debug print
        
        # Try to extract JSON if wrapped in markdown
        content = raw_content
        if "```json" in content:
            # Extract JSON from markdown code block
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            # Extract from generic code block
            start = content.find("```") + 3
            end = content.find("```", start)
            content = content[start:end].strip()
        
        # Parse the JSON
        result = json.loads(content)
        print(f"📊 Answer evaluated - Score: {result['score']}/10")
        return {
            "score": result["score"],
            "feedback": result["feedback"],
            "status": "success"
        }
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"❌ Raw content was: {raw_content}")
        return {
            "score": 5,  # Default middle score
            "feedback": "Unable to parse evaluation response - defaulting to neutral score",
            "status": "error"
        }
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return {
            "score": 5,  # Default middle score
            "feedback": "Unable to evaluate answer due to technical error",
            "status": "error"
        }

def record_unanswered_question(question: str) -> Dict:
    """
    Records when a candidate cannot answer a question
    Sends push notification to the interviewer
    """
    message = f"🚫 Interview Question Skipped: {question}"
    push(message)
    print(f"📝 Recorded unanswered question: {question}")
    return {"recorded": "unanswered_question", "status": "success"}

def end_interview(final_score: float, total_questions: int) -> Dict:
    """
    Officially ends the interview and sends summary
    """
    summary = f"🎯 Interview Completed!\nFinal Score: {final_score:.1f}%\nQuestions Asked: {total_questions}"
    push(summary)
    print(f"✅ Interview ended - Final score: {final_score:.1f}%")
    return {"interview_ended": True, "final_score": final_score}

# ============================================================================
# TOOL SCHEMAS FOR OPENAI
# ============================================================================

evaluate_answer_json = {
    "name": "evaluate_answer",
    "description": "Evaluate the candidate's answer using Gemini AI and provide a score out of 10",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The interview question that was asked"
            },
            "answer": {
                "type": "string", 
                "description": "The candidate's response to evaluate"
            },
            "job_context": {
                "type": "string",
                "description": "Relevant context from the job description"
            }
        },
        "required": ["question", "answer", "job_context"],
        "additionalProperties": False
    }
}

record_unanswered_question_json = {
    "name": "record_unanswered_question",
    "description": "Record when a candidate says they don't know or cannot answer a question",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            }
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

end_interview_json = {
    "name": "end_interview", 
    "description": "End the interview when maximum questions reached and provide final summary",
    "parameters": {
        "type": "object",
        "properties": {
            "final_score": {
                "type": "number",
                "description": "The final calculated score percentage"
            },
            "total_questions": {
                "type": "integer", 
                "description": "Total number of questions asked"
            }
        },
        "required": ["final_score", "total_questions"],
        "additionalProperties": False
    }
}

# Combine all tools
interview_tools = [
    {"type": "function", "function": evaluate_answer_json},
    {"type": "function", "function": record_unanswered_question_json}, 
    {"type": "function", "function": end_interview_json}
]

# ============================================================================
# MAIN MOCK INTERVIEWER CLASS
# ============================================================================

class MockInterviewer:
    """
    AI-powered mock interviewer that conducts tailored job interviews
    """
    
    def __init__(self):
        """Initialize the interviewer with candidate data"""
        self.openai = OpenAI()
        self.name = "Subhrajyoti Roy"
        
        # Load candidate profile data
        self._load_candidate_profile()
        
        # Initialize interview state
        self.interview_state = InterviewState()
        
        print(f"🎭 Mock Interviewer initialized for {self.name}")
    
    def _load_candidate_profile(self) -> None:
        """Load candidate's LinkedIn profile and summary"""
        try:
            # Load LinkedIn PDF
            reader = PdfReader("me/linkedin.pdf")
            self.linkedin = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    self.linkedin += text
            
            # Load summary
            with open("me/summary.txt", "r", encoding="utf-8") as f:
                self.summary = f.read()
                
            print("✅ Candidate profile loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading candidate profile: {e}")
            self.linkedin = "Profile unavailable"
            self.summary = "Summary unavailable"
    
    def handle_tool_call(self, tool_calls) -> List[Dict]:
        """
        Execute tool functions called by the AI interviewer
        
        Args:
            tool_calls: List of tool calls from OpenAI response
            
        Returns:
            List of tool execution results
        """
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            print(f"🔧 Tool called: {tool_name}")
            print(f"📋 Tool arguments: {arguments}")
            print(f"📊 Current interview state - Questions asked: {len(self.interview_state.questions_asked)}")
            
            # Get the tool function dynamically
            tool_function = globals().get(tool_name)
            
            if tool_function:
                try:
                    result = tool_function(**arguments)
                    
                    # Special handling for different tool types
                    if tool_name == "evaluate_answer":
                        self._update_score(arguments, result)
                    elif tool_name == "end_interview":
                        self.interview_state.interview_ended = True
                        print("🏁 Interview marked as ended")
                    elif tool_name == "record_unanswered_question":
                        print("❌ Unanswered question recorded")
                    
                    results.append({
                        "role": "tool",
                        "content": json.dumps(result),
                        "tool_call_id": tool_call.id
                    })
                    
                except Exception as e:
                    print(f"❌ Tool execution failed: {e}")
                    results.append({
                        "role": "tool", 
                        "content": json.dumps({"error": str(e)}),
                        "tool_call_id": tool_call.id
                    })
            else:
                print(f"❌ Tool function not found: {tool_name}")
                results.append({
                    "role": "tool",
                    "content": json.dumps({"error": f"Tool {tool_name} not found"}),
                    "tool_call_id": tool_call.id
                })
        
        return results
    
    def _update_score(self, arguments: Dict, result: Dict) -> None:
        """Update interview state with evaluation results"""
        if result.get("status") == "success" and "score" in result:
            # Add to total score
            score = result["score"]
            self.interview_state.total_score += score
            
            # Update current question if exists
            if self.interview_state.questions_asked:
                current_q = self.interview_state.questions_asked[-1]
                current_q.actual_score = score
                current_q.evaluation_feedback = result.get("feedback", "")
            
            print(f"📈 Score updated: +{score} points (Total: {self.interview_state.total_score})")
    
    def system_prompt(self) -> str:
        """
        Generate the system prompt for the AI interviewer
        
        Returns:
            Comprehensive system prompt with context and instructions
        """
        base_prompt = f"""
You are a professional AI interviewer conducting a mock job interview for {self.name}.

## INTERVIEW OBJECTIVES:
- Conduct a structured interview with a MAXIMUM of {self.interview_state.max_questions} questions
- Ask questions tailored to both the job requirements and candidate's background
- Cover multiple areas: technical skills, past experience, behavioral questions, problem-solving
- ONLY use your evaluation tool AFTER the candidate provides an answer to your question
- ONLY use record_unanswered_question tool if the candidate explicitly says "I don't know" or refuses to answer
- ONLY use end_interview tool when you have asked {self.interview_state.max_questions} questions AND received answers

## INTERVIEW FLOW:
1. First interaction: Expect the user to provide a job description
2. Once you have the job description, begin the interview by asking ONE question
3. Wait for the candidate's answer
4. After receiving an answer, use evaluate_answer tool to score it
5. Ask the next question
6. Repeat until you have asked {self.interview_state.max_questions} questions
7. Only then use end_interview tool

## QUESTION CATEGORIES TO COVER:
- Technical skills relevant to the job
- Past experience and projects
- Behavioral/situational questions
- Problem-solving scenarios
- Cultural fit and motivation

## CURRENT INTERVIEW STATUS:
- Questions asked so far: {len(self.interview_state.questions_asked)}
- Questions remaining: {self.interview_state.questions_remaining}
- Interview started: {self.interview_state.interview_started}
- Job description provided: {"Yes" if self.interview_state.job_description else "No"}

## CANDIDATE PROFILE:
### Summary:
{self.summary}

### LinkedIn Profile:
{self.linkedin}

## IMPORTANT RULES:
- Be professional but conversational
- Ask ONE question at a time and WAIT for the answer
- Do NOT use any tools when asking a question - just ask the question
- ONLY use evaluate_answer tool after receiving a candidate's response
- Do NOT assume the candidate cannot answer - wait for their response
- Track your question count carefully
- Only use end_interview tool when you have completed all {self.interview_state.max_questions} questions

Remember: You are evaluating {self.name} for a specific role. Make questions relevant and challenging but fair.
"""
        
        if self.interview_state.job_description:
            base_prompt += f"\n\n## JOB DESCRIPTION:\n{self.interview_state.job_description}\n"
        
        return base_prompt
    
    def chat(self, message: str, history: List) -> str:
        """
        Main chat function that handles the interview conversation
        
        Args:
            message: User's input message
            history: Conversation history
            
        Returns:
            AI interviewer's response
        """
        # Check if this is the job description (first meaningful input)
        if not self.interview_state.interview_started and not self.interview_state.job_description:
            if len(message.strip()) > 50:  # Assume job descriptions are substantial
                self.interview_state.job_description = message
                self.interview_state.interview_started = True
                print(f"📋 Job description received: {len(message)} characters")
        
        # Build message chain
        messages = [
            {"role": "system", "content": self.system_prompt()}
        ] + history + [
            {"role": "user", "content": message}
        ]
        
        # Interview conversation loop
        done = False
        max_iterations = 5  # Prevent infinite loops
        iteration_count = 0
        
        while not done and iteration_count < max_iterations:
            iteration_count += 1
            
            try:
                response = self.openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=interview_tools,
                    temperature=0.7
                )
                
                choice = response.choices[0]
                
                if choice.finish_reason == "tool_calls":
                    # Execute tools
                    message_obj = choice.message
                    tool_calls = message_obj.tool_calls
                    
                    tool_results = self.handle_tool_call(tool_calls)
                    
                    # Add assistant message and tool results to conversation
                    messages.append(message_obj)
                    messages.extend(tool_results)
                    
                    # Continue the loop for next response
                    
                else:
                    # Regular response, we're done
                    done = True
                    final_response = choice.message.content
                    
                    # Add interview status to response if needed
                    if self.interview_state.interview_ended:
                        score_summary = f"\n\n🎯 **Interview Complete!**\n"
                        score_summary += f"Final Score: {self.interview_state.final_score_percentage:.1f}%\n"
                        score_summary += f"Questions Asked: {len(self.interview_state.questions_asked)}"
                        final_response += score_summary
                    
                    return final_response
                    
            except Exception as e:
                print(f"❌ Error in chat: {e}")
                return f"I apologize, but I encountered a technical issue. Error: {str(e)}"
        
        # Fallback if loop exits without completion
        return "I apologize, but the interview system encountered an issue. Please try again."

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def create_interview_interface():
    """Create and configure the Gradio interface"""
    
    interviewer = MockInterviewer()
    
    # Custom CSS for better appearance
    css = """
    .gradio-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .chat-message {
        padding: 10px;
        margin: 5px 0;
        border-radius: 10px;
    }
    """
    
    # Create interface
    interface = gr.ChatInterface(
        fn=interviewer.chat,
        type="messages",
        title="🎭 AI Mock Interviewer",
        description="""
        **Welcome to your AI Mock Interview!**
        
        📋 **Step 1:** Paste the job description you're applying for
        🎯 **Step 2:** Answer up to 10 tailored interview questions  
        📊 **Step 3:** Receive real-time evaluation and final score
        
        *The AI will analyze your profile against the job requirements and ask relevant questions covering technical skills, experience, and behavioral aspects.*
        """,
        examples=[
            "Software Engineer position requiring Python, React, and cloud technologies. We're looking for someone with 3+ years experience in full-stack development...",
            "Data Scientist role focusing on machine learning, statistical analysis, and Python/R programming. Experience with ML pipelines and cloud platforms preferred...",
            "Product Manager position requiring technical background, stakeholder management, and agile methodologies. 5+ years experience in tech products..."
        ],
        css=css,
        theme=gr.themes.Soft()
    )
    
    return interface

# ============================================================================
# SCRIPT EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("🚀 Starting Mock Interview Application...")
    print("📝 Make sure you have:")
    print("   - me/linkedin.pdf (your LinkedIn profile)")
    print("   - me/summary.txt (your professional summary)")
    print("   - OPENAI_API_KEY in .env")
    print("   - GOOGLE_API_KEY in .env")
    print("   - PUSHOVER_TOKEN and PUSHOVER_USER in .env (optional)")
    print("-" * 50)
    
    try:
        interface = create_interview_interface()
        interface.launch(
            share=False,  # Set to True for public sharing
            debug=True,   # Enable debug mode for development
            show_error=True
        )
    except Exception as e:
        print(f"❌ Failed to launch application: {e}")
        print("Please check your environment setup and try again.")
