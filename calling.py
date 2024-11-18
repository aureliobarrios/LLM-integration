import os
import json
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

prompt = "When is the next flight from Amsterdam to New York?"

client = Groq(
    api_key=GROQ_API_KEY
)

#include the function
def get_flight_info(loc_origin, loc_destination):
    #get the flight information between two locations
    flight_info = {
        "loc_origin": loc_origin,
        "loc_destination": loc_destination,
        "datetime": str(datetime.now()),
        "airline": "KLM",
        "flight": "KL643"
    }
    return json.dumps(flight_info)

#creating a tool list for our LLM
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_flight_info",
            "description": "Get flight information between two locations",
            "parameters": {
                "type": "object",
                "properties": {
                    "loc_origin": {
                        "type": "string",
                        "description": "The departure airport, e.g. DUS"
                    },
                    "loc_destination": {
                        "type": "string",
                        "description": "The destination airport, e.g. HAM"
                    }
                },
                "required": ["loc_origin", "loc_destination"]
            }
        }
    }
]

#run the conversation
messages = [
    {
        "role": "user",
        "content": prompt
    }
]

response = client.chat.completions.create(
    messages=messages,
    model = "llama3-8b-8192",
    tools = tools,
    tool_choice = "auto",
)

response_message = response.choices[0].message
tool_calls = response_message.tool_calls

if tool_calls:
    available_functions = {
        "get_flight_info": get_flight_info
    }
    messages.append(response_message)

    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_to_call = available_functions[function_name]
        function_args = json.loads(tool_call.function.arguments)
        function_response = function_to_call(**function_args)

        messages.append({
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": function_name,
            "content": function_response
        })
    
    second_response = client.chat.completions.create(
        model = "llama3-8b-8192",
        messages=messages
    )
    final_response = second_response.choices[0].message.content
else:
    final_response = "Sorry didnt work"

print(final_response)