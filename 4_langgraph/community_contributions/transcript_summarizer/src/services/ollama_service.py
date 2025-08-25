import requests
import json
from typing import Dict, Any, Optional, List
import asyncio
import aiohttp
from dataclasses import dataclass
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class OllamaResponse:
    """Response from Ollama API."""
    content: str
    model: str
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None

class OllamaService:
    """Service for interacting with Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b", timeout: int = 500):
        """
        Initialize Ollama service.
        
        Args:
            base_url: Base URL for Ollama API
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def test_connection(self) -> bool:
        """
        Test connection to Ollama server.
        
        Returns:
            True if connection successful, False otherwise
        """
        url = f"{self.base_url}/api/tags"
        logger.info(f"Attempting to test connection to Ollama at {url}")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                logger.info("Successfully connected to Ollama.")
                return True
            else:
                logger.warning(f"Failed to connect to Ollama. Status code: {response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Error testing connection to Ollama: {e}")
            return False
    
    def check_model_availability(self) -> bool:
        """
        Check if the specified model is available.
        Returns:
            True if model is available, False otherwise
        """
        url = f"{self.base_url}/api/tags"
        logger.info(f"Checking availability of model '{self.model}' at {url}")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if any(model['name'].startswith(self.model) for model in models):
                    logger.info(f"Model '{self.model}' is available.")
                    return True
                else:
                    logger.warning(f"Model '{self.model}' not found in Ollama models.")
            return False
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False

    def generate_sync(self, prompt: str, temperature: float = 0.3, system_prompt: Optional[str] = None) -> OllamaResponse:
        """
        Generate text synchronously using Ollama.

        Args:
            prompt: Input prompt
            temperature: Temperature for generation
            system_prompt: Optional system prompt

        Returns:
            OllamaResponse object
        """
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": -1  # Generate until natural stopping point
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        logger.info(f"Sending synchronous generation request to {url} for model '{self.model}'")
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Synchronous generation successful for model '{self.model}'.")
            return OllamaResponse(
                content=result.get("response", ""),
                model=result.get("model", self.model),
                total_duration=result.get("total_duration"),
                load_duration=result.get("load_duration"),
                prompt_eval_count=result.get("prompt_eval_count"),
                eval_count=result.get("eval_count")
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with Ollama during synchronous generation: {str(e)}")
            raise Exception(f"Error communicating with Ollama: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Ollama response during synchronous generation: {str(e)}")
            raise Exception(f"Error parsing Ollama response: {str(e)}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during synchronous generation: {str(e)}")
            raise Exception(f"Error communicating with Ollama: {str(e)}")

    async def generate_async(self, prompt: str, temperature: float = 0.3, system_prompt: Optional[str] = None) -> OllamaResponse:
        """
        Generate text asynchronously using Ollama.

        Args:
            prompt: Input prompt
            temperature: Temperature for generation
            system_prompt: Optional system prompt

        Returns:
            OllamaResponse object
        """
        if not self.session:
            logger.error("Aiohttp session not initialized for asynchronous generation.")
            raise Exception("Session not initialized. Use async context manager.")

        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": -1
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        logger.info(f"Sending asynchronous generation request to {url} for model '{self.model}'")
        try:
            async with self.session.post(url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()

                logger.info(f"Asynchronous generation successful for model '{self.model}'.")
                return OllamaResponse(
                    content=result.get("response", ""),
                    model=result.get("model", self.model),
                    total_duration=result.get("total_duration"),
                    load_duration=result.get("load_duration"),
                    prompt_eval_count=result.get("prompt_eval_count"),
                    eval_count=result.get("eval_count")
                )

        except aiohttp.ClientError as e:
            logger.error(f"Aiohttp client error during asynchronous generation: {e}")
            raise Exception(f"Error communicating with Ollama: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Ollama response during asynchronous generation: {e}")
            raise Exception(f"Error parsing Ollama response: {str(e)}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during asynchronous generation: {e}")
            raise Exception(f"Error : {str(e)}")

    async def generate_multiple_async(self, prompts: List[str], temperature: float = 0.3, system_prompt: Optional[str] = None) -> List[OllamaResponse]:
        """
        Generate text for multiple prompts concurrently.

        Args:
            prompts: List of input prompts
            temperature: Temperature for generation
            system_prompt: Optional system prompt

        Returns:
            List of OllamaResponse objects
        """
        if not self.session:
            logger.error("Aiohttp session not initialized for multiple asynchronous generations.")
            raise Exception("Session not initialized. Use async context manager.")

        logger.info(f"Sending {len(prompts)} concurrent asynchronous generation requests for model '{self.model}'")
        tasks = [
            self.generate_async(prompt, temperature, system_prompt)
            for prompt in prompts
        ]

        try:
            results = await asyncio.gather(*tasks)
            logger.info(f"Successfully completed {len(results)} concurrent asynchronous generations.")
            return results
        except Exception as e:
            logger.error(f"An error occurred during concurrent asynchronous generation: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Model information dictionary
        """
        url = f"{self.base_url}/api/show"
        logger.info(f"Requesting model info for '{self.model}' from {url}")
        try:
            response = requests.post(
                url,
                json={"name": self.model},
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Successfully retrieved model info for '{self.model}'.")
            return response.json()
        except Exception as e:
            logger.error(f"Could not get model info for '{self.model}': {e}")
            return {"error": f"Could not get model info: {str(e)}"}

    def pull_model(self) -> bool:
        """
        Pull the model if it's not available locally.

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/api/pull"
        logger.info(f"Attempting to pull model '{self.model}' from {url}")
        try:
            response = requests.post(
                url,
                json={"name": self.model},
                timeout=600  # Model pulling can take a while
            )
            if response.status_code == 200:
                logger.info(f"Successfully initiated pull for model '{self.model}'.")
                return True
            else:
                logger.warning(f"Failed to pull model '{self.model}'. Status code: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error pulling model '{self.model}': {e}")
            return False

