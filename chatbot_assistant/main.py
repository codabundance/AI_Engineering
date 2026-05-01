from ast import arguments
import base64
from cProfile import label
from io import BytesIO
from json import load
import json
from logging import info
from multiprocessing import context
import os
from turtle import mode
from dotenv import load_dotenv
from httpx import stream
from openai import OpenAI
import sys
from PIL import Image as PILImage
from urllib3 import response
import gradio as gr
import sqlite3

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

class AirlineAssistant:
    def __init__(self) -> None:
        load_dotenv(override=True)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.openai = OpenAI() #connects by default, no base url or api key needed
        self.google = OpenAI(api_key=self.google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
        self.system_prompt = f"""You are a lovely and helpful Flight Assistant called Flight AI. 
        answer very precisely and with minimum explanation but be courteous.
        Be accurate. If you don't know the answer, say so.
        """
        self.price_function = {
            "name": "get_ticket_price",
            "description": "Get the flight ticket price for a destination city", #Important: LLM uses this to decide if it needs to call this tool
            "parameters": {
                "type": "object",
                "properties": {
                    "destination_city": {
                        "type": "string",
                        "description" : "The city that the customer wants to travel to"
                    }
                },
                "required": ["destination_city"], #there can be multiple required fields hence an array
                "additionalProperties": False
            }
        }
        #basically, all you need to do is create JSON of below format and pass it to tools properties in API
        self.tools_json = [{"type": "function", "function": self.price_function}] # there can be multiple tools, so an array and a separate specification
        
        self.DB = "prices.db"
        # with sqlite3.connect(self.DB) as conn:
        #     cursor = conn.cursor()
        #     cursor.execute('CREATE TABLE IF NOT EXISTS ticket_prices (city TEXT PRIMARY KEY, price REAL)')
        #     cursor.execute("INSERT INTO ticket_prices (city, price) VALUES ('london', 200)")
        #     cursor.execute("INSERT INTO ticket_prices (city, price) VALUES ('paris', 100)")
        #     cursor.execute("INSERT INTO ticket_prices (city, price) VALUES ('bangalore', 10)")
        #     cursor.execute("INSERT INTO ticket_prices (city, price) VALUES ('patna', 20)")
        #     conn.commit()

    def handle_tool_call(self, message_from_llm):
        # LLM returns an array of tool calls because there can be many
        # we try to parse the same json that we sent, LLM passes the same to us
        tools_responses = []
        for tool in message_from_llm.tool_calls:
            if tool.function.name == "get_ticket_price": # same name as defined in json that we sent to LLM
                arguments = json.loads(tool.function.arguments)
                city = arguments.get("destination_city")
                price_details = self.get_price_from_db(city)
                #form the correct tool response. See "role" : "tool"
                tools_responses.append({
                    "role" : "tool",
                    "content" : price_details,
                    "tool_call_id": tool.id
                })
                #tools_responses.append(tool_response)
        return tools_responses
    
    def handle_tool_calls_and_return_cities(self, message):
        responses = []
        cities = []
        for tool_call in message.tool_calls:
            if tool_call.function.name == "get_ticket_price":
                arguments = json.loads(tool_call.function.arguments)
                city = arguments.get('destination_city')
                cities.append(city)
                price_details = self.get_price_from_db(city)
                responses.append({
                "role": "tool",
                "content": price_details,
                "tool_call_id": tool_call.id
                })
        return responses, cities

    def chat_with_tools(self, message, history):
        history = [{"role": h["role"], "content": h["content"]} for h in history]
        messages = [{"role": "system", "content": self.system_prompt}] + history + [{"role": "user", "content": message}]
        response = self.openai.chat.completions.create(model="gpt-4.1-mini", messages=messages, tools=self.tools_json) # call LLM with tools available

        while(response.choices[0].finish_reason == "tool_calls"):
            message = response.choices[0].message
            response = self.handle_tool_call(message)
            messages.append(message) #add history
            messages.extend(response) #add tool call content
            print(messages)
            response = self.openai.chat.completions.create(model="gpt-4.1-mini", messages=messages, tools=self.tools_json) #call LLM again with entire data and tools available

        return response.choices[0].message.content

    def chat_with_audio_image(self,history):
        history = [{"role":h["role"], "content":h["content"]} for h in history]
        messages = [{"role": "system", "content": self.system_prompt}] + history
        response = self.openai.chat.completions.create(model="gpt-4.1-mini", messages=messages, tools=self.tools_json)
        cities = []
        image = None
        while response.choices[0].finish_reason=="tool_calls":
            message = response.choices[0].message
            responses, cities = self.handle_tool_calls_and_return_cities(message)
            messages.append(message)
            messages.extend(responses)
            response = self.openai.chat.completions.create(model="gpt-4.1-mini", messages=messages, tools=self.tools_json)
        
        reply = response.choices[0].message.content
        history += [{"role":"assistant", "content":reply}]
        voice = self.generate_audio(reply)
        if cities:
            image = self.generate_image(cities[0])
    
        return history, voice, image
    
    def generate_image(self, city):
        response = self.openai.images.generate(
            model="dall-e-3",
            prompt=f"An image representing a vacation in {city}, showing tourist spots and everything unique about {city}, in a vibrant pop-art style",
            size="1024x1024",
            n=1,
            response_format="b64_json",
        )
        image_base64 = response.data[0].b64_json
        image_data = base64.b64decode(image_base64)
        return PILImage.open(BytesIO(image_data))

    def generate_audio(self, message):
        response = self.openai.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="coral",    # Also, try replacing onyx with alloy or coral
        input=message
        )
        return response.content
    
    def get_price(self, destination):
        ticket_prices = {"london":"$200","paris":"$100","bangalore":"$10","patna":"$20"}
        return ticket_prices[destination.lower()]
    
    def get_price_from_db(self, destination):
        print(f"DATABASE TOOL CALLED: Getting ticket prices for {destination}", flush=True)
        conn = sqlite3.connect(self.DB)
        cursor = conn.cursor()
        cursor.execute("SELECT price FROM ticket_prices WHERE city = ?", (destination.lower(),))
        price = cursor.fetchone()
        conn.close()
        return f"Ticket price to {destination} is ${price[0]}" if price else "No price data available for this city"
    
    def chat_stream(self, message, history):
        history = [{"role": h["role"], "content": h["content"]} for h in history]
        messages = [{"role": "system", "content": self.system_prompt}] + history + [{"role": "user", "content": message}]
        stream = self.openai.chat.completions.create(model="gpt-4.1-mini", messages=messages, stream=True)
        result = ""
        for chunks in stream:
            result += chunks.choices[0].delta.content or ""
            yield result 
    
    # show messages in chatbot to user before sending to generate audio and image
    def put_message_in_chatbot(self, message, history):
        return "", history + [{"role":"user", "content":message}]

def main() -> int:
    #app = ChatbotAssistant()
    app = AirlineAssistant()
    # type="messages" was old in older versions of gradio to support OpenAI chat completion type, but with new version it is default
    
    # UI definition

    with gr.Blocks() as ui:
        with gr.Row():
            chatbot = gr.Chatbot(height=500)
            image_output = gr.Image(height=500, interactive=False)
        with gr.Row():
            audio_output = gr.Audio(autoplay=True)
        with gr.Row():
            message = gr.Textbox(label="Chat with our AI Assistant:")

# Hooking up events to callbacks

        message.submit(app.put_message_in_chatbot, inputs=[message, chatbot], outputs=[message, chatbot]).then(
        app.chat_with_audio_image, inputs=chatbot, outputs=[chatbot, audio_output, image_output]
        )

    ui.launch(inbrowser=True, auth=("saurabh", "saurabh123"))
    # gr.ChatInterface(
    #     fn=app.chat_with_tools
    # ).launch()

if __name__ == "__main__":
    sys.exit(main())