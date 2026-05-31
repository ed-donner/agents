import os
import json
import asyncio
import concurrent.futures
import time
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

openai = OpenAI()
competitors = []
answers = []
together = ""
openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
groq_api_key = os.getenv('GROQ_API_KEY')

models_dict = {
    'openai': {
        'model': 'gpt-4o-mini',
        'api_key': openai_api_key,
        'base_url': None
    },
    'gemini': {
        'model': 'gemini-2.0-flash',
        'api_key': google_api_key,
        'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai/'
    },
    'groq': {
        'model': 'llama-3.3-70b-versatile',
        'api_key': groq_api_key,
        'base_url': 'https://api.groq.com/openai/v1'
    },
    'ollama': {
        'model': 'llama3.2',
        'api_key': 'ollama',
        'base_url': 'http://localhost:11434/v1'
    }
}

def key_checker():

    if openai_api_key:
        print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
    else:
        print("OpenAI API Key not set")
        
    if anthropic_api_key:
        print(f"Anthropic API Key exists and begins {anthropic_api_key[:7]}")
    else:
        print("Anthropic API Key not set (and this is optional)")

    if google_api_key:
        print(f"Google API Key exists and begins {google_api_key[:2]}")
    else:
        print("Google API Key not set (and this is optional)")

    if deepseek_api_key:
        print(f"DeepSeek API Key exists and begins {deepseek_api_key[:3]}")
    else:
        print("DeepSeek API Key not set (and this is optional)")

    if groq_api_key:
        print(f"Groq API Key exists and begins {groq_api_key[:4]}")
    else:
        print("Groq API Key not set (and this is optional)")

def question_prompt_generator():
    request = "Please come up with a challenging, nuanced question that I can ask a number of LLMs to evaluate their intelligence. "
    request += "Answer only with the question, no explanation."
    messages = [{"role": "user", "content": request}]
    return messages

def generate_competition_question():
    """
    Generate a challenging question for the LLM competition
    Returns the question text and formatted messages for LLM calls
    """
    print("Generating competition question...")
    question_prompt = question_prompt_generator()
    question = llm_caller(question_prompt)
    question_messages = [{"role": "user", "content": question}]
    print(f"Question: \n{question}")
    return question, question_messages

def llm_caller(messages):
    response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    )
    return response.choices[0].message.content

def llm_caller_with_model(messages, model_name, api_key, base_url):
    llm = None

    if base_url:
        try:
            llm = OpenAI(api_key=api_key, base_url=base_url)
        except Exception as e:
            print(f"Error creating OpenAI client: {e}")
            return None
    else:
        try:
            llm = OpenAI(api_key=api_key)
        except Exception as e:
            print(f"Error creating OpenAI client: {e}")
            return None

    response = llm.chat.completions.create(model=model_name, messages=messages)
    return response.choices[0].message.content

def get_single_model_answer(provider: str, details: Dict, question_messages: List[Dict]) -> Tuple[str, Optional[str]]:
    """
    Call a single model and return (provider, answer) or (provider, None) if failed.
    This function is designed to be used with ThreadPoolExecutor.
    """
    print(f"Calling model {provider}...")
    try:
        answer = llm_caller_with_model(question_messages, details['model'], details['api_key'], details['base_url'])
        print(f"Model {provider} was successfully called!")
        return provider, answer
    except Exception as e:
        print(f"Model {provider} failed to call: {e}")
        return provider, None

def get_models_answers(question_messages):
    """
    Sequential version - kept for backward compatibility
    """
    for provider, details in models_dict.items():
        print(f"Calling model {provider}...")
        try:
            answer = llm_caller_with_model(question_messages, details['model'], details['api_key'], details['base_url'])
            print(f"Model {provider} was successful called!")
        except Exception as e:
            print(f"Model {provider} failed to call: {e}")
            continue
        competitors.append(provider)
        answers.append(answer)

def get_models_answers_parallel(question_messages, max_workers: int = 4):
    """
    Parallel version - calls all models simultaneously using ThreadPoolExecutor
    """
    print("Starting parallel execution of all models...")
    
    # Clear previous results
    competitors.clear()
    answers.clear()
    
    # Use ThreadPoolExecutor for parallel execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_provider = {
            executor.submit(get_single_model_answer, provider, details, question_messages): provider 
            for provider, details in models_dict.items()
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_provider):
            provider, answer = future.result()
            if answer is not None:  # Only add successful calls
                competitors.append(provider)
                answers.append(answer)
    
    print(f"Parallel execution completed. {len(competitors)} models responded successfully.")

async def get_single_model_answer_async(provider: str, details: Dict, question_messages: List[Dict]) -> Tuple[str, Optional[str]]:
    """
    Async version of single model call - for even better performance
    """
    print(f"Calling model {provider} (async)...")
    try:
        # Run the synchronous call in a thread pool
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(
            None, 
            llm_caller_with_model, 
            question_messages, 
            details['model'], 
            details['api_key'], 
            details['base_url']
        )
        print(f"Model {provider} was successfully called!")
        return provider, answer
    except Exception as e:
        print(f"Model {provider} failed to call: {e}")
        return provider, None

async def get_models_answers_async(question_messages):
    """
    Async version - calls all models simultaneously using asyncio
    """
    print("Starting async execution of all models...")
    
    # Clear previous results
    competitors.clear()
    answers.clear()
    
    # Create tasks for all models
    tasks = [
        get_single_model_answer_async(provider, details, question_messages)
        for provider, details in models_dict.items()
    ]
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    for result in results:
        if isinstance(result, Exception):
            print(f"Task failed with exception: {result}")
            continue
        provider, answer = result
        if answer is not None:  # Only add successful calls
            competitors.append(provider)
            answers.append(answer)
    
    print(f"Async execution completed. {len(competitors)} models responded successfully.")

def together_maker(answers):
    together = ""
    for index, answer in enumerate(answers):
        together += f"# Response from competitor {index+1}\n\n"
        together += answer + "\n\n"    
    return together

def judge_prompt_generator(competitors, question, together):
    judge = f"""You are judging a competition between {len(competitors)} competitors.
    Each model has been given this question:

    {question}

    Your job is to evaluate each response for clarity and strength of argument, and rank them in order of best to worst.
    Respond with JSON, and only JSON, with the following format:
    {{"results": ["best competitor number", "second best competitor number", "third best competitor number", ...]}}

    Here are the responses from each competitor:

    {together}

    Now respond with the JSON with the ranked order of the competitors, nothing else. Do not include markdown formatting or code blocks."""
    return judge

def judge_caller(judge_prompt, competitors):
    print(f"Calling judge...")
    judge_messages = [{"role": "user", "content": judge_prompt}]
    results = llm_caller_with_model(judge_messages, "o3-mini", openai_api_key, None)
    results_dict = json.loads(results)
    ranks = results_dict["results"]
    for index, result in enumerate(ranks):
        competitor = competitors[int(result)-1]
        print(f"Rank {index+1}: {competitor}")
    return ranks

def compare_execution_methods(question_messages, runs_per_method=1):
    """
    Compare performance of different execution methods
    """
    methods = ['sequential', 'parallel', 'async']
    results = {}
    
    for method in methods:
        print(f"\n{'='*50}")
        print(f"Testing {method} execution method")
        print(f"{'='*50}")
        
        method_times = []
        
        for run in range(runs_per_method):
            print(f"\nRun {run + 1}/{runs_per_method}")
            
            # Clear previous results
            competitors.clear()
            answers.clear()
            
            start_time = time.time()
            
            if method == 'sequential':
                get_models_answers(question_messages)
            elif method == 'parallel':
                get_models_answers_parallel(question_messages, max_workers=4)
            elif method == 'async':
                asyncio.run(get_models_answers_async(question_messages))
            
            execution_time = time.time() - start_time
            method_times.append(execution_time)
            print(f"Run {run + 1} completed in {execution_time:.2f} seconds")
        
        avg_time = sum(method_times) / len(method_times)
        results[method] = {
            'times': method_times,
            'avg_time': avg_time,
            'successful_models': len(competitors)
        }
        
        print(f"\n{method.upper()} Results:")
        print(f"  Average time: {avg_time:.2f} seconds")
        print(f"  Successful models: {len(competitors)}")
        print(f"  All times: {[f'{t:.2f}s' for t in method_times]}")
    
    # Print comparison summary
    print(f"\n{'='*60}")
    print("PERFORMANCE COMPARISON SUMMARY")
    print(f"{'='*60}")
    
    for method, data in results.items():
        print(f"{method.upper():>12}: {data['avg_time']:>6.2f}s avg, {data['successful_models']} models")
    
    # Calculate speedup
    if 'sequential' in results:
        seq_time = results['sequential']['avg_time']
        print(f"\nSpeedup vs Sequential:")
        for method, data in results.items():
            if method != 'sequential':
                speedup = seq_time / data['avg_time']
                print(f"  {method.upper()}: {speedup:.2f}x faster")
    
    return results

def run_llm_competition(question_messages, execution_method, question):
    """
    Run the LLM competition with the specified execution method
    """
    print(f"\nUsing {execution_method} execution method...")
    start_time = time.time()

    if execution_method == 'sequential':
        get_models_answers(question_messages)
    elif execution_method == 'parallel':
        get_models_answers_parallel(question_messages, max_workers=4)
    elif execution_method == 'async':
        asyncio.run(get_models_answers_async(question_messages))
    else:
        raise ValueError(f"Unknown execution method: {execution_method}")

    execution_time = time.time() - start_time
    print(f"Execution completed in {execution_time:.2f} seconds")

    together = together_maker(answers)
    judge_prompt = judge_prompt_generator(competitors, question, together)
    judge_caller(judge_prompt, competitors)
    
    return execution_time

# Interactive execution method selection
def get_execution_method():
    """
    Prompt user to select execution method
    """
    print("\n" + "="*60)
    print("EXECUTION METHOD SELECTION")
    print("="*60)
    print("Choose how to execute the LLM calls:")
    print("1. Sequential - Call models one after another (original method)")
    print("2. Parallel   - Call all models simultaneously (recommended)")
    print("3. Async      - Use async/await for maximum performance")
    print("4. Compare    - Run all methods and compare performance")
    print("="*60)
    
    while True:
        try:
            choice = input("Enter your choice (1-4): ").strip()
            
            if choice == '1':
                return 'sequential'
            elif choice == '2':
                return 'parallel'
            elif choice == '3':
                return 'async'
            elif choice == '4':
                return 'compare'
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")
                continue
        except KeyboardInterrupt:
            print("\nExiting...")
            exit(0)
        except EOFError:
            print("\nExiting...")
            exit(0)

def main():
    key_checker()
    
    # Get user's execution method choice
    EXECUTION_METHOD = get_execution_method()
    # Generate the competition question and get the question messages
    question, question_messages = generate_competition_question()

    if EXECUTION_METHOD == 'compare':
        print("\nRunning performance comparison...")
        compare_execution_methods(question_messages, runs_per_method=1)
    else:
     run_llm_competition(question_messages, EXECUTION_METHOD, question)

main()