# Book Proposal Review Assistant

A Gradio-based chat interface that helps review book proposals using AI. The application reads a PDF book proposal and allows users to interact with an AI agent to get insights and feedback about the proposal.

## Features

- PDF book proposal text extraction
- Interactive chat interface using Gradio
- AI-powered book proposal review using GPT-4
- Asynchronous processing for better performance

## Prerequisites

- Python 3.7+
- OpenAI API key
- Required Python packages:
  - openai
  - gradio
  - pypdf
  - python-dotenv
  - agents (custom package)

## Setup

1. Clone the repository
2. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
3. Place your book proposal PDF file named `book_proposal.pdf` in the same directory as the script
4. Install the required dependencies using uv:
   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install dependencies
   uv pip install openai gradio pypdf python-dotenv
   ```

## Usage

1. Run the script:
   ```bash
   python book_proposal_review.py
   ```
2. The application will:
   - Read the PDF book proposal
   - Initialize the AI agent with the proposal content
   - Launch a Gradio web interface
3. Open the provided local URL in your browser
4. Start chatting with the AI about the book proposal

## How It Works

1. The script reads a PDF book proposal using PyPDF
2. Creates an AI agent with the proposal content as context
3. Launches a Gradio chat interface where users can:
   - Ask questions about the proposal
   - Get feedback and insights
   - Discuss specific aspects of the book proposal

## Notes

- The AI agent is configured to provide concise and relevant responses
- The application requires a valid OpenAI API key
- The PDF file must be named `book_proposal.pdf` and placed in the same directory as the script
- Source of the book proposal is: [Sample Proposal](https://www.ubcpress.ca/asset/1626/sample-proposal-monograph.pdf)

## Error Handling

The application includes error handling for:
- Missing PDF file
- PDF reading errors
- API connection issues

![alt text](<Screenshot 2025-06-11 at 4.32.09 PM.png>)