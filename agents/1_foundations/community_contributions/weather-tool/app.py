from dotenv import load_dotenv
from openai import OpenAI
import datetime
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr

import openmeteo_requests

load_dotenv(override=True)

def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )

openmeteo = openmeteo_requests.Client()

def get_weather(place_name:str, countryCode:str = ""):
    coordinates = Geocoding().coordinates_search(place_name, countryCode)
    if coordinates:
        latitude = coordinates["results"][0]["latitude"]
        longitude = coordinates["results"][0]["longitude"]

    else:
        return {"error": "No coordinates found"}
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ["relative_humidity_2m", "temperature_2m", "apparent_temperature", "is_day", "precipitation", "cloud_cover", "wind_gusts_10m"],
        "timezone": "auto",
        "forecast_days": 1
    }
    weather = openmeteo.weather_api(url, params=params)

    current_weather = weather[0].Current()
    current_time = current_weather.Time()

    response = {
        "current_relative_humidity_2m": current_weather.Variables(0).Value(),
        "current_temperature_celcius": current_weather.Variables(1).Value(),
        "current_apparent_temperature_celcius": current_weather.Variables(2).Value(),
        "current_is_day": current_weather.Variables(3).Value(),
        "current_precipitation": current_weather.Variables(4).Value(),
        "current_cloud_cover": current_weather.Variables(5).Value(),
        "current_wind_gusts": current_weather.Variables(6).Value(),
        "current_time": current_time
    }

    return response
    
get_weather_json = {
    "name": "get_weather",
    "description": "Use this tool to get the weather at a given location",
    "parameters": {
        "type": "object",
        "properties": {
            "place_name": {
                "type": "string",
                "description": "The name of the location to get the weather for (city or region name)"
            },
            "countryCode": {
                "type": "string",
                "description": "The two-letter country code of the location"
            }
        },
        "required": ["place_name"],
        "additionalProperties": False
    }
}


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json},
        {"type": "function", "function": get_weather_json}]


class Geocoding:
    """
    A simple Python wrapper for the Open-Meteo Geocoding API.
    """
    def __init__(self):
        """
        Initializes the GeocodingAPI client.
        """
        self.base_url = "https://geocoding-api.open-meteo.com/v1/search"

    def coordinates_search(self, name: str, countryCode: str = ""):
        """
        Searches for the geo-coordinates of a location by name.

        Args:
            name (str): The name of the location to search for.
            countryCode (str): The country code of the location to search for (ISO-3166-1 alpha2).

        Returns:
            dict: The JSON response from the API as a dictionary, or None if an error occurs.
        """
        params = {
            "name": name,
            "count": 1,
            "language": "en",
            "format": "json",
        }
        if countryCode:
            params["countryCode"] = countryCode

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None


class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = os.getenv("BOT_SELF_NAME")
        reader = PdfReader("me/linkedin.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        # system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
        # particularly questions related to {self.name}'s career, background, skills and experience. \
        # Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
        # You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
        # Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
        # You have a tool called get_weather which can be useful in checking the current weather at {self.name}'s location or at the location of the user. But remember to use this information in casual conversation and only if it comes up naturally - don't force it. When you do share weather information, be selective and approximate. Don't offer decimal precision or exact percentages, give a qualitative description with maybe one quantity (like temperature)\
        # If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
        # If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        # Get today's date and store it in a string
        today_date = datetime.date.today().strftime("%Y-%m-%d")
        
        system_prompt = f"""
Today is {today_date}. You are acting as {self.name}, responding to questions on {self.name}'s website. Most visitors are curious about {self.name}'s career, background, skills, and experience—your job is to represent {self.name} faithfully, professionally, and engagingly in those areas. Think of each exchange as a conversation with a potential client or future employer.

You are provided with a summary of {self.name}'s background and LinkedIn profile to help you respond accurately. Focus your answers on relevant professional information.

You have access to a tool called `get_weather`, which you can use to check the weather at {self.name}'s location or the user’s, if the topic comes up **naturally** in conversation. Do not volunteer weather information unprompted. If the user mentions the weather, feel free to make a casual, conversational remark that draws on `get_weather`, but never recite raw data. Use qualitative, human language—mention temperature ranges or conditions loosely (e.g., "hot and muggy," "mild with a breeze," "snow starting to melt").

You also have access to `record_unknown_question`—use this to capture any question you can’t confidently answer, even if it’s off-topic or trivial.

If the user is interested or continues the conversation, look for a natural opportunity to encourage further connection. Prompt them to share their email and record it using the `record_user_details` tool.
"""

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content
    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
    