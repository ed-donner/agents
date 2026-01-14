#!/usr/bin/env python3
"""
Lab2 Multi-Model Comparison Script
=================================

This script implements the complete Lab2 workflow from the 1_foundations/2_lab2.ipynb notebook.
It demonstrates the Multi-Model Comparison pattern by:

1. Generating a challenging question using one model
2. Testing multiple AI models with that question  
3. Using a judge model to rank the responses
4. Displaying results in a clear format

The script gracefully handles missing API keys and unavailable services.
"""

import os
import json
import traceback
from dotenv import load_dotenv

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_subsection(title):
    """Print a formatted subsection header"""
    print(f"\n--- {title} ---")

def check_api_keys():
    """Check which API keys are available"""
    print_section("CHECKING API KEYS")
    
    keys_info = {}
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key and openai_key != 'your_openai_api_key_here':
        print(f"✓ OpenAI API Key exists and begins {openai_key[:8]}...")
        keys_info['openai'] = True
    else:
        print("✗ OpenAI API Key not set or using placeholder")
        keys_info['openai'] = False
    
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if anthropic_key and anthropic_key != 'your_anthropic_api_key_here':
        print(f"✓ Anthropic API Key exists and begins {anthropic_key[:7]}...")
        keys_info['anthropic'] = True
    else:
        print("✗ Anthropic API Key not set (optional)")
        keys_info['anthropic'] = False
    
    google_key = os.getenv('GOOGLE_API_KEY')
    if google_key and google_key != 'your_google_api_key_here':
        print(f"✓ Google API Key exists and begins {google_key[:2]}...")
        keys_info['google'] = True
    else:
        print("✗ Google API Key not set (optional)")
        keys_info['google'] = False
    
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    if deepseek_key and deepseek_key != 'your_deepseek_api_key_here':
        print(f"✓ DeepSeek API Key exists and begins {deepseek_key[:3]}...")
        keys_info['deepseek'] = True
    else:
        print("✗ DeepSeek API Key not set (optional)")
        keys_info['deepseek'] = False
    
    groq_key = os.getenv('GROQ_API_KEY')
    if groq_key and groq_key != 'your_groq_api_key_here':
        print(f"✓ Groq API Key exists and begins {groq_key[:4]}...")
        keys_info['groq'] = True
    else:
        print("✗ Groq API Key not set (optional)")
        keys_info['groq'] = False
    
    return keys_info

def generate_question(keys_info):
    """Generate a challenging question using OpenAI"""
    print_section("GENERATING CHALLENGING QUESTION")
    
    if not keys_info['openai']:
        print("⚠️  OpenAI API key required for question generation. Using fallback question.")
        return "Imagine you are tasked with explaining the concept of emergence to someone who has never encountered it before. How would you illustrate this concept using three different examples from completely different domains (biological, social, and technological), and what underlying principles connect these seemingly disparate phenomena?"
    
    try:
        from openai import OpenAI
        
        openai_client = OpenAI()
        
        request = "Please come up with a challenging, nuanced question that I can ask a number of LLMs to evaluate their intelligence. "
        request += "Answer only with the question, no explanation."
        messages = [{"role": "user", "content": request}]
        
        print("🤖 Asking GPT-4o-mini to generate a challenging question...")
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        question = response.choices[0].message.content
        
        print(f"✓ Generated question: {question}")
        return question
        
    except Exception as e:
        print(f"✗ Error generating question: {str(e)}")
        fallback = "Imagine you are tasked with explaining the concept of emergence to someone who has never encountered it before. How would you illustrate this concept using three different examples from completely different domains (biological, social, and technological), and what underlying principles connect these seemingly disparate phenomena?"
        print(f"📋 Using fallback question: {fallback}")
        return fallback

def test_openai_model(question, keys_info):
    """Test OpenAI GPT-4o-mini"""
    if not keys_info['openai']:
        return None, "OpenAI API key not available"
    
    try:
        from openai import OpenAI
        
        openai_client = OpenAI()
        messages = [{"role": "user", "content": question}]
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=messages
        )
        answer = response.choices[0].message.content
        return answer, None
        
    except Exception as e:
        return None, f"OpenAI error: {str(e)}"

def test_anthropic_model(question, keys_info):
    """Test Anthropic Claude"""
    if not keys_info['anthropic']:
        return None, "Anthropic API key not available"
    
    try:
        from anthropic import Anthropic
        
        claude = Anthropic()
        messages = [{"role": "user", "content": question}]
        
        response = claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=messages, 
            max_tokens=1000
        )
        answer = response.content[0].text
        return answer, None
        
    except Exception as e:
        return None, f"Anthropic error: {str(e)}"

def test_google_model(question, keys_info):
    """Test Google Gemini"""
    if not keys_info['google']:
        return None, "Google API key not available"
    
    try:
        from openai import OpenAI
        
        google_key = os.getenv('GOOGLE_API_KEY')
        gemini = OpenAI(api_key=google_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
        messages = [{"role": "user", "content": question}]
        
        response = gemini.chat.completions.create(
            model="gemini-2.0-flash", 
            messages=messages
        )
        answer = response.choices[0].message.content
        return answer, None
        
    except Exception as e:
        return None, f"Google Gemini error: {str(e)}"

def test_deepseek_model(question, keys_info):
    """Test DeepSeek"""
    if not keys_info['deepseek']:
        return None, "DeepSeek API key not available"
    
    try:
        from openai import OpenAI
        
        deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        deepseek = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com/v1")
        messages = [{"role": "user", "content": question}]
        
        response = deepseek.chat.completions.create(
            model="deepseek-chat", 
            messages=messages
        )
        answer = response.choices[0].message.content
        return answer, None
        
    except Exception as e:
        return None, f"DeepSeek error: {str(e)}"

def test_groq_model(question, keys_info):
    """Test Groq Llama"""
    if not keys_info['groq']:
        return None, "Groq API key not available"
    
    try:
        from openai import OpenAI
        
        groq_key = os.getenv('GROQ_API_KEY')
        groq = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
        messages = [{"role": "user", "content": question}]
        
        response = groq.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=messages
        )
        answer = response.choices[0].message.content
        return answer, None
        
    except Exception as e:
        return None, f"Groq error: {str(e)}"

def test_ollama_model(question):
    """Test local Ollama model"""
    try:
        from openai import OpenAI
        
        ollama = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
        messages = [{"role": "user", "content": question}]
        
        response = ollama.chat.completions.create(
            model="llama3.2", 
            messages=messages
        )
        answer = response.choices[0].message.content
        return answer, None
        
    except Exception as e:
        return None, f"Ollama error: {str(e)} (Is Ollama running with llama3.2 model?)"

def test_all_models(question, keys_info):
    """Test all available models with the question"""
    print_section("TESTING MODELS")
    
    models = [
        ("GPT-4o-mini", lambda: test_openai_model(question, keys_info)),
        ("Claude-3.5-Sonnet", lambda: test_anthropic_model(question, keys_info)),
        ("Gemini-2.0-Flash", lambda: test_google_model(question, keys_info)),
        ("DeepSeek-Chat", lambda: test_deepseek_model(question, keys_info)),
        ("Llama-3.3-70b (Groq)", lambda: test_groq_model(question, keys_info)),
        ("Llama-3.2 (Ollama)", lambda: test_ollama_model(question)),
    ]
    
    competitors = []
    answers = []
    
    for model_name, test_func in models:
        print_subsection(f"Testing {model_name}")
        
        try:
            answer, error = test_func()
            
            if answer:
                print(f"✓ {model_name} responded successfully")
                print(f"📝 Response preview: {answer[:100]}...")
                competitors.append(model_name)
                answers.append(answer)
            else:
                print(f"✗ {model_name} failed: {error}")
                
        except Exception as e:
            print(f"✗ {model_name} error: {str(e)}")
    
    return competitors, answers

def judge_responses(question, competitors, answers, keys_info):
    """Use a model to judge and rank the responses"""
    print_section("JUDGING RESPONSES")
    
    if len(competitors) < 2:
        print("⚠️  Need at least 2 model responses to judge. Skipping judgment.")
        return None
    
    if not keys_info['openai']:
        print("⚠️  OpenAI API key required for judging. Skipping judgment.")
        return None
    
    # Prepare the responses for judging
    together = ""
    for index, answer in enumerate(answers):
        together += f"# Response from competitor {index+1}\n\n"
        together += answer + "\n\n"
    
    judge_prompt = f"""You are judging a competition between {len(competitors)} competitors.
Each model has been given this question:

{question}

Your job is to evaluate each response for clarity and strength of argument, and rank them in order of best to worst.
Respond with JSON, and only JSON, with the following format:
{{"results": ["best competitor number", "second best competitor number", "third best competitor number", ...]}}

Here are the responses from each competitor:

{together}

Now respond with the JSON with the ranked order of the competitors, nothing else. Do not include markdown formatting or code blocks."""
    
    try:
        from openai import OpenAI
        
        openai_client = OpenAI()
        judge_messages = [{"role": "user", "content": judge_prompt}]
        
        print("⚖️  Asking o3-mini to judge the responses...")
        
        response = openai_client.chat.completions.create(
            model="o3-mini",
            messages=judge_messages,
        )
        results = response.choices[0].message.content
        
        print(f"📊 Raw judgment result: {results}")
        
        # Parse the JSON response
        results_dict = json.loads(results)
        ranks = results_dict["results"]
        
        print_subsection("FINAL RANKINGS")
        for index, result in enumerate(ranks):
            competitor = competitors[int(result)-1]
            print(f"🏆 Rank {index+1}: {competitor}")
        
        return ranks
        
    except Exception as e:
        print(f"✗ Error during judging: {str(e)}")
        return None

def display_full_results(question, competitors, answers, rankings):
    """Display the complete results in a formatted way"""
    print_section("COMPLETE RESULTS SUMMARY")
    
    print_subsection("Question Asked")
    print(f"❓ {question}")
    
    print_subsection("Model Responses")
    for i, (competitor, answer) in enumerate(zip(competitors, answers)):
        print(f"\n🤖 {competitor}:")
        print("-" * 40)
        print(answer)
        print("-" * 40)
    
    if rankings:
        print_subsection("Final Rankings")
        for index, result in enumerate(rankings):
            competitor = competitors[int(result)-1]
            print(f"🏆 Rank {index+1}: {competitor}")
    
    print_subsection("Pattern Analysis")
    print("🔍 This lab demonstrates the Multi-Model Comparison pattern:")
    print("   • Multiple models process the same task")
    print("   • Responses are collected and compared")
    print("   • A judge model evaluates and ranks results")
    print("   • This pattern improves quality through competition")

def main():
    """Main function to run the complete Lab2 workflow"""
    print_section("LAB2: MULTI-MODEL COMPARISON")
    print("This script implements the complete Lab2 workflow from 1_foundations/2_lab2.ipynb")
    print("Demonstrating the Multi-Model Comparison pattern with multiple AI providers")
    
    # Load environment variables
    load_dotenv(override=True)
    
    # Check available API keys
    keys_info = check_api_keys()
    
    # Generate the challenging question
    question = generate_question(keys_info)
    
    # Test all available models
    competitors, answers = test_all_models(question, keys_info)
    
    if not competitors:
        print("\n❌ No models were able to respond. Please check your API keys and try again.")
        print("\n💡 To get started:")
        print("   1. Edit the .env file with your actual API keys")
        print("   2. Or install and run Ollama with: ollama serve && ollama pull llama3.2")
        return
    
    # Judge the responses if we have multiple
    rankings = judge_responses(question, competitors, answers, keys_info)
    
    # Display complete results
    display_full_results(question, competitors, answers, rankings)
    
    print_section("LAB2 COMPLETED SUCCESSFULLY!")
    print(f"✅ Tested {len(competitors)} models")
    print("✅ Demonstrated Multi-Model Comparison pattern")
    if rankings:
        print("✅ Generated ranked results")
    print("\n🎯 Try editing the .env file with real API keys for more models!")

if __name__ == "__main__":
    main()