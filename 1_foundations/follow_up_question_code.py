# Follow-up question code for Agentic AI differentiation
# This code takes the business idea from OpenAI and asks about challenges where Agentic AI could differentiate

from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Initialize OpenAI client
openai = OpenAI()

# First, get the business idea (this would be your existing code)
messages = [{"role": "user", "content": "Give me an idea for a side-hustle business worth exploring for an Agentic AI opportunity"}]

response = openai.chat.completions.create(
    model="gpt-4.1-mini",
    messages=messages
)

business_idea = response.choices[0].message.content
print("Business Idea:")
print(business_idea)
print("\n" + "="*50 + "\n")

# METHOD 1: Using f-strings (much better than string concatenation)
follow_up_question = f"""Based on this business idea: {business_idea}

What are some opportunities or pain points in this industry where Agentic AI can serve as a differentiator? 
Please identify specific challenges and explain how Agentic AI could provide unique advantages."""

messages = [{"role": "user", "content": follow_up_question}]

response = openai.chat.completions.create(
    model="gpt-4.1-mini",
    messages=messages
)

challenge_analysis = response.choices[0].message.content
print("Challenge Analysis (Method 1 - f-string):")
print(challenge_analysis)
print("\n" + "="*50 + "\n")

# METHOD 2: Using a function to structure the prompt (even better)
def create_follow_up_prompt(business_idea, question_type="opportunities"):
    """
    Create a structured follow-up prompt based on the business idea.
    
    Args:
        business_idea (str): The business idea from the first API call
        question_type (str): Type of question to ask (opportunities, challenges, etc.)
    """
    return f"""Based on this business idea: {business_idea}

What are some {question_type} in this industry where Agentic AI can serve as a differentiator? 
Please identify specific challenges and explain how Agentic AI could provide unique advantages."""

# Use the function
follow_up_question_2 = create_follow_up_prompt(business_idea, "opportunities and pain points")
messages = [{"role": "user", "content": follow_up_question_2}]

response = openai.chat.completions.create(
    model="gpt-4.1-mini",
    messages=messages
)

challenge_analysis_2 = response.choices[0].message.content
print("Challenge Analysis (Method 2 - function):")
print(challenge_analysis_2)
print("\n" + "="*50 + "\n")

# METHOD 3: Using a template system (most professional)
class PromptTemplate:
    def __init__(self, template):
        self.template = template
    
    def format(self, **kwargs):
        return self.template.format(**kwargs)

# Define the template
follow_up_template = PromptTemplate("""Based on this business idea: {business_idea}

What are some {focus_area} in this industry where Agentic AI can serve as a differentiator? 
Please identify specific challenges and explain how Agentic AI could provide unique advantages.""")

# Use the template
follow_up_question_3 = follow_up_template.format(
    business_idea=business_idea,
    focus_area="opportunities and pain points"
)

messages = [{"role": "user", "content": follow_up_question_3}]

response = openai.chat.completions.create(
    model="gpt-4.1-mini",
    messages=messages
)

challenge_analysis_3 = response.choices[0].message.content
print("Challenge Analysis (Method 3 - template system):")
print(challenge_analysis_3) 