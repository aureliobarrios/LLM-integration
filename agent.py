import requests
import tiktoken

def count_tokens(prompt):
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(prompt)
    return len(tokens)

def jina_agent(url):
    response = requests.get("https://r.jina.ai/" + url)
    return response

if __name__ == "__main__":
    url = input("Enter url")
    response = jina_agent(url)