import os
import json
import logging
from typing import Dict, Any, Optional, List
import asyncio
import aiohttp
from dataclasses import dataclass
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class GeminiResponse:
    """Response from Gemini API."""
    content: str
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

class GeminiService:
    """Service for interacting with Google Gemini API."""
    
    def __init__(self, api_key: str, model: str = "gemini-pro", timeout: int = 300):
        """
        Initialize Gemini service.
        
        Args:
            api_key: Google Gemini API key
            model: Model name to use (e.g., "gemini-pro")
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model_name = model
        self.timeout = timeout
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        self.session = None # aiohttp session for async operations if needed for direct http calls

    async def __aenter__(self):
        """Async context manager entry."""
        # For google-generativeai, aiohttp.ClientSession might not be directly used
        # as the library handles its own async HTTP.
        # However, if we were to make direct HTTP calls, we'd initialize it here.
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def test_connection(self) -> bool:
        """
        Test connection to Gemini API by listing models.
        
        Returns:
            True if connection successful, False otherwise
        """
        logger.info("Attempting to test connection to Gemini API.")
        try:
            # Attempt to list models to verify API key and connectivity
            for m in genai.list_models():
                if self.model_name in m.name:
                    logger.info(f"Successfully connected to Gemini and found model '{self.model_name}'.")
                    return True
            logger.warning(f"Failed to find model '{self.model_name}' or connect to Gemini.")
            return False
        except Exception as e:
            logger.error(f"Error testing connection to Gemini: {e}")
            return False
    
    def check_model_availability(self) -> bool:
        """
        Check if the specified model is available.
        Returns:
            True if model is available, False otherwise
        """
        logger.info(f"Checking availability of model '{self.model_name}' for Gemini.")
        try:
            for m in genai.list_models():
                if self.model_name in m.name:
                    logger.info(f"Model '{self.model_name}' is available.")
                    return True
            logger.warning(f"Model '{self.model_name}' not found in available Gemini models.")
            return False
        except Exception as e:
            logger.error(f"Error checking Gemini model availability: {e}")
            return False

    def generate_sync(self, prompt: str, temperature: float = 0.3, system_prompt: Optional[str] = None) -> GeminiResponse:
        """
        Generate text synchronously using Gemini.

        Args:
            prompt: Input prompt
            temperature: Temperature for generation
            system_prompt: Optional system prompt (Gemini uses roles for this)

        Returns:
            GeminiResponse object
        """
        logger.info(f"Sending synchronous generation request to Gemini for model '{self.model_name}'")
        try:
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": 5000 # A reasonable default for summarization
            }
            
            contents = []
            if system_prompt:
                contents.append({"role": "user", "parts": [system_prompt]})
                contents.append({"role": "model", "parts": ["Okay, I understand."]}) # Acknowledge system prompt
            contents.append({"role": "user", "parts": [prompt]})

            response: GenerateContentResponse = self.model.generate_content(
                contents,
                generation_config=generation_config,
                request_options={"timeout": self.timeout}
            )
            
            response_text = ""
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    response_text += part.text
            
            prompt_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else None
            completion_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else None
            total_tokens = response.usage_metadata.total_token_count if response.usage_metadata else None

            logger.info(f"Synchronous generation successful for model '{self.model_name}'.")
            return GeminiResponse(
                content=response_text.strip(),
                model=self.model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )

        except Exception as e:
            logger.error(f"Error communicating with Gemini during synchronous generation: {str(e)}")
            raise Exception(f"Error communicating with Gemini: {str(e)}")

    async def generate_async(self, prompt: str, temperature: float = 0.3, system_prompt: Optional[str] = None) -> GeminiResponse:
        """
        Generate text asynchronously using Gemini.

        Args:
            prompt: Input prompt
            temperature: Temperature for generation
            system_prompt: Optional system prompt

        Returns:
            GeminiResponse object
        """
        logger.info(f"Sending asynchronous generation request to Gemini for model '{self.model_name}'")
        try:
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": 2048
            }
            
            contents = []
            if system_prompt:
                contents.append({"role": "user", "parts": [system_prompt]})
                contents.append({"role": "model", "parts": ["Okay, I understand."]})
            contents.append({"role": "user", "parts": [prompt]})

            response: GenerateContentResponse = await self.model.generate_content_async(
                contents,
                generation_config=generation_config,
                request_options={"timeout": self.timeout}
            )
            
            response_text = ""
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    response_text += part.text
            
            prompt_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else None
            completion_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else None
            total_tokens = response.usage_metadata.total_token_count if response.usage_metadata else None

            logger.info(f"Asynchronous generation successful for model '{self.model_name}'.")
            return GeminiResponse(
                content=response_text.strip(),
                model=self.model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )

        except Exception as e:
            logger.error(f"Error communicating with Gemini during asynchronous generation: {str(e)}")
            raise Exception(f"Error communicating with Gemini: {str(e)}")

    async def generate_multiple_async(self, prompts: List[str], temperature: float = 0.3, system_prompt: Optional[str] = None) -> List[GeminiResponse]:
        """
        Generate text for multiple prompts concurrently.

        Args:
            prompts: List of input prompts
            temperature: Temperature for generation
            system_prompt: Optional system prompt

        Returns:
            List of GeminiResponse objects
        """
        logger.info(f"Sending {len(prompts)} concurrent asynchronous generation requests for Gemini model '{self.model_name}'")
        
        tasks = []
        for prompt in prompts:
            contents = []
            if system_prompt:
                contents.append({"role": "user", "parts": [system_prompt]})
                contents.append({"role": "model", "parts": ["Okay, I understand."]})
            contents.append({"role": "user", "parts": [prompt]})
            
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": 2048
            }
            
            tasks.append(self.model.generate_content_async(
                contents,
                generation_config=generation_config,
                request_options={"timeout": self.timeout}
            ))

        try:
            responses: List[GenerateContentResponse] = await asyncio.gather(*tasks)
            
            results = []
            for response in responses:
                response_text = ""
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        response_text += part.text
                
                prompt_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else None
                completion_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else None
                total_tokens = response.usage_metadata.total_token_count if response.usage_metadata else None
                
                results.append(GeminiResponse(
                    content=response_text.strip(),
                    model=self.model_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens
                ))
            
            logger.info(f"Successfully completed {len(results)} concurrent asynchronous generations for Gemini.")
            return results
        except Exception as e:
            logger.error(f"An error occurred during concurrent asynchronous generation with Gemini: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Model information dictionary
        """
        logger.info(f"Requesting model info for '{self.model_name}' from Gemini.")
        try:
            for m in genai.list_models():
                if self.model_name in m.name:
                    logger.info(f"Successfully retrieved model info for '{self.model_name}'.")
                    return m.to_dict()
            logger.warning(f"Model '{self.model_name}' not found when getting info.")
            return {"error": f"Model '{self.model_name}' not found."}
        except Exception as e:
            logger.error(f"Could not get model info for '{self.model_name}': {e}")
            return {"error": f"Could not get model info: {str(e)}"}
