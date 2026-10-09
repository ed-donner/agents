from environment import pushover_token, pushover_user
import requests

pushover_url = "https://api.pushover.net/1/messages.json"

class Pushover:
    # notify via pushover
    def __push(self, message):
        print(f"Push: {message}")
        payload = {"user": pushover_user, "token": pushover_token, "message": message}
        requests.post(pushover_url, data=payload)

    # tools to notify when user is exist on a prompt
    def record_user_details(self, email, name="Anonymous", notes="not provided"):
        self.__push(f"Recorded interest from {name} with email {email} and notes {notes}")
        return {"status": "ok"}


    # tools to notify when user not exist on a prompt
    def record_unknown_question(self, question):
        self.__push(f"Recorded '{question}' that couldn't answered")
        return {"status": "ok"}
