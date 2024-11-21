import requests
import tiktoken

def count_tokens(prompt):
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(prompt)
    return len(tokens)

def jina_agent(url):
    response = requests.get("https://r.jina.ai/" + url)
    return response

trial_name = input("Trial Name: ")

filename = f"./trials/{trial_name}.txt"

with open(filename, "w+") as file:
    file.write("Hello World")