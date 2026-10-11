from groq import Groq

from app.core.config import GROQ_API_KEY


class ResponseGenerator:

    def __init__(self, api_key: str):

        self.client = Groq(
            api_key=api_key
        )

    def generate(self, prompt: str):

        response = self.client.chat.completions.create(

            model="openai/gpt-oss-120b",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content