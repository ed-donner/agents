class Input:
    def __init__(self, prompt: str):
        self.prompt = prompt
        self.value = None

    def get_input(self) -> str:
        self.value = input(self.prompt)
        return self.value

    def validate_input(self, condition: callable) -> bool:
        return condition(self.value)

    def get_value(self):
        return self.value