import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

prompt = input("What is your question?")

client = Groq(
    api_key=GROQ_API_KEY
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ],
    model = "llama3-8b-8192"
)

output = chat_completion.choices[0].message.content

print(output)