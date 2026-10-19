import json
from pathlib import Path
from datetime import datetime, timezone

import requests

class Agent:

    def __init__(self, name: str, instruction: str, memory: str, url: str, model: str, credits: int = 100):
        self.name = name
        self.instruction = instruction
        self.memory = memory
        self.url = url
        self.model = model
        self.credits = credits

    def call(self, message: str, num_predict: int):
        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": f"{self.instruction}\nYour current private credit balance is {self.credits}."
                    },
                    {
                        "role": "user", 
                        "content": f"<memory>{self.memory}</memory>\r\n{message}"
                    }
                ],
                "stream": False,
                "options": {
                    "num_predict": num_predict
                }
            },
        )

        answer = response.json()["message"]["content"]
        return answer

    def append_memory(self, new: str):
        self.memory += new

    def overwrite_memory(self, new: str):
        self.memory = new
