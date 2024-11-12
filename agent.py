import requests

def jina_agent(url):
    response = requests.get("https://r.jina.ai/" + url)
    return response

if __name__ == "__main__":
    url = input("Enter url")
    response = jina_agent(url)