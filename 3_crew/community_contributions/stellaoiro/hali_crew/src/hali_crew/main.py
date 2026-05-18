from hali_crew.crew import HaliCrew
from datetime import date


def run():
    inputs = {
        'myth': 'The HPV vaccine causes infertility in young girls',
        'current_year': str(date.today().year),
    }
    HaliCrew().crew().kickoff(inputs=inputs)


if __name__ == "__main__":
    run()
