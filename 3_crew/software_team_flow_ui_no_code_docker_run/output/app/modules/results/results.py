class Results:
    def __init__(self):
        self.data = []

    def add_result(self, result):
        self.data.append(result)

    def get_results(self):
        return self.data

    def clear_results(self):
        self.data.clear()