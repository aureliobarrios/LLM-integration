import os
from groq import Groq
from googlesearch import search

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def invoke_groq(prompt):
    """Function that is used to invoke GROQ API"""
    client = Groq(
        api_key = GROQ_API_KEY
    )
    chat_completion = client.chat.completions.create(
        messages = [
            {
                "role" : "user",
                "content": prompt
            }
        ],
        model = "llama3-8b-8192"
    )
    return chat_completion.choices[0].message.content


if __name__ == "__main__":
    print("yessir")