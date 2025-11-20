"""This module contains functions to interact with the OpenRouter API.
   It load dotenv, OpenAI and other necessary packages to interact
   with the OpenRouter API.
   Also stores the chat history in a list."""
from dotenv import load_dotenv
from openai import OpenAI
from IPython.display import Markdown, display
import os

# override any existing environment variables
load_dotenv(override=True)

# load
openrouter_api_key = os.getenv('OPENROUTER_API_KEY')

if openrouter_api_key:
    print(f"OpenAI API Key exists and begins {openrouter_api_key[:8]}")
else:
    print("OpenAI API Key not set - please head to the troubleshooting guide in the setup folder")
    

chatHistory = []


def chatWithOpenRouter(model:str, prompt:str)-> str:
    """ This function takes a model and a prompt and shows the response
        in markdown format. It uses the OpenAI class from the openai package"""

    # here instantiate the OpenAI class but with the OpenRouter
    # API URL
    llmRequest = OpenAI(
        api_key=openrouter_api_key,
        base_url="https://openrouter.ai/api/v1"
    )

    # add the prompt to the chat history
    chatHistory.append({"role": "user", "content": prompt})

    # make the request to the OpenRouter API
    response = llmRequest.chat.completions.create(
        model=model,
        messages=chatHistory
    )

    # get the output from the response
    assistantResponse = response.choices[0].message.content

    # show the answer
    display(Markdown(f"**Assistant:** {assistantResponse}"))
    
    # add the assistant response to the chat history
    chatHistory.append({"role": "assistant", "content": assistantResponse})


def getOpenrouterResponse(model:str, prompt:str)-> str:
    """
    This function takes a model and a prompt and returns the response
    from the OpenRouter API, using the OpenAI class from the openai package.
    """
    llmRequest = OpenAI(
        api_key=openrouter_api_key,
        base_url="https://openrouter.ai/api/v1"
    )

    # add the prompt to the chat history
    chatHistory.append({"role": "user", "content": prompt})

    # make the request to the OpenRouter API
    response = llmRequest.chat.completions.create(
        model=model,
        messages=chatHistory
    )

    # get the output from the response
    assistantResponse = response.choices[0].message.content
    
    # add the assistant response to the chat history
    chatHistory.append({"role": "assistant", "content": assistantResponse})

    # return the assistant response
    return assistantResponse


#clear chat history
def clearChatHistory():
    """ This function clears the chat history. It can't be undone!"""
    chatHistory.clear()