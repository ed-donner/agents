# Google Gemini AI Calculator

Created by [Vaibhav Manwatkar](https://github.com/learnwithvaibhavm) as a community contribution.

## Overview

This simple Python application demonstrates how to integrate with Google's Gemini AI model using the `google-generativeai` library. The application asks Gemini to solve a basic mathematical problem (2+2) and displays the AI's response, showcasing the fundamental interaction with Google's Generative AI API.

## Features

- **Google Gemini Integration**: Uses Google's latest Gemini 2.0 Flash Experimental model
- **Environment Variable Management**: Secure API key handling using `python-dotenv`
- **Simple Mathematical Query**: Demonstrates AI's ability to perform basic calculations
- **Clean Output**: Displays the AI's response in a readable format

## Prerequisites

- Python 3.7 or higher
- Google API key with access to Gemini API
- Required Python packages (see Installation section)

## Installation

1. **Clone or download this file** to your local machine

2. **Install required dependencies**:
   ```bash
   pip install google-generativeai python-dotenv
   ```
   
   Or if using `uv`:
   ```bash
   uv add google-generativeai python-dotenv
   ```

3. **Set up your Google API key**:
   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a `.env` file in the same directory as the script
   - Add your API key to the `.env` file:
     ```text
     GOOGLE_API_KEY=your_actual_api_key_here
     ```

## Usage

1. **Run the application**:
   ```bash
   python 1_lab1_google.py
   ```

2. **Expected output**:
   ```
   4
   ```

## Code Structure

```python
from dotenv import load_dotenv
load_dotenv(override=True)

import os
import google.generativeai as genai

# Configure the API key
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Initialize the model
model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")

# Generate content
response = model.generate_content(["What is 2+2?"])
print(response.text)
```

## Key Components

### 1. Environment Setup
- `load_dotenv(override=True)`: Loads environment variables from `.env` file
- `os.getenv('GOOGLE_API_KEY')`: Retrieves the API key securely

### 2. Model Configuration
- `genai.configure()`: Sets up the API key for authentication
- `genai.GenerativeModel()`: Initializes the Gemini model with specified version

### 3. Content Generation
- `model.generate_content()`: Sends a prompt to the AI model
- `response.text`: Extracts the text response from the AI

## Model Information

- **Model Used**: `gemini-2.0-flash-exp` (Gemini 2.0 Flash Experimental)
- **Capabilities**: Text generation, reasoning, mathematical calculations
- **Input Format**: List of strings or single string
- **Output Format**: Response object with `.text` attribute

## Error Handling

The application includes a `pyright: ignore[reportMissingImports]` comment to suppress type checker warnings for the `google.generativeai` import, which is a common practice when the package might not be installed in all environments.

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Install the required package:
   ```bash
   pip install google-generativeai
   ```

2. **API Key Error**: Ensure your `.env` file contains a valid `GOOGLE_API_KEY`

3. **Authentication Error**: Verify your API key has access to the Gemini API

## Extending the Application

This basic example can be extended to:
- Ask more complex mathematical questions
- Implement conversation loops
- Add error handling for API failures
- Create a user interface for interactive queries
- Process different types of prompts beyond mathematics

## Dependencies

- `google-generativeai`: Google's official Python client for Generative AI
- `python-dotenv`: Loads environment variables from `.env` files

## License

This project is part of the community contributions for the Agents course and follows the same licensing terms.

## Contributing

Feel free to fork this project and submit improvements or additional features as pull requests.

## Author

**Vaibhav Manwatkar**
- GitHub: [@learnwithvaibhavm](https://github.com/learnwithvaibhavm)
- This is a community contribution to the Agents course