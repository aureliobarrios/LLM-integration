import os
import json
import uuid
import gradio as gr
from groq import Groq
from googlesearch import search
from dotenv import load_dotenv

with gr.Blocks() as demo:    
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
    
    # ---------- Components ----------

    #build selection section
    radio = gr.Radio(
        ["General", "Tutorial", "Videos"],
        value="General",
        label="What kind of resources would you like to receive?"
    )
    #build chatbot interface

    message = """Hello, I am your chatbot assistant tasked with building a learning path for you!.
    \nPlease enter what you wish to learn below!
    """

    chatbot = gr.Chatbot(value=[
        {"role": "assistant", "content": message}
    ], type="messages")
    #build textbot for message input
    msg = gr.Textbox(placeholder="Insert question here")

    #build button row section
    with gr.Row():
        clear_button = gr.Button("Clear")
        submit_button = gr.Button("Build Path")

    #create output textbox
    output = gr.Textbox(label="Learning Path")

    # ---------- Functions ----------

    #function to receive user input
    def user(user_message, history):
        return "", history + [{"role": "user", "content": user_message}]
    
    #function to return bot output
    def bot(history, radio):
        #trial name to save test
        os.environ["TRIAL"] = uuid.uuid4().hex[:5]
        trial_name = os.environ["TRIAL"]
        #used to calculate query price
        INPUT_TOKENS = 0 #prompt tokens
        OUTPUT_TOKENS = 0 #completion tokens
        #load environment variables and build client
        load_dotenv()
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")

        client = Groq(
            api_key=GROQ_API_KEY
        )

        #get previous user message
        student_prompt = history[-1]["content"]
        #get user resource selection
        selection = radio
        # TODO : include implementation for radio resource selection
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
        lp_text_filename = f"./gradio-tests/{trial_name}.txt"

        with open(lp_text_filename, "w+") as file:
            file.write(learning_path_text)
        
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

        try:
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
        except Exception as e:
            print(e)


        #update tokens used
        INPUT_TOKENS = INPUT_TOKENS + response.usage.prompt_tokens
        OUTPUT_TOKENS = OUTPUT_TOKENS + response.usage.completion_tokens       

        if response.choices[0].message.tool_calls:
            #get the arguments of the content
            functio_args = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
            #run arguments to function
            out_json = extract_learning_info(**functio_args)
            #save the content of our response message
            content_filename = f"./gradio-tests/content_{trial_name}.txt"

            with open(content_filename, "w+") as file:
                file.write("Passed through function tool_calls")
        else:
            #get the content of our response
            content = response.choices[0].message.content
            
            #save the content of our response message
            content_filename = f"./gradio-tests/content_{trial_name}.txt"

            with open(content_filename, "w+") as file:
                file.write(content)

            # #get starting index of JSON object
            # start_index = content.find("{")
            # #get ending index of JSON object
            # end_index = len(content) - content[::-1].find("}")
            # #get the entire JSON text
            # json_text = content[start_index:end_index] 

            #get start index of JSON file
            start_index = min([i for i in [content.find("{"), content.find("[")] if i >= 0])
            #get end index of JSON file
            end_index = len(content) - min([i for i in [content[::-1].find("}"), content[::-1].find("]")] if i >= 0])
            #get the entire JSON text
            json_text = content[start_index:end_index]       

            try:
                #load text to json
                json_response = json.loads(json_text)
            except Exception as e:
                try:
                    #list of brackets in string
                    brackets = []
                    #mapping of closed brackets to open
                    bracket_map = {
                        "}": "{",
                        "]": "["
                    }
                    #inverse bracket map
                    inverse_map = {v: k for k, v in bracket_map.items()}
                    #save the character index
                    char_index = 0
                    #loop through every character in format string
                    for char in json_text:
                        if char == "}" or char == "]":
                            if brackets[-1] != bracket_map[char]:
                                #then we must add new bracket
                                while brackets[-1] != bracket_map[char]:
                                    #add new bracket and remove
                                    json_text = json_text[0:char_index] + inverse_map[brackets[-1]] + json_text[char_index:]
                                    brackets = brackets[:-1]
                                    # print(brackets)
                                brackets = brackets[:-1]
                            else:
                                #eliminate brackets
                                brackets = brackets[:-1]
                        elif char == "{" or char == "[":
                            brackets.append(char)
                        #increment index
                        char_index += 1

                    #handle edge case where last missing bracket is at the end
                    while brackets:
                        json_text = json_text + inverse_map[brackets[0]]
                        brackets = brackets[1:]
                    #load text to json
                    json_response = json.loads(json_text)
                except Exception as e:
                    print("Failure! Could not load your file to JSON with error", e)
                # ---------- Previous implementation ----------

                # if e.args[0].startswith("Expecting ',' delimiter:"):
                #     try:
                #         #load text to json
                #         json_response = json.loads(json_text[0:e.pos-1] + "}" + json_text[e.pos:])
                #     except Exception as e:
                #         try:
                #             if e.pos == len(json_text):
                #                 json_response = json.loads(json_text + "}")
                #             else:
                #                 print("Nothing happened!")
                #         except Exception as e:
                #             print("Failure!! Could not load your file to JSON with error", e)
                # else:
                #     print("Failure!!! Could not load your file to JSON with error", e)
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
            json_filename = f"./gradio-tests/queries_{trial_name}.json"

            with open(json_filename, "w+") as file:
                json.dump(out_json, file)

        #TODO: Summarize entire process
        summary_text = "This is an example summary text"
        #build out string to display to chatbot
        resource_message = f"{summary_text}\n"
        #gather resources from json
        for key in out_json:
            #build level text
            resource_message = resource_message + f"\n{key.capitalize()} Level\n\n"
            #build description text
            resource_message = resource_message + f"Goal: {out_json[key]['description']}\n"
            #build query text
            # resource_message = resource_message + f"\tResources:\n"
            #get search results
            search_results = search(out_json[key]["query"], advanced=True, num_results=5)
            #go through the results
            index = 1
            for result in search_results:
                resource_message = resource_message + f"{index}. {result.title} : {result.url}\n"
                index += 1

        #append learning path to chatbot
        history.append({"role": "assistant", "content": resource_message})
        #get the total request price
        price = get_request_price(INPUT_TOKENS, OUTPUT_TOKENS)
        #append query price to chatbot
        price_message = f"Process Completed Succesfully! Total Estimated Price: ${price}"
        history.append({"role": "assistant", "content": price_message})
        #reset tokens for next iteration
        INPUT_TOKENS, OUTPUT_TOKENS = 0, 0
        return history
    
    #function to return to output text
    def learning(history):
        return "Built learning path for: " + history[-1]["content"]
    
    def clear_handle(history):
        #clear chatbot history
        history = []
        #add initial chat prompt
        history.append({"role": "assistant", "content": message})
        return history
    
    #functions to display file saving information
    def learning_path_info():
        trial_name = os.environ["TRIAL"]
        display_message = f"Learning Path Context Saved To: ./gradio-tests/{trial_name}.txt"
        gr.Info(display_message, duration=5)

    def extracted_content_info():
        trial_name = os.environ["TRIAL"]
        display_message = f"Extracted Content Saved To: ./gradio-tests/content_{trial_name}.txt"
        gr.Info(display_message, duration=5)

    def query_info():
        trial_name = os.environ["TRIAL"]
        display_message = f"Query Information Saved To: ./gradio-tests/queries_{trial_name}.txt"
        gr.Info(display_message, duration=5)
    
    # ---------- Actions ----------

    #handle user submit
    msg.submit(
        user, [msg, chatbot], [msg, chatbot], queue=False
    ).then(
        bot, [chatbot, radio], chatbot
    ).then(
        learning_path_info, None, None
    ).then(
        extracted_content_info, None, None
    ).then(
        query_info, None, None
    )

    #handle user click on clear button
    clear_button.click(
        clear_handle, chatbot, chatbot, queue=False
    ).then(
        lambda: None, None, output
    )

    #handle user click on submit button
    submit_button.click(
        user, [msg, chatbot], [msg, chatbot], queue=False
    ).then(
        bot, [chatbot, radio], chatbot
    ).then(
        learning, chatbot, output
    ).then(
        learning_path_info, None, None
    ).then(
        extracted_content_info, None, None
    ).then(
        query_info, None, None
    )

if __name__ == "__main__":
    demo.launch(show_error=True)