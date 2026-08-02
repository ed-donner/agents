import os
import re
import subprocess
import time
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

COMPILE_FLAGS = [
    "-Ofast", "-march=native", "-g0", "-mtune=native",
    "-fopenmp", "-fomit-frame-pointer",
]
OUTPUTS_DIR = "outputs"
BINARY_PATH = os.path.join(OUTPUTS_DIR, "fortran_binary")


class FortranCompilerInput(BaseModel):
    source_file: str = Field(
        ...,
        description="Path to the .f90 Fortran source file to compile.",
    )
    output_binary: str = Field(
        default=BINARY_PATH,
        description="Path for the compiled binary output.",
    )


class FortranCompilerTool(BaseTool):
    name: str = "Fortran Compiler"
    description: str = (
        "Compiles a Fortran .f90 source file using gfortran with HPC optimization "
        "flags: -Ofast -march=native -g0 -mtune=native -fopenmp -fomit-frame-pointer. "
        "Returns compilation success status and any error messages."
    )
    args_schema: Type[BaseModel] = FortranCompilerInput

    def _run(self, source_file: str, output_binary: str = BINARY_PATH) -> str:
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
        cmd = ["gfortran"] + COMPILE_FLAGS + ["-o", output_binary, source_file]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                return (
                    f"COMPILATION SUCCESS\n"
                    f"Binary: {output_binary}\n"
                    f"Command: {' '.join(cmd)}\n"
                    f"Stderr: {result.stderr or 'none'}"
                )
            else:
                return (
                    f"COMPILATION FAILED (exit code {result.returncode})\n"
                    f"Command: {' '.join(cmd)}\n"
                    f"Stdout: {result.stdout}\n"
                    f"Stderr: {result.stderr}"
                )
        except subprocess.TimeoutExpired:
            return "COMPILATION FAILED: timeout after 120 seconds"
        except FileNotFoundError:
            return "COMPILATION FAILED: gfortran not found in PATH"


class CodeExecutorInput(BaseModel):
    binary_path: str = Field(
        default=BINARY_PATH,
        description="Path to the compiled Fortran binary to execute.",
    )
    timeout_seconds: int = Field(
        default=300,
        description="Maximum execution time in seconds.",
    )


class CodeExecutorTool(BaseTool):
    name: str = "Fortran Binary Executor"
    description: str = (
        "Executes a compiled Fortran binary, captures stdout, stderr, and "
        "wall-clock timing. Returns the output and execution time."
    )
    args_schema: Type[BaseModel] = CodeExecutorInput

    def _run(self, binary_path: str = BINARY_PATH, timeout_seconds: int = 300) -> str:
        if not os.path.isfile(binary_path):
            return f"EXECUTION FAILED: binary not found at {binary_path}"
        os.chmod(binary_path, 0o755)
        try:
            start = time.perf_counter()
            result = subprocess.run(
                [binary_path], capture_output=True, text=True,
                timeout=timeout_seconds,
            )
            elapsed = time.perf_counter() - start
            return (
                f"EXECUTION COMPLETE\n"
                f"Wall time: {elapsed:.6f} seconds\n"
                f"Exit code: {result.returncode}\n"
                f"Stdout:\n{result.stdout}\n"
                f"Stderr:\n{result.stderr or 'none'}"
            )
        except subprocess.TimeoutExpired:
            return f"EXECUTION FAILED: timeout after {timeout_seconds} seconds"
        except PermissionError:
            return f"EXECUTION FAILED: permission denied on {binary_path}"


class PythonExecutorInput(BaseModel):
    python_code: str = Field(
        ...,
        description="Python source code string to execute for timing comparison.",
    )
    timeout_seconds: int = Field(
        default=600,
        description="Maximum execution time in seconds.",
    )


class PythonExecutorTool(BaseTool):
    name: str = "Python Code Executor"
    description: str = (
        "Executes a Python code string in a subprocess, captures stdout and "
        "wall-clock timing. Used for performance comparison with the Fortran output."
    )
    args_schema: Type[BaseModel] = PythonExecutorInput

    def _run(self, python_code: str, timeout_seconds: int = 600) -> str:
        try:
            start = time.perf_counter()
            result = subprocess.run(
                ["python3", "-c", python_code],
                capture_output=True, text=True, timeout=timeout_seconds,
            )
            elapsed = time.perf_counter() - start
            return (
                f"PYTHON EXECUTION COMPLETE\n"
                f"Wall time: {elapsed:.6f} seconds\n"
                f"Exit code: {result.returncode}\n"
                f"Stdout:\n{result.stdout}\n"
                f"Stderr:\n{result.stderr or 'none'}"
            )
        except subprocess.TimeoutExpired:
            return f"PYTHON EXECUTION FAILED: timeout after {timeout_seconds} seconds"


class OutputFormatterInput(BaseModel):
    fortran_result: str = Field(
        ...,
        description="Full output string returned by the Fortran Binary Executor tool.",
    )
    python_result: str = Field(
        ...,
        description="Full output string returned by the Python Code Executor tool.",
    )
    compile_result: str = Field(
        ...,
        description="Full output string returned by the Fortran Compiler tool.",
    )


class OutputFormatterTool(BaseTool):
    name: str = "Plain Text Output Formatter"
    description: str = (
        "Formats Fortran and Python benchmark results as a plain text report "
        "with no markdown formatting. Parses Wall time from tool outputs automatically. "
        "Writes the report to outputs/final_output.txt and returns the formatted text."
    )
    args_schema: Type[BaseModel] = OutputFormatterInput

    def _run(
        self,
        fortran_result: str,
        python_result: str,
        compile_result: str,
    ) -> str:
        # Parse wall times from tool output strings
        f_match = re.search(r"Wall time:\s*([\d.]+)", fortran_result)
        p_match = re.search(r"Wall time:\s*([\d.]+)", python_result)
        fortran_time = float(f_match.group(1)) if f_match else 0.0
        python_time = float(p_match.group(1)) if p_match else 0.0
        speedup = (python_time / fortran_time) if fortran_time > 0 else 0.0

        def _extract_stdout(text: str) -> str:
            m = re.search(r"Stdout:\n(.*?)(?:\nStderr:|$)", text, re.DOTALL)
            return m.group(1).strip() if m else text.strip()

        fortran_stdout = _extract_stdout(fortran_result)
        python_stdout = _extract_stdout(python_result)

        flags = "-Ofast -march=native -g0 -mtune=native -fopenmp -fomit-frame-pointer"

        report = (
            "PYTHON TO FORTRAN CONVERSION BENCHMARK\n"
            + "=" * 50 + "\n\n"
            + "COMPILATION FLAGS\n"
            + "-" * 20 + "\n"
            + f"{flags}\n\n"
            + "FORTRAN OUTPUT\n"
            + "-" * 20 + "\n"
            + fortran_stdout + "\n"
            + f"Execution Time: {fortran_time:.6f} seconds\n\n"
            + "PYTHON OUTPUT\n"
            + "-" * 20 + "\n"
            + python_stdout + "\n"
            + f"Execution Time: {python_time:.6f} seconds\n\n"
            + "PERFORMANCE SUMMARY\n"
            + "-" * 20 + "\n"
            + f"Fortran time : {fortran_time:.6f} s\n"
            + f"Python time  : {python_time:.6f} s\n"
            + f"Speedup      : {speedup:,.1f}x faster than Python\n"
        )

        output_path = os.path.join(OUTPUTS_DIR, "final_output.txt")
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
        with open(output_path, "w") as fh:
            fh.write(report)

        return report
