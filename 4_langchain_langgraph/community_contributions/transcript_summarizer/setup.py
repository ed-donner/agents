from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="transcript-summarizer",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A scalable transcript summarizer using Ollama and LLaMA3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/transcript-summarizer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.23.3",
            "black>=23.12.1",
            "isort>=5.13.2",
            "mypy>=1.8.0",
            "pre-commit>=3.6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "transcript-summarizer=main:main",
        ],
    },
)
