import os
import json
from groq import Groq
from googlesearch import search
from dotenv import load_dotenv

#load environment variables and build client
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(
    api_key=GROQ_API_KEY
)

#load in text from file
filename = "files/" + input("Insert learning path filename")

with open(filename, "r") as file:
    learning_path_text = file.read()

#build current prompt
prompt = f'''
Please extract the following information from the given text and return it as a JSON object:

beginner_description
beginner_query
intermediate_description
intermediate_query
hard_description
hard_query
advanced_description
advanced_query

This is the body of text to extract the information from:
{learning_path_text}
'''

#function we intend to use for function calling
def extract_learning_info(beginner_description, beginner_query, 
                          intermediate_description, intermediate_query, 
                          hard_description, hard_query,
                          advanced_description, advanced_query):
    learning_info = {
        "beginner": {
            "description": beginner_description,
            "query": beginner_query
        },
        "intermediate": {
            "description": intermediate_description,
            "query": intermediate_query
        },
        "hard": {
            "description": hard_description,
            "query": hard_query
        },
        "advanced": {
            "description": advanced_description,
            "query": advanced_query
        }
    }
    return json.dumps(learning_info)

#build tool configuration
tools  = [
    {
        "type": "function",
        "function": {
            "name": "extract_learning_info",
            "description": "Extract information from given text and return as JSON object",
            "parameters": {
                "type": "object",
                "properties": {
                    "beginner_description": {
                        "type": "string",
                        "description": "Description of what the student is learning in the beginner difficulty level"
                    },
                    "beginner_query": {
                        "type": "string",
                        "description": "The web query the student will use to gather resources for the beginner difficulty level"
                    },
                    "intermediate_description": {
                        "type": "string",
                        "description": "Description of what the student is learning in the intermediate difficulty level"
                    },
                    "intermediate_query": {
                        "type": "string",
                        "description": "The web query the student will use to gather resources for the intermediate difficulty level"
                    },
                    "hard_description": {
                        "type": "string",
                        "description": "Description of what the student is learning in the hard difficulty level"
                    },
                    "hard_query": {
                        "type": "string",
                        "description": "The web query the student will use to gather resources for the hard difficulty level"
                    },
                    "advanced_description": {
                        "type": "string",
                        "description": "Description of what the student is learning in the advanced difficulty level"
                    },
                    "advanced_query": {
                        "type": "string",
                        "description": "The web query the student will use to gather resources for the advanced difficulty level"
                    },
                },
                "required": [
                    "beginner_description", "beginner_query",
                    "intermediate_description", "intermediate_query",
                    "hard_description", "hard_query",
                    "advanced_description", "advanced_query"
                ]
            }
        }
    }
]

#call response
response = client.chat.completions.create(
    model = "llama3-8b-8192",
    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ],
    tools = tools,
    tool_choice = "auto"
)

#get response tokens usage
tokens = response.usage.total_tokens

#get the content of our response
content = response.choices[0].message.content

#save the content of our response message
content_filename = "trials/" + input("Name of file to save response content")

with open(content_filename, "w") as file:
    file.write(content)

#TODO: edge case where we dont have JSON content in text

#get starting index of JSON object
start_index = content.find("{")
#get ending index of JSON object
end_index = len(content) - content[::-1].find("}")
#get the entire JSON text
json_text = content[start_index:end_index]

try:
    #load text to json
    json_response = json.loads(json_text)
except Exception as e:
    if e.args[0].startswith("Expecting ',' delimiter:"):
        try:
            #load text to json
            json_response = json.loads(json_text[0:e.pos-1] + "}" + json_text[e.pos:])
        except Exception as e:
            print("Failure! Could not load your file to JSON with error", e)
    else:
        print("Failure!! Could not load your file to JSON with error", e)
try:
    #get the current keys of json file
    curr_keys = json_response.keys()
    if "tool_calls" in curr_keys:
        out_json = extract_learning_info(**json_response["tool_calls"][0]["parameters"])
        print(f"Success! Succesfully load JSON using tool_calls")
    elif "parameters" in curr_keys:
        out_json = extract_learning_info(**json_response["parameters"])
        print(f"Success! Succesfully load JSON using parameters")
    elif "hard_query" in curr_keys:
        out_json = extract_learning_info(**json_response)
        print(f"Success! Succesfully load JSON using arguments")
    else:
        print(f"Failure! Could not process JSON keys")
except Exception as e:
    print(f"Failure! Could not process JSON keys with error", e)

if out_json:
    json_filename = "trials/" + input("Name your output JSON filename")

    with open(json_filename, "w") as file:
        json.dump(out_json, file)