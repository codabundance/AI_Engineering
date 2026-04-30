from cProfile import label
from json import load
from logging import info
from multiprocessing import context
import os
from turtle import mode
from dotenv import load_dotenv
from httpx import stream
from openai import OpenAI
import sys
from urllib3 import response
import gradio as gr

class ChatbotAssistant:
    def __init__(self) -> None:
        load_dotenv(override=True)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.openai = OpenAI() #connects by default, no base url or api key needed
        self.google = OpenAI(api_key=self.google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
        self.system_prompt = f"""You are a lovely chat assistant, 
        answer very precisely and with minimum explanation"""

    def chat(self, message, history):
        history = [{"role": h["role"], "content": h["content"]} for h in history]
        sys_prompt = f"""You are a snarky chat assistant, 
        answer very precisely and with minimum explanation"""
        messages = [{"role": "system", "content": sys_prompt}] + history + [{"role": "user", "content": message}]
        response = self.openai.chat.completions.create(model="gpt-4.1-mini", messages=messages)
        return response.choices[0].message.content
    
    def chat_stream(self, message, history):
        history = [{"role": h["role"], "content": h["content"]} for h in history]
        messages = [{"role": "system", "content": self.system_prompt}] + history + [{"role": "user", "content": message}]
        stream = self.openai.chat.completions.create(model="gpt-4.1-mini", messages=messages, stream=True)
        result = ""
        for chunks in stream:
            result += chunks.choices[0].delta.content or ""
            yield result 

def main() -> int:
    app = ChatbotAssistant()
    # type="messages" was old in older versions of gradio to support OpenAI chat completion type, but with new version it is default
    gr.ChatInterface(
        fn=app.chat_stream
    ).launch()

if __name__ == "__main__":
    sys.exit(main())       