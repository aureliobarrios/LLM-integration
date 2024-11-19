import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(
    api_key=GROQ_API_KEY
)

student_1_description = "David Nguyen is a sophomore majoring in computer science at Stanford University. He is Asian American and has a 3.8 GPA. David is known for his programming skills and is an active member of the university's Robotics Club. He hopes to pursue a career in artificial intelligence after graduating."
student_2_description="Ravi Patel is a sophomore majoring in computer science at the University of Michigan. He is South Asian Indian American and has a 3.7 GPA. Ravi is an active member of the university's Chess Club and the South Asian Student Association. He hopes to pursue a career in software engineering after graduating."

prompt1 = f'''
Please extract the following information from the given text and return it as a JSON object:

name
major
school
grades
club

This is the body of text to extract the information from:
'''

def extract_student_info(name, major, school, grades, club):
    
    """Get the student information"""
    print("Function was called")

    return f"{name} is majoring in {major} at {school}. He has {grades} GPA and he is an active member of the university's {club}."

tools  = [
    {
        "type": "function",
        "function": {
            "name": "extract_student_info",
            "description": "Get the student information from the body of the input text",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the person"
                    },
                    "major": {
                        "type": "string",
                        "description": "Major subject"
                    },
                    "school": {
                        "type": "string",
                        "description": "The university name"
                    },
                    "grades": {
                        "type": "integer",
                        "description": "GPA of the student"
                    },
                    "club": {
                        "type": "string",
                        "description": "School club for extracurricular activities"
                    }
                },
                "required": ["name", "major", "school", "grades", "club"]
            }
        }
    }
]

student_description = [student_1_description,student_2_description]
for i in student_description:
    response = client.chat.completions.create(
        model = "llama3-8b-8192",
        messages = [
            {
                "role": "user",
                "content": prompt1
            },
            {
                'role': 'user', 
                'content': i
            }
        ],
        tools = tools,
        tool_choice = 'auto'
    )

    # Loading the response as a JSON object
    # json_response = json.loads(response.choices[0].message.function_call.arguments)
    json_response = json.loads(response.choices[0].message.content)
    print(json_response)