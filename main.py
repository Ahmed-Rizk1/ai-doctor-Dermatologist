import base64
import requests
import io
from PIL import Image
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ API KEY is not set in the .env file")

def process_image(image_path, query):
    try:
        # افتح الصورة وقلل حجمها
        img = Image.open(image_path)
        img = img.resize((512, 512))
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # للـ vision models
        vision_messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}"}}
                ]
            }
        ]

        # للـ text-only models
        text_messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        def make_api_request(model, messages):
            response = requests.post(
                GROQ_API_URL,
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 1000
                },
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            return response

        # vision model
        model1 = make_api_request("meta-llama/llama-guard-4-12b", vision_messages)
        # text-only model
        model2 = make_api_request("llama-3.3-70b-versatile", text_messages)

        responses = {}
        for model, response in [("model1", model1), ("model2", model2)]:
            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"]
                logger.info(f"Processed response from {model} API : {answer}")
                responses[model] = answer
            else:
                logger.error(f"Error from {model} API : {response.status_code} - {response.text}")
                responses[model] = f"Error from {model} API : {response.status_code}"

        return responses

    except Exception as e:
        logger.error(f"An unexpected error occurred : {str(e)}")
        return {"error": f"An unexpected error occurred : {str(e)}"}



if __name__ == "__main__":
    image_path = "test1.png"
    query = "what are the encoders in this picture?"
    result = process_image(image_path, query)
    print(result)
