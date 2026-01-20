"""
Configuration for AI Visual Art Studio
Set up your OpenAI API keys and model preferences here
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Art Studio"""
    
    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Model Configuration
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_MODEL_TURBO = os.getenv("OPENAI_MODEL_TURBO", "gpt-4o-mini")
    
    # Model Parameters
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
    
    # DALL-E Configuration
    DALLE_MODEL = os.getenv("DALLE_MODEL", "dall-e-3")
    
    # Optional: Azure OpenAI
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present"""
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is required. Please set it in your .env file or environment variables.\n"
                "Example .env file:\n"
                "OPENAI_API_KEY=your_openai_api_key_here\n"
                "OPENAI_MODEL=gpt-4\n"
                "OPENAI_TEMPERATURE=0.7"
            )
        return True
    
    @classmethod
    def get_model_config(cls, agent_type: str = "default"):
        """Get model configuration for specific agent types"""
        configs = {
            "concept_artist": {
                "model": cls.OPENAI_MODEL,
                "temperature": 0.8,  # More creative
                "max_tokens": 1500
            },
            "sketch_artist": {
                "model": cls.OPENAI_MODEL,
                "temperature": 0.7,  # Balanced creativity
                "max_tokens": 1200
            },
            "refinement_artist": {
                "model": cls.OPENAI_MODEL,
                "temperature": 0.6,  # More focused
                "max_tokens": 1000
            },
            "curator": {
                "model": cls.OPENAI_MODEL,
                "temperature": 0.5,  # More analytical
                "max_tokens": 1000
            },
            "default": {
                "model": cls.OPENAI_MODEL,
                "temperature": cls.OPENAI_TEMPERATURE,
                "max_tokens": cls.OPENAI_MAX_TOKENS
            }
        }
        
        return configs.get(agent_type, configs["default"])
