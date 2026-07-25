# ----------------------------------------------------
# This script is using the idea of 2-lab-2, where we
# used multiple models to ask the same question to 
# multiple models, and then rank the answers.  However,
# in this case, we want to read a resume from the file
# resume-text.txt, then ask each model to revise the 
# resume.  Then, just like the lab, we ask AI to rank
# the models in the end.
# ----------------------------------------------------
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
from IPython.display import Markdown, display


# ----------------------------------------------------
# Write results to output file
# ----------------------------------------------------
def write_results(results, ):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, 'resume-results-rankings.txt')
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(results)
# ----------------------------------------------------

# ----------------------------------------------------
# read the file - this is the initial resume to re-write
# ----------------------------------------------------
def read_file():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    resume_path = os.path.join(script_dir, 'resume-text.txt')
    with open(resume_path, "r", encoding="utf-8") as f:
        return f.read()
# ----------------------------------------------------

load_dotenv(override=True)

# ----------------------------------------------------
# Get the API keys that we need
# ----------------------------------------------------
openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
google_api_key = os.getenv('GEMINI_API_KEY')
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
groq_api_key = os.getenv('GROQ_API_KEY')
# ----------------------------------------------------


# ----------------------------------------------------
# Set up the initial prompt and call gpt-5-mini
# ----------------------------------------------------
if os.path.exists("resume-results-rankings.txt"):
    os.remove("resume-results-rankings.txt")
    
competitors = []
answers = []

request = "Please re-write the resume so that it is professional and will likely pass any automated AI filters to filter it out for the position.  I need it to be in a format that I can easily copy and paste it into Word."
request += f'{read_file()}'

messages = [{"role": "user", "content": request}]
model_name = "gpt-5-nano"
write_results(f'\n\n#### Answer from {model_name} ####\n\n')

openai = OpenAI()

response = openai.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content

write_results(answer)
print('Answer written to file')

competitors.append(model_name)
answers.append(answer)
# ----------------------------------------------------

# ----------------------------------------------------
# Call claude-sonnet-4-5 using Anthropic to answer the question
# ----------------------------------------------------
model_name = "claude-sonnet-4-5"
write_results(f'\n\n#### Answer from {model_name} ####\n\n')

claude = Anthropic()
response = claude.messages.create(model=model_name, messages=messages, max_tokens=1000)
answer = response.content[0].text

write_results(answer)
print('Answer written to file')

competitors.append(model_name)
answers.append(answer)
# ----------------------------------------------------


# ----------------------------------------------------
# Call gemini-2.5-flash to answer the question
# ----------------------------------------------------
gemini = OpenAI(api_key=google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")

model_name = "gemini-2.5-flash"
write_results(f'\n\n#### Answer from {model_name} ####\n\n')

response = gemini.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content

write_results(answer)
print('Answer written to file')

competitors.append(model_name)
answers.append(answer)
# ----------------------------------------------------


# ----------------------------------------------------
# Call deepseek-chat to answer the question
# ----------------------------------------------------
deepseek = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1")

model_name = "deepseek-chat"

write_results(f'\n\n#### Answer from {model_name} ####\n\n')
response = deepseek.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content

write_results(answer)
print('Answer written to file')

competitors.append(model_name)
answers.append(answer)
# ----------------------------------------------------

# ----------------------------------------------------
# Call deepseek-chat to answer the question
# ----------------------------------------------------
groq_api_key = os.getenv('GROQ_API_KEY')
groq = OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")

model_name = "openai/gpt-oss-120b"
write_results(f'\n\n####vAnswer from Groq using {model_name} ####\n\n')

response = groq.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content

write_results(answer)
print('Answer written to file')

competitors.append(model_name)
answers.append(answer)
# ----------------------------------------------------



# ----------------------------------------------------
# Put the answers together and let AI decide which one
# is best
# ----------------------------------------------------
together = ""
for index, answer in enumerate(answers):
    together += f"# Response from competitor {index+1}\n\n"
    together += answer + "\n\n"
    
judge = f"""You are judging a competition between {len(competitors)} competitors.
Each model has been given this question:

{request}

Your job is to evaluate each response for clarity and strength of argument, and rank them in order of best to worst.
Respond with JSON, and only JSON, with the following format:
{{"results": ["best competitor number", "second best competitor number", "third best competitor number", ...]}}

Here are the responses from each competitor:

{together}

Now respond with the JSON with the ranked order of the competitors, nothing else. Do not include markdown formatting or code blocks."""

judge_messages = [{"role": "user", "content": judge}]

write_results('\n\n####Outputting ranking numbers####\n')

openai = OpenAI()
response = openai.chat.completions.create(
    model="gpt-5-mini",
    messages=judge_messages,
)
results = response.choices[0].message.content
write_results(results)
print("results written to file")

write_results('\n\n#### Outputting Ranked models ####\n')
results_dict = json.loads(results)
ranks = results_dict["results"]
for index, result in enumerate(ranks):
    competitor = competitors[int(result)-1]
    write_results(f"Rank {index+1}: {competitor}\n")

print('Rankings written to file')
print('Script complete')
# ----------------------------------------------------
