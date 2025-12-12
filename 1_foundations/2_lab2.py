# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: .venv
#     language: python
#     name: python3
# ---

# %% [markdown]
# ## Welcome to the Second Lab - Week 1, Day 3
#
# Today we will work with lots of models! This is a way to get comfortable with APIs.

# %% [markdown]
# <table style="margin: 0; text-align: left; width:100%">
#     <tr>
#         <td style="width: 150px; height: 150px; vertical-align: middle;">
#             <img src="../assets/stop.png" width="150" height="150" style="display: block;" />
#         </td>
#         <td>
#             <h2 style="color:#ff7800;">Important point - please read</h2>
#             <span style="color:#ff7800;">The way I collaborate with you may be different to other courses you've taken. I prefer not to type code while you watch. Rather, I execute Jupyter Labs, like this, and give you an intuition for what's going on. My suggestion is that you carefully execute this yourself, <b>after</b> watching the lecture. Add print statements to understand what's going on, and then come up with your own variations.<br/><br/>If you have time, I'd love it if you submit a PR for changes in the community_contributions folder - instructions in the resources. Also, if you have a Github account, use this to showcase your variations. Not only is this essential practice, but it demonstrates your skills to others, including perhaps future clients or employers...
#             </span>
#         </td>
#     </tr>
# </table>

# %%
# Start with imports - ask ChatGPT to explain any package that you don't know

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
from IPython.display import Markdown, display

# %%
# Always remember to do this!
load_dotenv(override=True)

# %%
# Print the key prefixes to help with any debugging

openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
groq_api_key = os.getenv('GROQ_API_KEY')

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

# %%
request = "Produce one sentence that could serve as a challenging question. Do not include any constraints, rubrics, assumptions, or evaluation criteria."
messages = [{"role": "user", "content": request}]

# %%
messages
openai = OpenAI()
response = openai.chat.completions.create(
    model="gpt-5-mini",
    messages=messages,
    max_completion_tokens=1000
)
question = response.choices[0].message.content
print(question)
display(Markdown(question))


# %%
competitors = []
answers = []
messages = [{"role": "user", "content": question}]

# %% [markdown]
# ## Note - update since the videos
#
# I've updated the model names to use the latest models below, like GPT 5 and Claude Sonnet 4.5. It's worth noting that these models can be quite slow - like 1-2 minutes - but they do a great job! Feel free to switch them for faster models if you'd prefer, like the ones I use in the video.

# %%
# The API we know well
# I've updated this with the latest model, but it can take some time because it likes to think!
# Replace the model with gpt-4.1-mini if you'd prefer not to wait 1-2 mins

model_name = "gpt-5-nano"

response = openai.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content

display(Markdown(answer))
competitors.append(model_name)
answers.append(answer)

# %%
# Anthropic has a slightly different API, and Max Tokens is required

model_name = "claude-sonnet-4-5"

claude = Anthropic()
response = claude.messages.create(model=model_name, messages=messages, max_tokens=1000)
answer = response.content[0].text

display(Markdown(answer))
competitors.append(model_name)
answers.append(answer)

# %%
gemini = OpenAI(api_key=google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model_name = "gemini-2.5-flash"

response = gemini.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content

display(Markdown(answer))
competitors.append(model_name)
answers.append(answer)

# %%
deepseek = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1")
model_name = "deepseek-chat"

response = deepseek.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content

display(Markdown(answer))
competitors.append(model_name)
answers.append(answer)

# %%
# Updated with the latest Open Source model from OpenAI

groq = OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
model_name = "openai/gpt-oss-120b"

response = groq.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content

display(Markdown(answer))
competitors.append(model_name)
answers.append(answer)


# %% [markdown]
# ## For the next cell, we will use Ollama
#
# Ollama runs a local web service that gives an OpenAI compatible endpoint,  
# and runs models locally using high performance C++ code.
#
# If you don't have Ollama, install it here by visiting https://ollama.com then pressing Download and following the instructions.
#
# After it's installed, you should be able to visit here: http://localhost:11434 and see the message "Ollama is running"
#
# You might need to restart Cursor (and maybe reboot). Then open a Terminal (control+\`) and run `ollama serve`
#
# Useful Ollama commands (run these in the terminal, or with an exclamation mark in this notebook):
#
# `ollama pull <model_name>` downloads a model locally  
# `ollama ls` lists all the models you've downloaded  
# `ollama rm <model_name>` deletes the specified model from your downloads

# %% [markdown]
# <table style="margin: 0; text-align: left; width:100%">
#     <tr>
#         <td style="width: 150px; height: 150px; vertical-align: middle;">
#             <img src="../assets/stop.png" width="150" height="150" style="display: block;" />
#         </td>
#         <td>
#             <h2 style="color:#ff7800;">Super important - ignore me at your peril!</h2>
#             <span style="color:#ff7800;">The model called <b>llama3.3</b> is FAR too large for home computers - it's not intended for personal computing and will consume all your resources! Stick with the nicely sized <b>llama3.2</b> or <b>llama3.2:1b</b> and if you want larger, try llama3.1 or smaller variants of Qwen, Gemma, Phi or DeepSeek. See the <A href="https://ollama.com/models">the Ollama models page</a> for a full list of models and sizes.
#             </span>
#         </td>
#     </tr>
# </table>

# %%
# !ollama pull llama3.2

# %%
ollama = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
model_name = "llama3.1:8b"

response = ollama.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content

display(Markdown(answer))
competitors.append(model_name)
answers.append(answer)

# %%
# So where are we?

print(competitors)
print(answers)


# %%
# It's nice to know how to use "zip"
for competitor, answer in zip(competitors, answers):
    print(f"Competitor: {competitor}\n\n{answer}")


# %%
# Let's bring this together - note the use of "enumerate"

together = ""
for index, answer in enumerate(answers):
    together += f"# Response from competitor {index+1}\n\n"
    together += answer + "\n\n"

# %%
print(together)
print(len(together))

# %%
judge = f"""You are judging a competition between {len(competitors)} competitors.
Each model has been given this question:

{question}

Your job is to evaluate each response for clarity and strength of argument, and rank them in order of best to worst.
Respond with JSON, and only JSON, with the following format:
{{"results": ["best competitor number", "second best competitor number", "third best competitor number", ...]}}

Here are the responses from each competitor:

{together}

Now respond with the JSON with the ranked order of the competitors, nothing else. Do not include markdown formatting or code blocks."""


# %%
print(judge)

# %%
# Add this cell anywhere to see what you've actually collected:
print(f"Number of competitors: {len(competitors)}")
print(f"Number of answers: {len(answers)}")
print("Competitors:", competitors)

# %%
print(question[:50], "...")
print(len(competitors), len(answers), len(ranks))

# %%
judge_messages = [{"role": "user", "content": judge}]

# %%
# Judgement time!

openai = OpenAI()
response = openai.chat.completions.create(
    model="o3-mini",
    messages=judge_messages,
)
results = response.choices[0].message.content
print(results)


# %%
# OK let's turn this into results!

results_dict = json.loads(results)
ranks = results_dict["results"]
for index, result in enumerate(ranks):
    competitor = competitors[int(result)-1]
    print(f"Rank {index+1}: {competitor}")

# %% [markdown]
# <table style="margin: 0; text-align: left; width:100%">
#     <tr>
#         <td style="width: 150px; height: 150px; vertical-align: middle;">
#             <img src="../assets/exercise.png" width="150" height="150" style="display: block;" />
#         </td>
#         <td>
#             <h2 style="color:#ff7800;">Exercise</h2>
#             <span style="color:#ff7800;">Which pattern(s) did this use? Try updating this to add another Agentic design pattern.
#             </span>
#         </td>
#     </tr>
# </table>

# %% [markdown]
# # Workflow design patterns
#
# - Sequential. Because the tasks are being run sequentially, one after the other.
# - Prompt chaining. The first prompt is used to generate the second prompt.
# - Parallelization (structural). While the examples run sequentially in the notebook, the competitor models are independent and could be executed in parallel, so the workflow is designed to support parallelization even if it isn’t exploited here.
#
# While the workflow includes an evaluator role, it does not implement a full evaluator–optimizer loop as depicted in the reference diagram, since no feedback-driven regeneration or iterative optimization occurs.
#
# ---
#
# I will attempt to add explicit feedback to the workflow, turning "judge" into an evaluator-optimizer, triggering a revision loop:
#
# - Evaluate - judge produces structured critique, including what to improve.
# - Optimize - competitor models attempt to improve.
# - Evaluate again - judge ranks again, or compares v1 and v2 improvement.
#
# Scratch that. To avoid turning this into prompt soup, I'm going to feed the ranking back to the model, and ask it to improve the response, to achieve a better ranking.

# %% [markdown]
# ## Evaluator-Optimizer Loop Implementation
#
# Feed the ranking back to each model and ask them to improve their response.
#

# %%
# Store original answers and prepare for improvements
original_answers = answers.copy()
improved_answers = []

def get_improvement_prompt(question, original_answer, rank, total):
    """Create a prompt asking the model to improve its response based on ranking feedback."""
    return f"""You previously answered this question:

{question}

Your answer was:
{original_answer}

You were ranked #{rank} out of {total} competitors.

Please improve your response to achieve a better ranking. Focus on clarity and strength of argument."""

def get_rank_for_competitor(competitor_idx, ranks):
    """Find the rank position (1-based) for a given competitor index (0-based)."""
    competitor_num = str(competitor_idx + 1)
    if competitor_num in ranks:
        return ranks.index(competitor_num) + 1
    return len(ranks)  # If not found, assume last place

print("Ready to generate improved answers!")


# %%
# Improve GPT-5-nano response
competitor_idx = 0
model_name = competitors[competitor_idx]
rank = get_rank_for_competitor(competitor_idx, ranks)

improvement_prompt = get_improvement_prompt(question, original_answers[competitor_idx], rank, len(competitors))
improve_messages = [{"role": "user", "content": improvement_prompt}]

response = openai.chat.completions.create(model=model_name, messages=improve_messages)
improved_answer = response.choices[0].message.content

display(Markdown(f"**{model_name} (was rank #{rank}) improved response:**"))
display(Markdown(improved_answer))
improved_answers.append(improved_answer)


# %%
# Improve Claude response
competitor_idx = 1
model_name = competitors[competitor_idx]
rank = get_rank_for_competitor(competitor_idx, ranks)

improvement_prompt = get_improvement_prompt(question, original_answers[competitor_idx], rank, len(competitors))
improve_messages = [{"role": "user", "content": improvement_prompt}]

response = claude.messages.create(model=model_name, messages=improve_messages, max_tokens=1000)
improved_answer = response.content[0].text

display(Markdown(f"**{model_name} (was rank #{rank}) improved response:**"))
display(Markdown(improved_answer))
improved_answers.append(improved_answer)


# %%
# Improve Gemini response
competitor_idx = 2
model_name = competitors[competitor_idx]
rank = get_rank_for_competitor(competitor_idx, ranks)

improvement_prompt = get_improvement_prompt(question, original_answers[competitor_idx], rank, len(competitors))
improve_messages = [{"role": "user", "content": improvement_prompt}]

response = gemini.chat.completions.create(model=model_name, messages=improve_messages)
improved_answer = response.choices[0].message.content

display(Markdown(f"**{model_name} (was rank #{rank}) improved response:**"))
display(Markdown(improved_answer))
improved_answers.append(improved_answer)


# %%
# Improve Ollama/Llama response
competitor_idx = 3
model_name = competitors[competitor_idx]
rank = get_rank_for_competitor(competitor_idx, ranks)

improvement_prompt = get_improvement_prompt(question, original_answers[competitor_idx], rank, len(competitors))
improve_messages = [{"role": "user", "content": improvement_prompt}]

response = ollama.chat.completions.create(model=model_name, messages=improve_messages)
improved_answer = response.choices[0].message.content

display(Markdown(f"**{model_name} (was rank #{rank}) improved response:**"))
display(Markdown(improved_answer))
improved_answers.append(improved_answer)


# %%
# Improve Groq (openai/gpt-oss-120b) response
competitor_idx = 4
model_name = competitors[competitor_idx]
rank = get_rank_for_competitor(competitor_idx, ranks)

improvement_prompt = get_improvement_prompt(question, original_answers[competitor_idx], rank, len(competitors))
improve_messages = [{"role": "user", "content": improvement_prompt}]

response = groq.chat.completions.create(model=model_name, messages=improve_messages)
improved_answer = response.choices[0].message.content

display(Markdown(f"**{model_name} (was rank #{rank}) improved response:**"))
display(Markdown(improved_answer))
improved_answers.append(improved_answer)


# %%
# Verify we have all improved answers
print(f"Original answers: {len(original_answers)}")
print(f"Improved answers: {len(improved_answers)}")
print("Competitors:", competitors)


# %%
# Build the improved responses for re-judging
improved_together = ""
for index, answer in enumerate(improved_answers):
    improved_together += f"# Response from competitor {index+1}\n\n"
    improved_together += answer + "\n\n"

print(f"Total improved response length: {len(improved_together)}")


# %%
# Re-judge the improved responses
judge_v2 = f"""You are judging a competition between {len(competitors)} competitors.
Each model has been given this question:

{question}

Your job is to evaluate each response for clarity and strength of argument, and rank them in order of best to worst.
Respond with JSON, and only JSON, with the following format:
{{"results": ["best competitor number", "second best competitor number", "third best competitor number", ...]}}

Here are the IMPROVED responses from each competitor:

{improved_together}

Now respond with the JSON with the ranked order of the competitors, nothing else. Do not include markdown formatting or code blocks."""

judge_v2_messages = [{"role": "user", "content": judge_v2}]


# %%
# Round 2 judgement!
response = openai.chat.completions.create(
    model="o3-mini",
    messages=judge_v2_messages,
)
results_v2 = response.choices[0].message.content
print(results_v2)


# %%
# Compare Round 1 vs Round 2 rankings
results_v2_dict = json.loads(results_v2)
ranks_v2 = results_v2_dict["results"]

print("=" * 50)
print("RANKING COMPARISON: Before vs After Improvement")
print("=" * 50)

print("\n📊 ROUND 1 (Original responses):")
for index, result in enumerate(ranks):
    competitor = competitors[int(result)-1]
    print(f"  Rank {index+1}: {competitor}")

print("\n📊 ROUND 2 (Improved responses):")
for index, result in enumerate(ranks_v2):
    competitor = competitors[int(result)-1]
    print(f"  Rank {index+1}: {competitor}")

print("\n🔄 CHANGES:")
for i, comp in enumerate(competitors):
    comp_num = str(i + 1)
    old_rank = ranks.index(comp_num) + 1 if comp_num in ranks else "N/A"
    new_rank = ranks_v2.index(comp_num) + 1 if comp_num in ranks_v2 else "N/A"
    
    if old_rank != "N/A" and new_rank != "N/A":
        change = old_rank - new_rank
        if change > 0:
            emoji = "⬆️"
            change_str = f"+{change}"
        elif change < 0:
            emoji = "⬇️"
            change_str = str(change)
        else:
            emoji = "➡️"
            change_str = "0"
        print(f"  {comp}: {old_rank} → {new_rank} ({emoji} {change_str})")


# %% [markdown]
# <table style="margin: 0; text-align: left; width:100%">
#     <tr>
#         <td style="width: 150px; height: 150px; vertical-align: middle;">
#             <img src="../assets/business.png" width="150" height="150" style="display: block;" />
#         </td>
#         <td>
#             <h2 style="color:#00bfff;">Commercial implications</h2>
#             <span style="color:#00bfff;">These kinds of patterns - to send a task to multiple models, and evaluate results,
#             are common where you need to improve the quality of your LLM response. This approach can be universally applied
#             to business projects where accuracy is critical.
#             </span>
#         </td>
#     </tr>
# </table>
