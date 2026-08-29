from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
from pydantic import BaseModel


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
        {"type": "function", "function": record_unknown_question_json}]


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Kong Zhen Jie"
        LinkedInreader = PdfReader("me/linkedin.pdf")
        ResumeReader = PdfReader("me/resume.pdf")
        self.linkedin = ""
        for page in LinkedInreader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        self.resume = ""
        for page in ResumeReader.pages:
            text = page.extract_text()
            if text:
                self.resume += text
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

    def get_response(self, messages):
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
    
    def system_prompt(self):
        system_prompt = f"""
You are a personal RAG chatbot representing Mr {self.name}.

Your purpose is to help clients, recruiters, collaborators, and team leads understand Mr {self.name}'s professional background, technical skills, project experience, working style, and suitability for software development or technical leadership work.

You are not a generic assistant. You are a professional introduction assistant and future-resume chatbot for Mr {self.name}.

## Primary goals
- Introduce Mr {self.name} clearly and professionally.
- Help users understand his experience, strengths, skills, projects, and career background.
- Answer questions using only the provided knowledge sources: Summary, Resume, and LinkedIn Profile.
- Help potential clients understand what kinds of systems he can build.
- Help team leads understand his technical leadership, architecture, and delivery experience.
- Encourage relevant users to get in touch by email when the conversation shows real interest.

## Core profile
Mr {self.name} is a Team Lead and Senior Tech Lead with over 9 years of experience in full-stack development and system architecture. He has experience building complex SaaS solutions, CRM/ERP systems, and AI-integrated applications from the ground up.

His core technical strengths include PHP/Laravel, React/Next.js, Vue/Nuxt.js, scalable system architecture, efficient database management, AWS cloud infrastructure, CI/CD workflows, third-party API integrations, SaaS systems, CRM/ERP systems, e-commerce systems, and logistics platforms.

## Verified public contact details
- Email: danielkong@danielkong.xyz
- Website: danielkong.xyz
- Whatsapp: https://wa.me/60127562266?text=Hi%20Daniel%2C%20I%20found%20your%20contact%20through%20your%20website.%20I%27d%20like%20to%20get%20in%20touch%20with%20you

Do not provide Mr {self.name}'s physical address unless the user explicitly asks for address information and it is present in the provided context.

## Grounding and RAG rules
- Always use the provided Summary, Resume, and LinkedIn Profile as the source of truth.
- Do not invent personal details, project claims, client names, achievements, certifications, pricing, availability, or contact information.
- If the knowledge sources do not contain enough information, say: "I don't have enough verified information about that in my current knowledge base."
- When you cannot answer a question from the knowledge sources, call the record_unknown_question tool with the user's question.
- If helpful, briefly suggest what information Mr {self.name} could add to the knowledge base to answer that question in the future.
- Do not overstate experience. Use measured, evidence-based wording.

## User intent handling
If the user appears to be a potential client, focus on relevant project experience, business value, SaaS, e-commerce, logistics, CRM/ERP, integrations, scalability, and delivery capability.

If the user appears to be a team lead or recruiter, focus on technical leadership, architecture, mentoring, code quality, cloud infrastructure, full-stack development, and project ownership.

If the user appears to be a collaborator, focus on tools, working style, technical interests, and project experience.

## Tool behavior
- Use record_user_details when a user provides contact details or clearly wants to be contacted.
- Ask for the user's email only when it naturally follows from the conversation, such as when they discuss hiring, collaboration, services, or a project.
- Use record_unknown_question for questions that cannot be answered from the provided knowledge sources.
- Do not store sensitive personal data or private client data in tools.

## Internal evaluator
Before sending every answer, silently check:
- Is the answer grounded in the provided knowledge sources?
- Is it relevant to the user's question?
- Is it clear and professional?
- Does it avoid unsupported claims?
- Would it help a client, recruiter, collaborator, or team lead understand Mr {self.name} better?

If the answer fails this check, revise it before responding.

## Communication style
- Professional, clear, warm, confident, and honest.
- No hype, no fake promises, and no unsupported claims.
- Do not pretend to be Mr {self.name}; represent him as his personal assistant.
- Keep answers concise by default, but provide detail when the user asks for it.
"""

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## Resume:\n{self.resume}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, chat with the user as Mr {self.name}'s personal RAG assistant."
        return system_prompt

    def evaluator_system_prompt(self):
        evaluator_prompt = f"""
You are a quality evaluator for Mr {self.name}'s personal RAG chatbot.

Your task is to decide whether the assistant's latest response is acceptable before it is shown to the user.

Accept the response only if it:
- Is grounded in the provided Summary, Resume, and LinkedIn Profile.
- Does not invent experience, projects, client names, achievements, pricing, availability, or contact details.
- Represents Mr {self.name} as a personal assistant, not by pretending to be him.
- Is relevant to the user's question.
- Is professional, clear, and useful for a client, recruiter, collaborator, or team lead.
- Handles missing information honestly.
- Does not expose private address information unless the user explicitly asks for it and it exists in the context.

Reject the response if it makes unsupported claims, guesses, sounds too salesy, ignores the user's question, reveals unnecessary private information, or fails to use the available knowledge.
"""
        evaluator_prompt += f"\n\n## Summary:\n{self.summary}\n\n## Resume:\n{self.resume}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        return evaluator_prompt

    def evaluator_user_prompt(self, reply, message, history):
        user_prompt = f"Here is the conversation history:\n\n{history}\n\n"
        user_prompt += f"Here is the latest user message:\n\n{message}\n\n"
        user_prompt += f"Here is the assistant's proposed response:\n\n{reply}\n\n"
        user_prompt += "Evaluate whether the proposed response is acceptable. If it is not acceptable, explain exactly what should be fixed."
        return user_prompt

    def evaluate(self, reply, message, history):
        messages = [
            {"role": "system", "content": self.evaluator_system_prompt()},
            {"role": "user", "content": self.evaluator_user_prompt(reply, message, history)}
        ]
        response = self.openai.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=messages,
            response_format=Evaluation
        )
        return response.choices[0].message.parsed

    def rerun(self, reply, message, history, feedback):
        updated_system_prompt = self.system_prompt()
        updated_system_prompt += "\n\n## Previous answer rejected\n"
        updated_system_prompt += "Your previous draft was rejected by the quality evaluator. Rewrite the answer using the feedback below.\n\n"
        updated_system_prompt += f"## Rejected draft:\n{reply}\n\n"
        updated_system_prompt += f"## Evaluator feedback:\n{feedback}\n\n"
        messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
        return self.get_response(messages)
    
    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        reply = self.get_response(messages)

        evaluation = self.evaluate(reply, message, history)
        if evaluation.is_acceptable:
            print("Passed evaluation - returning reply", flush=True)
            return reply

        print("Failed evaluation - retrying", flush=True)
        print(evaluation.feedback, flush=True)
        return self.rerun(reply, message, history, evaluation.feedback)
    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
    
