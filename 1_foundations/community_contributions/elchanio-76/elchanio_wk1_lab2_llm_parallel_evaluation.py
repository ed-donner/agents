import json
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Markdown not necessary if not running in a notebook
# from IPython.display import Markdown, display
import boto3
from anthropic import Anthropic
from botocore import client as botocore_client
from dotenv import load_dotenv
from openai import OpenAI
from collections import defaultdict

# This exercise builds upon the week 1 lab 2 of Agentic AI course.
# Implementing two patterns:
# Agent parallelization with ThreadPoolExecutor and combined LLM as a judge
# We are asking all of the models to evaluate the anonymized responses
# and average out the rankings.

# This can eat up a lot of tokens, so be careful running it multiple times.
# I didn't limit the number of tokens on purpose.

# Modify the setup_environment() and the models dictionary in main()
# to adjust to your taste/environment.


def setup_environment():
    """
    Set up the environment by initializing the Bedrock, Anthropic,
    and OpenAI clients.
    Returns:
        Dictionary with initialized clients
    """
    try:
        load_dotenv(override=True)
    except Exception as e:
        print(f"\U0000274C Warning: Could not load .env file: {e}")
    
    try:
        bedrock_api_key = os.environ["AWS_BEARER_TOKEN_BEDROCK"]
    except KeyError:
        bedrock_api_key = None
        print("\U0000274C Warning: AWS_BEARER_TOKEN_BEDROCK not found in environment")
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    google_api_key = os.getenv("GEMINI_API_KEY")
    xai_api_key = os.getenv("XAI_API_KEY")

    clients = {}

    if bedrock_api_key:
        try:
            print("Bedrock API key loaded successfully. Initializing runtime client")
            bedrock_client = boto3.client(
                service_name="bedrock-runtime", region_name="us-east-1"
            )
            clients.update({"bedrock": bedrock_client})
        except Exception as e:
            print(f"\U0000274C Error initializing Bedrock client: {e}")
    
    if anthropic_api_key:
        try:
            print("Anthropic API key loaded successfully. Initializing client")
            anthropic_client = Anthropic(api_key=anthropic_api_key)
            clients.update({"anthropic": anthropic_client})
        except Exception as e:
            print(f"\U0000274C Error initializing Anthropic client: {e}")
    
    if openai_api_key:
        try:
            print("OpenAI API key loaded successfully. Initializing client")
            openai_client = OpenAI(api_key=openai_api_key)
            clients.update({"openai": openai_client})
        except Exception as e:
            print(f"\U0000274C Error initializing OpenAI client: {e}")
    
    if google_api_key:
        try:
            print("Google API key loaded successfully. Initializing client")
            google_client = OpenAI(
                api_key=google_api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            )
            clients.update({"google": google_client})
        except Exception as e:
            print(f"\U0000274C Error initializing Google client: {e}")
    
    if xai_api_key:
        try:
            print("XAI API key loaded successfully. Initializing client")
            xai_client = OpenAI(
                api_key=xai_api_key, base_url="https://api.x.ai/v1"
            )
            clients.update({"xai": xai_client})
        except Exception as e:
            print(f"\U0000274C Error initializing XAI client: {e}")

    try:
        ollama_client = OpenAI(
            api_key="ollama", base_url="http://localhost:11434/v1"
        )
        clients.update({"ollama": ollama_client})
    except Exception as e:
        print(f"\U0000274C Error initializing Ollama client: {e}")

    return clients


def call_openai(client, prompt, model="gpt-5-nano", **kwargs):
    """
    Call the OpenAI API with the given prompt and model.
    """
    try:
        messages = [{"role": "user", "content": prompt}]
        response = client.chat.completions.create(
            model=model, messages=messages, **kwargs
        )
        text = response.choices[0].message.content

        return text
    except Exception as e:
        print(f"\U0000274C Error calling OpenAI API with model {model}: {e}")
        raise


def call_anthropic(client, prompt, model="claude-3-5-haiku-latest", **kwargs):
    """
    Call the Anthropic API with the given prompt and model.
    """
    try:
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            **kwargs,
        )
        return message.content[0].text
    except Exception as e:
        print(f"\U0000274C Error calling Anthropic API with model {model}: {e}")
        raise


def call_bedrock(client, prompt, model="us.amazon.nova-micro-v1:0", **kwargs):
    try:
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        response = client.converse(modelId=model, messages=messages, **kwargs)
        return response["output"]["message"]["content"][0]["text"]
    except Exception as e:
        print(f"\U0000274C Error calling Bedrock API with model {model}: {e}")
        raise


def call_single_model(provider, model, client, prompt):
    """Call a single model and return the response."""
    try:
        if isinstance(client, OpenAI):
            print(
                f"""-> \U0001f9e0 Asking {model} on {provider}\
                using OpenAI API... \U0001f9e0"""
            )
            response = call_openai(client, prompt, model=model)
        elif isinstance(client, Anthropic):
            print(
                f"""-> \U0001f9e0 Asking {model} on {provider}\
                using Anthropic API... \U0001f9e0"""
            )
            response = call_anthropic(client, prompt, model=model)
        elif isinstance(client, botocore_client.BaseClient):
            print(
                f"""-> \U0001f9e0 Asking {model} on {provider}\
                using Bedrock API... \U0001f9e0"""
            )
            response = call_bedrock(client, prompt, model=model)
        else:
            raise ValueError(f"\U0000274C Unknown client type for model {model}")
        return model, response
    except Exception as e:
        print(f"\U0000274C Error calling model {model} on {provider}: {e}")
        return model, f"Error: {str(e)}"


def call_models(clients, prompt, models):
    """
    Call the models in parallel and return the responses.
    """
    responses = {}

    try:
        with ThreadPoolExecutor(max_workers=len(models)) as executor:
            futures = []
            for provider, model in models.items():
                if provider in clients:
                    client = clients[provider]
                    future = executor.submit(
                        call_single_model, provider, model, client, prompt
                    )
                    futures.append(future)
                else:
                    print(f"Warning: No client found for provider {provider}")
                    responses[model] = f"Error: No client available for {provider}"

            for future in as_completed(futures):
                try:
                    model, response = future.result()
                    responses[model] = response
                    print(f"\U00002705 {model} completed responding! \U00002705")
                except Exception as e:
                    print(f"\U0000274C Error processing future result: {e}")

    except Exception as e:
        print(f"\U0000274C Error in parallel model execution: {e}")
        raise

    return responses


def extract_json_response(text):
    # Find JSON that starts with {"results"
    pattern = r'(\{"results".*?\})'
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Try to find the complete JSON object
            return extract_complete_json(text)
    
    return None

def extract_complete_json(text):
    # More sophisticated approach to handle nested objects
    start_idx = text.find('{"response"')
    if start_idx == -1:
        return None
    
    bracket_count = 0
    for i, char in enumerate(text[start_idx:], start_idx):
        if char == '{':
            bracket_count += 1
        elif char == '}':
            bracket_count -= 1
            if bracket_count == 0:
                json_str = text[start_idx:i+1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue
    return None


def main():
    """Main function"""
    print("Demonstrate paralellization pattern of calling multiple LLM's")
    print("=" * 50)

    # Set up the environment
    print("Setting up the environment...")
    try:
        clients = setup_environment()
        if not clients:
            print("Error: No clients were successfully initialized")
            return
        print(f"Initialized {len(clients)} clients:")
        print(clients)
        print("\n" + "=" * 50)
    except Exception as e:
        print(f"Error during client initialization: {e}")
        import traceback
        traceback.print_exc()
        return

    # Flow:
    # 1. Ask a model to define a question.
    # 2. Ask the 6 models in parallel to answer the question
    # 3. Aggregate answers
    # 4. Ask each judging model to evaluate the answers
    # 5. Calculate average rank from model evaluations
    # 6. Print results

    # 1. Ask a model to define a question.
    print("STEP 1: Asking a model to define a question...")
    request = """Please come up with a challenging, nuanced question that\
    I can ask a number of LLMs to evaluate their intelligence. """
    request += (
        "Answer only with the question, without any explanation or preamble."
    )

    print("Request: " + request)
    question_model = "gpt-oss:20b"
    print("\U0001f9e0 Asking model: " + question_model + " \U0001f9e0")
    
    try:
        if "ollama" not in clients:
            print("\U0000274C Error: Ollama client not available")
            return
        question = call_openai(clients["ollama"], request, model=question_model)
        print("-" * 50)
        print("Question: " + question)
        print("-" * 50)
    except Exception as e:
        print(f"\U0000274C Error generating question: {e}")
        return

    # 2. Ask the 6 models in parallel to answer the question.
    # Define the model names in a dictionary
    print("=" * 50 + "\nSTEP 2: Ask the models..")
    models = {
        # "bedrock":"us.amazon.nova-lite-v1:0",
        "bedrock": "us.meta.llama3-3-70b-instruct-v1:0",
        "anthropic": "claude-3-7-sonnet-latest",
        "openai": "gpt-5-mini",
        "google": "gemini-2.5-flash",
        "xai": "grok-3-mini",
        "ollama": "gpt-oss:20b",
    }
    try:
        answers = call_models(clients, question, models)
        if not answers:
            print("\U0000274C Error: No answers received from models")
            return
    except Exception as e:
        print(f"\U0000274C Error getting model answers: {e}")
        return

    # 3. Aggregate answers
    print("STEP 3: Aggregating answers...")

    try:
        answers_list = [answer for answer in answers.values()]
        competitors = [model for model in answers.keys()]
        print("... And the competitors are:")
        for i in enumerate(competitors):
            print(f"Competitor C{i[0]+1}: {i[1]}")

        together = ""
        for index, answer in enumerate(answers_list):
            together += f"# Response from competitor 'C{index+1}'\n\n"
            together += answer + "\n\n" + "-" * 50 + "\n\n"
    except Exception as e:
        print(f"\U0000274C Error aggregating answers: {e}")
        return

    # 4. Ask each model to evaluate the answers
    print("=" * 50 + "\nSTEP 4: Evaluating answers...")
    # Create evaluation prompt
    judge = f"""
        You are  an expert evaluator of LLMS in a competition.\
        You are judging a competition between {len(competitors)} competitors.\
        Competitors are identified by an id such as 'C1', 'C2', etc.\
        Each competitor has been given this question:

        {question}

        Your job is to evaluate each response for clarity and strength of argument,\
        and rank them in order of best to worst. Think about your evaluation.

        Respond with JSON with the following format:
        {{"results": ["best competitor id", "second best competitor id", "third best competitor id", ...]}}

        Here are the responses from each competitor:

        {together}

        Now respond with the JSON, and only JSON, with the ranked\
        order of the competitors, nothing else.\
        Do not include markdown formatting or code blocks."""
    # Write evaluation prompt to file
    try:
        print("Writing evaluation prompt to file 'evaluation_prompt.txt'")
        with open("evaluation_prompt.txt", "w") as f:
            f.write(together)
    except Exception as e:
        print(f"\U0000274C Error writing evaluation prompt to file: {e}")

    judging_models = {
        "bedrock": "us.amazon.nova-pro-v1:0",
        "anthropic": "claude-sonnet-4-20250514",
        "openai": "o3-mini",
        "google": "gemini-2.5-pro",
    }
    try:
        print(f"\U00002696"*5+" JUDGEMENT TIME! " + f"\U00002696"*5)
        evaluations = call_models(clients, judge, judging_models)
        if not evaluations:
            print("\U0000274C Error: No evaluations received from judging models")
            return
    except Exception as e:
        print(f"\U0000274C Error getting model evaluations: {e}")
        return

    # 5. Calculate average rank from model evaluations
    print("=" * 42 + "\nSTEP 5: Calculating average rank from model evaluations...")
    rankings = []
    for model, evaluation in evaluations.items():
        try:
            parsed = extract_json_response(evaluation)
            rankings.append(parsed["results"])
        except json.JSONDecodeError as e:
            print(
                f"\U0000274C Error parsing JSON response for model {model}: {e}\nResponse: {evaluation}"
            )
            rankings.append([])
        except Exception as e:
            print(f"\U0000274C Unexpected error processing evaluation for model {model}: {e}")
            rankings.append([])

    print(rankings)

    try:
        # Collect all rankings for each contestant
        contestant_rankings = defaultdict(list)
        for judge_ranking in rankings:
            for position, contestant in enumerate(judge_ranking, 1):
                contestant_rankings[contestant].append(position)

        # Calculate average rankings
        average_rankings = {contestant: sum(ranks)/len(ranks) 
                        for contestant, ranks in contestant_rankings.items() if ranks}

        #print(average_rankings)
        
        if not average_rankings:
            print("\U0000274C Error: No valid rankings to process")
            return
            
        # Sort by average (ascending - lowest average = best rank)
        sorted_results = sorted(average_rankings.items(), key=lambda x: x[1])
        #print(sorted_results)

        # 6. present the results by competitor
        print("Final Rankings:\n"+"="*42)
        for competitor, average in sorted_results:
            try:
                competitor_name = competitors[int(competitor.lower().strip('c'))-1]
                rank = sorted_results.index((competitor, average))+1
                print(f"\U0001F3C6 Rank: {rank} ---- Model: {competitor_name} ---- Average rank: {average} \U0001F3C6")
            except (ValueError, IndexError) as e:
                print(f"\U0000274C Error processing competitor {competitor}: {e}")

        print("=" * 42)
        print("Done!")
    except Exception as e:
        print(f"\U0000274C Error calculating final rankings: {e}")


if __name__ == "__main__":
    main()
