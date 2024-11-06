import os
import re
import uuid
import json
from groq import Groq
from googlesearch import search
from langchain.prompts import ChatPromptTemplate

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

PROMPT_TEMPLATE = """
You are tasked to answer the question given by a student on a certain topic they have. 

Before you answer the question I need you to break down the topic into 5 essential steps
needed to answer that question. 

For each of these steps I need you to search the web for resources that will help guide the
student to answer his initial question on his own. Make sure to build a one sentence query
that the student can input into a search engine that will lead him to the resources needed
to solve the current step.

I need you to keep in mind that the student asking this questions believes their level of expertise
is as follows: {expertise}. Also keep in mind that this student aims for a career in: {career}

Your output should be in json format following very strictly this example provided: {format}

Following the information I have given you, answer the students question: {question}
"""

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

def build_prompt(prompt_info):
    """Function that builds the prompt template that will be used for the GPT"""
    #build initial template
    template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    #build the prompt from template
    prompt = template.format(expertise=prompt_info["difficulty"],
                             career=prompt_info["learning_path"],
                             format=prompt_info["output_format"],
                             question=prompt_info["prompt"])
    return prompt

def gather_resources(filename):
    """Function that will be used to search the web for resources"""
    #read the file into a string
    with open(filename, 'r') as file:
        output = file.read().replace("\n", "")
    #use regex to get queries
    queries = re.findall(r"{(.*?)}", output)
    #save queries in a dictionary
    query_dic = {
        "query": [],
        "description": []
    }
    #get the query from each step
    for line in queries[:5]:
        #break down the line into query components
        line_breakdown = re.findall(r'"(.*?)"', line)
        #input query into dictionary
        query_dic["query"].append(line_breakdown[1])
        #input description into dictionary
        query_dic["description"].append(line_breakdown[3])
    #dictionary to store our web search results
    web_search = {}
    #query the web
    step_index = 0
    for search_query in query_dic["query"]:
        #get the results of the search query
        results = search(search_query, advanced=True, num_results=5)
        #save current step
        web_search["step_" + str(step_index+1)] = {
            "query": search_query,
            "description": query_dic["description"][step_index],
            "results": {}
        }
        #save results
        result_index = 1
        for search_result in results:
            #store web search results into the dictionary to return
            web_search["step_" + str(step_index+1)]["results"]["search_" + str(result_index)] = {
                "title": search_result.title,
                "url": search_result.url,
                "description": search_result.description
            }
            result_index += 1
        step_index += 1
    return web_search

if __name__ == "__main__":
    #if we are testing using student input or using pre existing test
    student_input = True
    filename = ""
    if student_input:
        #brief questionnare for the student
        question = input("What is your question today? ")
        # print("Question:", question)
        expertise = input("What would you say your level of expertise on the subject is? ")
        # print("Expertise:", expertise)
        track = input("By solving this question what career would you say we are getting you closer to? ")
        # print("Track:", track)
        prompt_info = {
            "prompt": question,
            "difficulty": expertise,
            "learning_path": track,
            "output_format": {
                "step number": "A one sentence query the student can input into a search engine that will lead him to useful resources for the current step.",
                "description": "provide a description of what the search query is solving for"
            }
        }
        #build our prompt
        prompt = build_prompt(prompt_info)
        #get a response from groq
        response = invoke_groq(prompt)
        #write our response to a file
        unique_id = uuid.uuid4().hex
        filename = f"output/output_{unique_id[:5]}.txt"
        with open(filename, 'w') as f:
            f.write(response)
    #get search results for a test file
    if filename:
        #gather resources into dictionary
        resources = gather_resources(filename)
    else:
        filename = input("Enter the filename: ")
        resources = gather_resources(filename)
    #write out resources onto file
    out_filename = "output/results_" + str(filename[::-1][4:9][::-1]) + ".json"
    with open(out_filename, "w") as outfile:
        json.dump(resources, outfile)