"""Graph node functions - the core logic of the interview prep agent"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from src.models import State
from src.llm import llm, planner_llm
from src.external_services import search_company_info, search_youtube
from src.config import MAX_REFINEMENTS


def planner(state: State) -> State:
    """
    Handles conversation and gathers company/role information
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with planner response and extracted info
    """
    current_stage = state.get("stage", "gather_info")
    
    # Don't run during processing stages
    if current_stage in ["research", "generate", "format"]:
        return state
    
    system_prompt = f"""
You are an interview prep assistant.

CURRENT STATE:
- Stage: {current_stage}
- Company: {state.get("company_name", "Not provided")}
- Role: {state.get("role_title", "Not provided")}

YOUR JOB:
If stage is "gather_info":
  1. If no company_name → ask "What company are you interviewing with?"
  2. If have company but no role_title → ask "What role are you applying for?"
  3. If have both → set stage="research" and tell them you'll research the company

EXTRACTION RULES:
- Extract company_name from responses like: "Google", "I'm interviewing at Google", "The company is Google"
- Extract role_title from responses like: "Software Engineer", "I'm applying for Software Engineer role"
- For greetings like "hi" or "hello", do NOT extract anything, just ask for the company name
- Do NOT guess or assume information from greetings

Be friendly and concise!
"""
    
    messages = [
        SystemMessage(content=system_prompt),
        *state.get("messages", [])
    ]
    
    result = planner_llm.invoke(messages)
    
    # Build update dict
    update = {
        "messages": [AIMessage(content=result.response)],
        "stage": result.stage if result.stage else current_stage
    }
    
    # Add any extracted info
    if result.company_name:
        update["company_name"] = result.company_name
    if result.role_title:
        update["role_title"] = result.role_title
    
    return update


def research(state: State) -> State:
    """
    Research the company using Tavily AI-powered web search
    
    Args:
        state: Current graph state with company_name and role_title
        
    Returns:
        Updated state with company_info summary
    """
    company = state["company_name"]
    role = state["role_title"]
    
    # Search for company information using Tavily
    search_results = search_company_info(company, role)
    company_data = search_results.get("content", "")
    sources = search_results.get("sources", [])
    
    # Fallback to LLM knowledge if search fails
    if not company_data:
        prompt = f"""
Based on your knowledge, provide a brief summary of {company} for interview preparation.
Focus on: mission, products/services, culture, and what makes them unique.
Keep it to 3-4 sentences.
"""
        result = llm.invoke([HumanMessage(content=prompt)])
        return {
            "company_info": result.content,
            "stage": "generate"
        }
    
    # Ask LLM to summarize the search results for interview prep
    prompt = f"""
Summarize this company for interview prep (3-4 sentences):

Company: {company}
Role: {role}

Information found:
{company_data}

Focus on: mission, products, culture, and what makes them unique.
Be concise and relevant for a {role} interview.
"""
    
    result = llm.invoke([HumanMessage(content=prompt)])
    
    return {
        "company_info": result.content,
        "stage": "generate"
    }


def generate_guide(state: State) -> State:
    """
    Generate comprehensive interview prep guide
    
    Args:
        state: Current graph state with company info
        
    Returns:
        Updated state with generated prep guide
    """
    prompt = f"""
Create an interview prep guide for:

Company: {state['company_name']}
Role: {state['role_title']}
Company Info: {state['company_info']}

Include:
1. Company overview (2-3 sentences)
2. 10 likely interview questions (mix behavioral and technical for the role)
3. Brief answer tips for each question type
4. 3 insightful questions they should ask the interviewer

Format with markdown headers (##). Be concise and practical.
"""
    
    result = llm.invoke([HumanMessage(content=prompt)])
    
    # Format the guide cleanly
    guide = f"""# 🎯 Interview Prep Guide

## Company: {state['company_name']}
## Role: {state['role_title']}

{result.content}"""
    
    return {
        "prep_guide": guide,
        "stage": "ask_refinement",
        "refinement_count": 0
    }


def ask_refinement(state: State) -> State:
    """
    Show guide and ask if user wants refinements
    
    Args:
        state: Current graph state with prep guide
        
    Returns:
        Updated state with refinement prompt or completion
    """
    # Check if hit max refinements
    if state.get("refinement_count", 0) >= MAX_REFINEMENTS:
        final = f"""{state['prep_guide']}

---
✅ Max refinements reached. Good luck with your interview! 🚀"""
        return {
            "messages": [AIMessage(content=final)],
            "stage": "completed"
        }
    
    # Show guide with refinement options
    msg = f"""{state['prep_guide']}

---

**Want to refine this?**
- Add more questions
- Find YouTube videos  
- Adjust details

Say **"looks good"** when ready!"""
    
    return {
        "messages": [AIMessage(content=msg)],
        "stage": "await_refinement"
    }


def handle_refinement(state: State) -> State:
    """
    Process user's refinement request
    
    Args:
        state: Current graph state with user's refinement message
        
    Returns:
        Updated state based on refinement type (YouTube, done, or update)
    """
    last_message = state["messages"][-1].content.lower()
    
    # Check if user wants YouTube videos
    if any(word in last_message for word in ["youtube", "video", "videos", "watch", "visual"]):
        return {
            "stage": "youtube_search"
        }
    
    # Check if user is done
    if any(word in last_message for word in ["looks good", "perfect", "done", "good", "finish", "fine", "great", "ready"]):
        final_msg = """---
✅ **You're all set! Good luck with your interview!** 🚀

Click 🔄 Reset to prep for another interview."""
        return {
            "messages": [AIMessage(content=final_msg)],
            "stage": "completed"
        }
    
    # User wants changes - update the guide
    prompt = f"""
The user wants to refine their interview prep guide.

Current guide:
{state['prep_guide']}

User's request: {last_message}

Update the guide based on their request. Keep the same markdown format.
Only change what they asked for, keep everything else the same.
Be precise and helpful.
"""
    
    result = llm.invoke([HumanMessage(content=prompt)])
    
    # Format the updated guide
    updated_guide = f"""# 🎯 Interview Prep Guide

## Company: {state['company_name']}
## Role: {state['role_title']}

{result.content}"""
    
    return {
        "messages": [AIMessage(content="✅ Updated!")],
        "prep_guide": updated_guide,
        "refinement_count": state.get("refinement_count", 0) + 1,
        "stage": "ask_refinement"
    }


def youtube_search_node(state: State) -> State:
    """
    Search YouTube for relevant interview prep videos
    
    Args:
        state: Current graph state with company and role
        
    Returns:
        Updated state with YouTube video links
    """
    company = state["company_name"]
    role = state["role_title"]
    
    videos = search_youtube(company, role)
    
    if not videos:
        video_msg = "❌ Sorry, I couldn't find YouTube videos at the moment. Try again or continue with other refinements!"
    else:
        video_msg = f"📺 **Here are helpful YouTube videos for {company} {role} interviews:**\n\n"
        for i, video in enumerate(videos, 1):
            video_msg += f"**{i}. [{video['title']}]({video['url']})**\n"
            video_msg += f"   Channel: {video['channel']}\n\n"
        
        video_msg += "---\n\nAnything else you'd like to know or refine?"
    
    return {
        "messages": [AIMessage(content=video_msg)],
        "stage": "await_refinement"
    }

