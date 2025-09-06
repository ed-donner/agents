from chat import Chat
from rag import Retriever
from evaluator import Evaluator

class ChatbotController:
    def __init__(self):
        self.retriever = Retriever()
        self.chatbot = Chat()
        self.evaluator = Evaluator(name="Damla")

    def get_response(self, message, history, recorded_emails):
        chunks = self.retriever.get_relevant_chunks(message)
        reply, new_recorded_emails = self.chatbot.chat(message, history, recorded_emails, chunks)
        evaluation = self.evaluator.evaluate(reply, message, history)

        while not evaluation.is_acceptable:
            print("Retrying due to failed evaluation...")
            reply = self.chatbot.rerun(reply, message, history, evaluation.feedback)
            evaluation = self.evaluator.evaluate(reply, message, history)

        return reply, new_recorded_emails