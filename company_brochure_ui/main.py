from cProfile import label
from json import load
from logging import info
from multiprocessing import context
import os
from turtle import mode
from dotenv import load_dotenv
from openai import OpenAI
import sys

from urllib3 import response
import gradio as gr

class CompanyBrochure:
    def __init__(self) -> None:
        load_dotenv(override=True)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.openai = OpenAI() #connects by default, no base url or api key needed
        self.google = OpenAI(api_key=self.google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")

    def run(self, prompt:str, model: str, stream:bool):
        system_prompt = "You are a very helpful assistant"
        if(model=="GPT"):
            if(stream):
                yield from self.stream_gpt(system_prompt, prompt)
            else:
                return self.message_gpt(system_prompt, prompt)
        elif(model=="GEMINI"):
            if(stream):
                yield from self.stream_gemini(system_prompt, prompt)
            else:
                return self.message_gemini(system_prompt, prompt)
        else:
            print("Unknown Model")

    def message_gpt(self, system_prompt: str, prompt:str) -> str:
        messages = [{"role":"system", "content":system_prompt },
                    {"role":"user", "content":prompt }]
        response = self.openai.chat.completions.create(model="gpt-4.1-mini", messages=messages)
        return response.choices[0].message.content

    def message_gemini(self, system_prompt: str, prompt:str) -> str:
        messages = [{"role":"system", "content":system_prompt },
                    {"role":"user", "content":prompt }]
        response = self.google.chat.completions.create(model="gemini-2.5-flash", messages=messages)
        return response.choices[0].message.content
    
    def stream_gpt(self, system_prompt:str, prompt:str) -> str:
        messages = [{"role":"system", "content":system_prompt },
                    {"role":"user", "content":prompt }]
        stream = self.openai.chat.completions.create(model="gpt-4.1-mini", messages=messages, stream=True)
        result=""
        for chunk in stream:
            result += chunk.choices[0].delta.content or ""
            yield result
    
    def stream_gemini(self, system_prompt:str, prompt:str) -> str:
        messages = [{"role":"system", "content":system_prompt },
                    {"role":"user", "content":prompt }]
        stream = self.google.chat.completions.create(model="gemini-2.5-flash", messages=messages, stream=True)
        result=""
        for chunk in stream:
            result += chunk.choices[0].delta.content or ""
            yield result

def shout(text):
    print(f"Shout has been called: {text}")
    return text.upper()

def main() -> int:
    # Create a simple UI
    message_input = gr.Textbox(label="Your message:", info="Enter a message to send to GPT", lines=7)
    model_selector = gr.Dropdown(["GPT", "GEMINI"], label="Select Model", value="GPT")
    is_stream = gr.Checkbox(label="Enable streaming", value=True)
    message_output = gr.Markdown(label="Response:")
    app = CompanyBrochure()
    view = gr.Interface(
        fn=app.run,
        inputs=[message_input, model_selector, is_stream], 
        outputs=[message_output], 
        flagging_mode="never")
    view.launch(inbrowser=True)
    #app = CompanyBrochure()
    #return app.run()

if __name__ == "__main__":
    sys.exit(main())       