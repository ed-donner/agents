#!/usr/bin/env python
import subprocess
from pathlib import Path

from crewai.flow import Flow, and_, listen, start
from pydantic import BaseModel

from engineering_flow_two_crews.crews.backend_crew.backend_crew import BackendCrew
from engineering_flow_two_crews.crews.test_crew.test_crew import TestCrew

class EngineeringFlowState(BaseModel):
    '''State shared by the parallel branches and join step.'''

    backend_requirement: str = '''
Create an Account class that stores a balance. Support deposits and
withdrawals, reject non-positive amounts, and prevent overdrafts.
'''
    test_requirement: str = '''
Test deposits, withdrawals, invalid amounts, and overdrafts with unittest.
'''
    interface_contract: str = '''
File: backend.py
Class: Account
Constructor: Account(opening_balance: float = 0)
Read-only property: balance -> float
Methods: deposit(amount: float) -> None; withdraw(amount: float) -> None
Invalid amounts and overdrafts must raise ValueError.
'''
    backend_code: str = ''
    test_code: str = ''
    test_results: str = ''


class EngineeringFlow(Flow[EngineeringFlowState]):
    '''Run two engineering crews in parallel and join their outputs.'''

    @start()
    def build_backend(self):
        print('Starting the backend crew')
        result = BackendCrew().crew().kickoff(
            inputs={
                'backend_requirement': self.state.backend_requirement,
                'interface_contract': self.state.interface_contract,
            }
        )
        self.state.backend_code = self._clean_python_code(result.raw)
        return self.state.backend_code

    @start()
    def build_tests(self):
        print('Starting the test crew')
        result = TestCrew().crew().kickoff(
            inputs={
                'test_requirement': self.state.test_requirement,
                'interface_contract': self.state.interface_contract,
            }
        )
        self.state.test_code = self._clean_python_code(result.raw)
        return self.state.test_code

    @listen(and_(build_backend, build_tests))
    def integrate_and_test(self):
        '''Wait for both crews, save their code, then run the unit tests.'''
        output_dir = Path(__file__).resolve().parents[2] / 'output'
        output_dir.mkdir(exist_ok=True)

        (output_dir / 'backend.py').write_text(
            self.state.backend_code, encoding='utf-8'
        )
        (output_dir / 'test_backend.py').write_text(
            self.state.test_code, encoding='utf-8'
        )

        # Generated code is run in Docker, not directly on the host.
        command = [
            'docker', 'run', '--rm',
            '-v', f'{output_dir.resolve()}:/workspace',
            '-w', '/workspace', 'python:3.13-slim',
            'python', '-m', 'unittest', '-v', 'test_backend.py',
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            self.state.test_results = completed.stdout + completed.stderr
        except subprocess.TimeoutExpired:
            self.state.test_results = 'Tests stopped after the 60-second limit.'

        (output_dir / 'test_results.txt').write_text(
            self.state.test_results, encoding='utf-8'
        )
        print(self.state.test_results)
        return self.state.test_results

    @staticmethod
    def _clean_python_code(text: str) -> str:
        '''Remove an accidental Markdown fence from a raw code result.'''
        lines = text.strip().splitlines()
        if lines and lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        return '\n'.join(lines).strip() + '\n'


def kickoff():
    EngineeringFlow().kickoff()


def plot():
    EngineeringFlow().plot()


if __name__ == '__main__':
    kickoff()
