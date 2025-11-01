"""
Unified LLM Caller for OpenAI GPT and Google Gemini, Claude
"""

import os
from openai import OpenAI
from anthropic import Anthropic
from pydantic import BaseModel
from typing import Optional, Union, Type, List, Dict
from enum import Enum


class OpenAIModel(str, Enum):
    """Available OpenAI models"""
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    O1_PREVIEW = "o1-preview"
    O1_MINI = "o1-mini"


class GeminiModel(str, Enum):
    """Available Gemini models"""
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_5_FLASH_8B = "gemini-1.5-flash-8b"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_EXP_1206 = "gemini-exp-1206"

class ClaudeModel(str, Enum):
    """Available Claude models"""
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_5_HAIKU = "claude-3-5-haiku-20241022"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"


def _build_messages(prompt: str, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
    """Build messages array for API call"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    return messages


def _call_llm(
    client: OpenAI,
    prompt: str,
    model: str,
    system_prompt: Optional[str] = None,
    response_format: Optional[Type[BaseModel]] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> Union[str, BaseModel]:
    """
    Internal function to call LLM API
    
    Args:
        client: OpenAI client instance
        prompt: The prompt to send
        model: Model string to use
        system_prompt: System message (optional)
        response_format: Pydantic model class for structured output (optional)
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum tokens in response (optional)
    
    Returns:
        String or Pydantic object
    """
    messages = _build_messages(prompt, system_prompt)
    
    call_params = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    
    if max_tokens:
        call_params["max_tokens"] = max_tokens
    
    if response_format:
        completion = client.beta.chat.completions.parse(
            **call_params,
            response_format=response_format
        )
        return completion.choices[0].message.parsed
    else:
        completion = client.chat.completions.create(**call_params)
        return completion.choices[0].message.content


def gpt_call(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: OpenAIModel = OpenAIModel.GPT_4O_MINI,
    response_format: Optional[Type[BaseModel]] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    api_key: Optional[str] = None
) -> Union[str, BaseModel]:
    """
    Call OpenAI GPT API
    
    Args:
        prompt: The prompt to send
        system_prompt: System message to set behavior/context (optional)
        model: Model to use (default: GPT-4o-mini)
        response_format: Pydantic model class for structured output (optional)
        temperature: Sampling temperature, controls randomness/creativity (0.0-2.0)
        max_tokens: Maximum tokens in response (optional)
        api_key: OpenAI API key (optional, uses OPENAI_API_KEY env var if not provided)
    
    Returns:
        String message if no response_format, or Pydantic object if provided
    """
    client = OpenAI(api_key=api_key) if api_key else OpenAI()
    
    return _call_llm(
        client=client,
        prompt=prompt,
        model=model.value,
        system_prompt=system_prompt,
        response_format=response_format,
        temperature=temperature,
        max_tokens=max_tokens
    )


def gemini_call(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: GeminiModel = GeminiModel.GEMINI_2_0_FLASH,
    response_format: Optional[Type[BaseModel]] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    api_key: Optional[str] = None
) -> Union[str, BaseModel]:
    """
    Call Google Gemini API
    
    Args:
        prompt: The prompt to send
        system_prompt: System message to set behavior/context (optional)
        model: Model to use (default: Gemini 2.0 Flash)
        response_format: Pydantic model class for structured output (optional)
        temperature: Sampling temperature, controls randomness/creativity (0.0-2.0)
        max_tokens: Maximum tokens in response (optional)
        api_key: Google AI API key (optional, uses GOOGLE_API_KEY env var if not provided)
    
    Returns:
        String message if no response_format, or Pydantic object if provided
    """
    api_key = api_key or os.getenv('GOOGLE_API_KEY')
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    
    return _call_llm(
        client=client,
        prompt=prompt,
        model=model.value,
        system_prompt=system_prompt,
        response_format=response_format,
        temperature=temperature,
        max_tokens=max_tokens
    )


def claude_call(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: ClaudeModel = ClaudeModel.CLAUDE_3_HAIKU,
    response_format: Optional[Type[BaseModel]] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = 1024,
    api_key: Optional[str] = None
) -> Union[str, BaseModel]:
    """
    Call Anthropic Claude API
    
    Args:
        prompt: The prompt to send
        system_prompt: System message to set behavior/context (optional)
        model: Model to use (default: Claude 3.5 Sonnet)
        response_format: Pydantic model class for structured output (optional)
        temperature: Sampling temperature, controls randomness/creativity (0.0-1.0)
        max_tokens: Maximum tokens in response (default: 1024)
        api_key: Anthropic API key (optional, uses ANTHROPIC_API_KEY env var if not provided)
    
    Returns:
        String message if no response_format, or Pydantic object if provided
    """
    api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
    client = Anthropic(api_key=api_key)
    
    # Build messages
    messages = _build_messages(prompt, system_prompt=None)  # Claude handles system separately
    
    # Prepare call parameters
    call_params = {
        "model": model.value,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    # Add system prompt if provided (Claude uses separate system parameter)
    if system_prompt:
        call_params["system"] = system_prompt
    print(call_params)
    # Call API
    if response_format:
        # Structured output with Pydantic
        completion = client.messages.create(
            **call_params,
            response_format=response_format
        )
        # Parse the response based on Pydantic model
        return response_format.model_validate_json(completion.content[0].text)
    else:
        # Plain text output
        completion = client.messages.create(**call_params)
        return completion.content[0].text
