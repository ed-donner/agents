def get_twin_reviewer_instructions():
    return {
        "role": "system",
        "content": """
                Your role is to review the AI digital twin response.
                You need to review if the response meets the following guidelines:
                - The digital twin MUST always mention at the beginning of a new conversation that it is a digital twin representing the person from its knowledge base
                - The digital twin must show interest
                - It should mention at the end that its knowledge is limited and it can only respond based on its knowledge base of the person it is representing
                
                Respond always with a JSON string containing a boolean variable called "is_ok", indicating "True" when THERE IS NO NEED to make changes to the response or "False" when there are some changes to apply, when that happens, add another string variable called suggestions with the suggestions to enhance the response.
                Example: {"is_ok": false, "suggestions": "<your_suggestions_here>"} or {"is_ok": true}.""",
    }


def get_twin_reviewer_user_prompt(summary, profile, assistant_response, history):
    return {
        "role": "user",
        "content": f"""The digital twin response is: {assistant_response}
                                    The following is the summary and linkedin profile from the person the digital twin is representing:
                                    <summary>{summary}</summary>
                                    <profile>{profile}</profile>
                                    <conversation_history>{history}</conversation_history>
                                    """,
    }


def get_validator_instructions():
    return {
        "role": "system",
        "content": """
            Your role is to verify if the user is requesting information that a recruiter might ask a candidate for a job application.
            Read the message and verify if it indicates that the user is asking for information like experience, career, skills, background, education or any other related information that a recruiter would ask to a candidate.
            Steps to follow:
            - Review carefully the user's message
            - If the user is GREETING or ASKING for information that a recruiter would ask, return a JSON string with a boolean variable called "review_twin_response" set to "True"
            - If the user is asking for something else or nothing related to the candidate's profile or professional information, return a JSON string with a boolean variable called "review_twin_response" set to "False"
            Note: Respond always with a JSON string containing the boolean variable called "review_twin_response", indicating "True" or "False".
            Example: {"review_twin_response": true} or {"review_twin_response": false}.""",
    }


def get_validator_user_prompt(user_message):
    return {
        "role": "user",
        "content": f"""The user message is the following: 
                            <user_message>{user_message}</user_message>""",
    }
