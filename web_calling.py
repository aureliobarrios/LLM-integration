import os
import json
from groq import Groq
from googlesearch import search
from dotenv import load_dotenv

# -------------------- Helper Functions --------------------

#function to calculate price
def get_request_price(input_tokens, output_tokens):
    #price per input token
    input_price = 2.5 / 1_000_000
    #price per output token
    output_price = 10 / 1_000_000
    return (input_price * input_tokens) + (output_price * output_tokens)

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
    return learning_info

# -------------------- Environment Variables --------------------

INPUT_TOKENS = 0 #prompt tokens
OUTPUT_TOKENS = 0 #completion tokens

#load environment variables and build client
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(
    api_key=GROQ_API_KEY
)

# -------------------- Process --------------------

trial_name = input("Insert current trial name: ")

# #load in text from file
# filename = f"trials/{trial_name}.txt"

# with open(filename, "r") as file:
#     learning_path_text = file.read()

#receive student prompt
student_prompt = input("What do you want to learn today? ")

#build prompt that will return context for learning path
context_prompt = f'''
{student_prompt}

Can you build me a learning path to solve this problem that follows these 
levels: beginner, intermediate, hard, advanced.

For each of these levels give me a one sentence query that I can input into
my search engine that will return resources that will help me solve my problem.

Make sure to also include a one sentence description of what the current
difficulty level is teaching me.
'''

#build context for learning path
chat_completion = client.chat.completions.create(
    messages = [
        {
            "role": "user",
            "content": context_prompt
        }
    ],
    model = "llama3-8b-8192"
)

#update tokens used
INPUT_TOKENS = INPUT_TOKENS + chat_completion.usage.prompt_tokens
OUTPUT_TOKENS = OUTPUT_TOKENS + chat_completion.usage.completion_tokens

#get learning path context
learning_path_text = chat_completion.choices[0].message.content

#save learning path text
lp_text_filename = f"./trials/{trial_name}.txt"

with open(lp_text_filename, "w+") as file:
    file.write(learning_path_text)
    print(f"Learning Path Context Saved To: {lp_text_filename}")

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

#update tokens used
INPUT_TOKENS = INPUT_TOKENS + response.usage.prompt_tokens
OUTPUT_TOKENS = OUTPUT_TOKENS + response.usage.completion_tokens

#get the content of our response
content = response.choices[0].message.content

#save the content of our response message
content_filename = f"./trials/content_{trial_name}.txt"

with open(content_filename, "w+") as file:
    file.write(content)
    print(f"Extracted Content Saved To: {content_filename}")

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
            try:
                if e.pos == len(json_text):
                    json_response = json.loads(json_text + "}")
                else:
                    print("Nothing happened!")
            except Exception as e:
                print("Failure!! Could not load your file to JSON with error", e)
    else:
        print("Failure!!! Could not load your file to JSON with error", e)
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
    elif "properties" in curr_keys:
        out_json = extract_learning_info(**json_response["properties"])
        print(f"Success! Succesfully load JSON using properties")
    else:
        for key in curr_keys:
            if "hard_query" in json_response[key].keys():
                print(f"Success! Succesfully load JSON using search")
                out_json = extract_learning_info(**json_response[key])
            else:
                out_json = None
                print(f"Failure! Could not process JSON keys")
except Exception as e:
    print(f"Failure! Could not process JSON keys with error", e)

if out_json:
    json_filename = f"./trials/queries_{trial_name}.json"

    with open(json_filename, "w+") as file:
        json.dump(out_json, file)
        print(f"Query Information Saved To: {json_filename}")

price = get_request_price(INPUT_TOKENS, OUTPUT_TOKENS)

print(f"Process Completed Succesfully! Total Price: ${price}")