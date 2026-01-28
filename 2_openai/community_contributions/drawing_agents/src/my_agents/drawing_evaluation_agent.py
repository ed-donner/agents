
from agents import Agent, Runner, ModelSettings
from openai.types.responses import ResponseInputTextParam, ResponseInputImageParam
from openai.types.responses.response_input_item_param import Message

from utils.image_utils import encode_image_base64

drawing_evaluation_agent = Agent(
    name="Drawing Evaluation Agent",
    model="gpt-4o",
    instructions="""
    You are an evaluator for kid drawings. You will be given the original drawing request, and also the image. 
    You will output a textual evaluation of the image, and also points for improvement
    """,
)

async def run_evaluation_agent(text: str, image_path: str):
    base64_img = encode_image_base64(image_path)
    return await Runner.run(
        drawing_evaluation_agent,
        input=[
            Message(
                role="user",
                content=[
                    ResponseInputTextParam(
                        type="input_text",
                        text=text,
                    ),
                    ResponseInputImageParam(
                        type="input_image",
                        image_url=f"data:image/jpeg;base64,{base64_img}",
                        detail="low",
                    ),
                ],
            )
        ],
    )
