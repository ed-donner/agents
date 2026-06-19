from pathlib import Path
import base64
import openai
import os
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class IllustratorToolInput(BaseModel):
    prompt: str = Field(..., description="Text prompt for image generation.")

class IllustratorTool(BaseTool):
    name: str = "GPT-4o Image Generator"
    description: str = "Generates an image using GPT-4o (DALL·E 3) based on a text prompt."
    args_schema: Type[BaseModel] = IllustratorToolInput

    def _run(self, prompt: str, filename: str, size: str = "1024x1024") -> str:
        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.images.generate(
                model="gpt-image-1", 
                prompt=prompt,
                size=size,
                n=1,
            )
            image_data = response.data[0].b64_json
            # Ensure parent directory exists
            out_path = Path(filename)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, 'wb') as f:
                f.write(base64.b64decode(image_data))
            return f"Image generated and saved to {filename}."
        except Exception as e:
            return f"Failed to generate image: {e}"
