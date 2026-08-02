import os
import requests
import uuid
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from openai import OpenAI

class ImageGenerationInput(BaseModel):
    """Input schema for ImageGenerationInput."""
    prompt : str = Field(..., description="A detailed prompt describing the image to be generated.")

class ImageGenerationTool(BaseTool):
    name: str = "Generate Campaign Image"
    description: str = "Generates an image using DALL-E 3 based on a highly detailed prompt and saves it to disk. Returns the saved file path."

    args_schema: Type[BaseModel] = ImageGenerationInput

    def _run(self, prompt: str) -> str:
        print(f"\n🎨 [Graphic Designer Tool] Generating image for prompt: {prompt[:50]}...")
        try:
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            
            # Save the image locally
            filename = f"output/bill_pay_ad_{uuid.uuid4().hex[:6]}.png"
            img_data = requests.get(image_url).content
            with open(filename, 'wb') as handler:
                handler.write(img_data)
                
            return f"SUCCESS: Image generated and saved locally as '{filename}'"
        except Exception as e:
            return f"ERROR: Failed to generate image. Details: {str(e)}"