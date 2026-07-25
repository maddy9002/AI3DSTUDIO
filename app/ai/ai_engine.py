import json
import ollama

from app.ai.prompts import SYSTEM_PROMPT


class AIEngine:

    def __init__(self):

        self.model = "llama3"

    def ask(self, prompt):

        response = ollama.chat(

            model=self.model,

            messages=[

                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ]

        )

        return json.loads(

            response["message"]["content"]

        )