
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import os
import app_tools
import json
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
class validation(BaseModel):
    is_acceptable: bool
    feedback: str

class emailResp(BaseModel):
    body: str
    subject: str
class Person:

    def __init__(self):
        load_dotenv(override=True)
        self.openai = OpenAI()
        self.gemeni = os.getenv("GOOGLE_API_KEY")
        self.gemeniUrl = os.getenv("GOOGLE_BASE_URL")
        reader = PdfReader("resume.pdf")
        self.name = "Yasaman"
        self.tools = [{"type": "function", "function": app_tools.record_unkown_question_json},{"type":"function", "function": app_tools.store_email_json}]
        self.resume = ""
        self.emailFrom = os.getenv("FROM_EMAIL")
        self.emailPassword = os.getenv("APP_GMAIL_PASSWORD")
        self.gemeni = OpenAI(api_key=os.getenv("GOOGLE_API_KEY"),base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
        for page in reader.pages:
            text = page.extract_text()
            if text: 
                self.resume += text

    def system_chat_promt(self): 
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
        particularly questions related to {self.name}'s career, background, skills and experience. \
        Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
        You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
        Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
        If you don't know the answer to any question, use your record_unkown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
        If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and name and record it using your store_email tool."\
        "If they already provided their name or email do not aks them again . always check the history."

        system_prompt += f"\n\n ## Resume :\n{self.resume}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt

    def email_system_prompt(self):
        system_prompt = f"""You are acting as {self.name}, creating a follow-up email for a user who recently chatted with {self.name}'s chatbot.
            Your task:
            - Review the chat history provided and craft an engaging, professional email response base on the history
            - provide relative subject base on the email body you create.
            - Maintain a warm, personable tone while keeping language professional and polite like talking to a potential client or future employer who came cross the website.
            - Include relevant references or light humor from the conversation where appropriate
            - Encourage continued engagement and make the recipient eager to respond
            - Keep the email concise (2-4 short paragraphs)
            - If any quistions were asked tell them {self.name} will email them the answer and don't answer the question.
            - If the they provided their name start the email by their name like Hello Dear ##name

            Tone guidelines:
            - Professional but approachable (like a friendly colleague, not a robot)
            - Use conversational language while maintaining professionalism
            - Add personality through relevant observations from the chat, not forced jokes

            Structure:
            1. Warm greeting with reference to something specific from their chat
            2. Address any questions or topics they raised
            3. Clear call-to-action or next steps
            4. Professional closing

            Avoid: Generic templates, excessive formality, unrelated humor, or anything that feels salesy."""
        return system_prompt
    
    def evaluate_system_prompt(self):
        system_prompt = f"You are an evaluator that decids weather a email response to the user who had chat with {self.name}"\
        "is acceptable. You are provided with a conversation between a User and an Agent. Your taks is to decide wether the Agent's response for email body is acceptable quality" \
        "The Agent has been instructed to be professional and engagging, as if as if talking to a potential client or future employer who came cross the website." \
        "If user had any question Agent shouln't provide and answer, it just tell user that {self.name} will contact them shortly" \
        "The Agent has been provided with context on {self.name} in the form of their resume details. Here's the information:"

        system_prompt += f"\n\n ## Resume :\n{self.resume}\n\n"
        system_prompt += f"With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."
        return system_prompt
    
    def chat(self, message, history, session_id):
        messages = [{"role":"system", "content": self.system_chat_promt()}] + history + [{"role":"user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=self.tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = app_tools.handle_tool_call(tool_calls, session_id=session_id)
                messages.append(message)
                messages.extend(results)
            else:
                done = True

        return response.choices[0].message.content
    def evaluator_user_prompt(self,reply, history):
        user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
        user_prompt += f"Here's the response from the Agent: \n\n{reply}\n\n"
        user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
        return user_prompt

    def evaluate(self,reply, history) -> validation:
        messages = [{"role":"user", "content": self.evaluator_user_prompt(reply,history)}, {"role":"system", "content": self.evaluate_system_prompt()}] 
        resposne = self.gemeni.beta.chat.completions.parse(model="gemini-2.0-flash", messages=messages, response_format=validation)
        return resposne.choices[0].message.parsed
    
    def rerun(self,reply,history, feedback) -> emailResp:
        update_system_prompt = self.email_system_prompt() + "\n\n## Previuos answr rejected \n You just tried to reply, but the quality control rejected your reply"
        update_system_prompt += f"## You attempted to answer: {reply}"
        update_system_prompt += f"## reason for rejection {feedback}"
        messages = [{"role":"user", "content":"Please provide good quality of email resposne."}] + history + [{"role":"system", "content":update_system_prompt}]
        response = self.openai.beta.chat.completions.parse(model="gpt-4o-mini", messages=messages, response_format=emailResp)
        return response.choices[0].message.parsed
    
    def email(self, sessiondata):
        messages = [{"role": "system", "content": self.email_system_prompt()}] + sessiondata["history"]
        reply = self.openai.beta.chat.completions.parse(model="gpt-4o-mini", messages=messages,response_format=emailResp)
        resp = reply.choices[0].message.parsed
        evaluation = self.evaluate(reply=reply.choices[0].message.content, history=sessiondata["history"])
        if not evaluation.is_acceptable:
            reReply = self.rerun(reply=reply,history=sessiondata["history"],feedback=evaluation.feedback)
            resp = reReply
        self.send_email(sessiondata=sessiondata,reply=resp)


    def send_email(self,sessiondata,reply=""):
        msg = MIMEMultipart("alternative")
        msg["From"] = self.emailFrom
        if  reply:
            email = sessiondata["email"]
        else:
            email = os.getenv("TO_EMAIL")

        msg["To"] = email
        if not reply:
            msg["Subject"] = "follow up"
            body = f"{sessiondata["name"]} reach out to you and had this questions {sessiondata["questions"]} \n and this what we chat {sessiondata["history"]},here is email {sessiondata["email"]}"
            msg.attach(MIMEText(body, "plain"))

        else:
            msg["Subject"] = reply.subject
            msg.attach(MIMEText(reply.body, "plain"))
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.set_debuglevel(1)  # prints SMTP conversation to stdout for debugging
                server.login(self.emailFrom, self.emailPassword)
                # sendmail returns a dict of failures; empty dict means success
                failures = server.sendmail(self.emailFrom, [email], msg.as_string())
        except smtplib.SMTPAuthenticationError as e:
            return {"ok": False, "error": f"SMTP auth failed: {e}"}
        except smtplib.SMTPException as e:
            return {"ok": False, "error": f"SMTP error: {e}"}
        except Exception as e:
            return {"ok": False, "error": f"Unexpected error: {e}"}
        if failures:
            print(failures)
            return {"ok": False, "error": f"Failed recipients: {failures}"}
        
  