import os
import json
import uuid
import time
import gradio as gr
from groq import Groq
from youtube_search import YoutubeSearch
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

    #add build type component
    build_type = gr.Radio(
        ["Learning Path", "Tutorial"],
        label="What do you wish to build today?"
    )

    #add learning path topic textbox
    topic = gr.Textbox(visible=False)

    #add difficulty selection component
    difficulty = gr.Radio(visible=False)

    #build selection gradio
    radio = gr.Radio(visible=False)

    #build chatbot interface
    chatbot = gr.Chatbot(type="messages")

    #build message textbox for chatbot
    msg = gr.Textbox(visible=False)

    #build button row section
    with gr.Row():
        clear_button = gr.Button("Clear", interactive=False)
        submit_button = gr.Button("Build Path", interactive=False)

    # ---------- Functions ----------

    #function to receive user input
    def user(build_type, topic, msg, history):
        if build_type == "Learning Path":
            #build chatbot message
            message = f"Requested Learning Path For: {topic}"
            return "", history + [{"role": "user", "content": message}]
        else:
            return "", history + [{"role": "user", "content": msg}]
    
    #function to return bot output
    def bot(build_type, difficulty, radio, history):
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
        #handle input based on different selections
        if build_type == "Learning Path":
            #get the topic
            topic = student_prompt.split(":")[1].lower()
            #build student prompt
            student_prompt = f"I want to learn {topic}"
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

        #implement out_json edge case
        out_json = None
        #keep track of number of trials
        trial = 0
        #run process until we have an out_json or less than trials
        while out_json is None and trial < 2:
            print(f"Current Trial: {trial}")
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
                print("Success! Succesfully loaded using tool_calls")
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
                try:
                    #get the current keys of json file
                    curr_keys = json_response.keys()
                    if "tool_calls" in curr_keys:
                        if "parameters" in json_response["tool_calls"][0].keys():
                            out_json = extract_learning_info(**json_response["tool_calls"][0]["parameters"])
                        elif "function" in json_response["tool_calls"][0].keys():
                            out_json = extract_learning_info(**json_response["tool_calls"][0]["function"]["parameters"])
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
            trial += 1
        
        #handle extracted information
        if out_json:
            #build out file name
            json_filename = f"./gradio-tests/queries_{trial_name}.json"
            #save extracted information
            with open(json_filename, "w+") as file:
                json.dump(out_json, file)

            #handle summary based on build type
            if build_type == "Learning Path":
                #get the difficulty chosen
                selected_difficulty = difficulty.lower()
                #start building out summary prompt
                summary_prompt = f'''
                I would like you to respond like you are an instructor summarizing to a student. Please avoid drawn out responses, keep it concise and to the point.
                Summarize the topic that the student is learning in 3 sentences. Begin your response with: In your learning path you must learn ...

                Topic: {out_json[selected_difficulty]["description"]}
                '''
                #get the index of current level
                difficulty_index = list(out_json.keys()).index(selected_difficulty)
                #get the previous levels empty list if beginner level
                prev_levels = list(out_json.keys())[:difficulty_index]
                #loop through previous levels
                if prev_levels:
                    #add assumptions prompt
                    summary_prompt = summary_prompt + "\nAlso add a couple of sentences summarizing each of the assumptions mentioned below that the student should already know. Begin this portion of the response with: This learning path assumes you know ...\n"
                    #loop through previous level
                    for level in prev_levels:
                        #add assumption prompt for previous level
                        summary_prompt = summary_prompt + f"\nAssuming the student has already learned: {out_json[level]["description"]}"    
            else:
                #prompt to summarize entire process
                summary_prompt = f'''
                I would like you to respond like you are an instructor summarizing to a student. Please avoid drawn out responses, keep it concise and to the point.
                Summarize what the student is learning in 4 sentences. Begin your response with: In your learning path you must learn ...

                {learning_path_text}
                '''

            #get summary response from chatbot
            summary_response = client.chat.completions.create(
                messages = [
                    {
                        "role": "user",
                        "content": summary_prompt
                    }
                ],
                model = "llama3-8b-8192"
            )
            #update tokens used and price 
            INPUT_TOKENS = INPUT_TOKENS + summary_response.usage.prompt_tokens
            OUTPUT_TOKENS = OUTPUT_TOKENS + summary_response.usage.completion_tokens

            #get the summary text
            summary_text = summary_response.choices[0].message.content
            #build out string to display to chatbot
            resource_message = f"{summary_text}\n"
            #build output message based on build
            if build_type == "Learning Path":
                #get the selected difficulty
                selected_difficulty = difficulty.lower()
                #get student input
                student_input = history[-1]["content"]
                #get the topic
                topic = student_input.split(":")[1].lower()
                #build level text
                resource_message = resource_message + f"\n{selected_difficulty.capitalize()} Learning Path\n\n"
                #build description text
                resource_message = resource_message + f"Goal: {out_json[selected_difficulty]['description']}\n"
                #build query text
                if radio == "Videos":
                    #get search results
                    search_results = json.loads(YoutubeSearch(out_json[selected_difficulty]["query"], max_results=10).to_json())
                    #go through the results
                    index = 1
                    for result in search_results["videos"]:
                        resource_message = resource_message + f"{index}. {result['title']} : https://www.youtube.com{result['url_suffix']}\n"
                else:
                    #get search results
                    search_results = search(out_json[selected_difficulty]["query"], advanced=True, num_results=10)
                    #go through the results
                    index = 1
                    for result in search_results:
                        resource_message = resource_message + f"{index}. {result.title} : {result.url}\n"
                        index += 1
            else:
                #gather resources from json
                for key in out_json:
                    #build level text
                    resource_message = resource_message + f"\n{key.capitalize()} Level\n\n"
                    #build description text
                    resource_message = resource_message + f"Goal: {out_json[key]['description']}\n"
                    #build query text
                    # resource_message = resource_message + f"\tResources:\n"
                    if radio == "Videos":
                        #get search results
                        search_results = json.loads(YoutubeSearch(out_json[key]["query"], max_results=5).to_json())
                        #go through the results
                        index = 1
                        for result in search_results["videos"]:
                            resource_message = resource_message + f"{index}. {result['title']} : https://www.youtube.com{result['url_suffix']}\n"
                    else:
                        #get search results
                        search_results = search(out_json[key]["query"], advanced=True, num_results=5)
                        #go through the results
                        index = 1
                        for result in search_results:
                            resource_message = resource_message + f"{index}. {result.title} : {result.url}\n"
                            index += 1
        else:
            resource_message = "Could not process your request please try again!\n\n"

        #get the total request price
        price = get_request_price(INPUT_TOKENS, OUTPUT_TOKENS)
        #append query price to chatbot
        price_message = f"Process Completed! Total Estimated Price: ${price}"
        #add price message to final message
        resource_message = resource_message + f"\n\n{price_message}"

        # #append learning path to chatbot
        # history.append({"role": "assistant", "content": resource_message})
        #add streaming functionaility
        history.append({"role": "assistant", "content": ""})
        for character in resource_message:
            history[-1]["content"] += character
            time.sleep(0.005)
            yield history

        # history.append({"role": "assistant", "content": price_message})
        #reset tokens for next iteration
        INPUT_TOKENS, OUTPUT_TOKENS = 0, 0
        return history
    
    def clear_handle(history):
        #clear chatbot history
        history = []
        return history
    
    #functions to display file saving information
    def learning_path_info():
        trial_name = os.environ["TRIAL"]
        display_message = f"Learning Path Context Saved To: ./gradio-tests/{trial_name}.txt"
        gr.Info(display_message, duration=10)

    def extracted_content_info():
        trial_name = os.environ["TRIAL"]
        display_message = f"Extracted Content Saved To: ./gradio-tests/content_{trial_name}.txt"
        gr.Info(display_message, duration=10)

    def query_info():
        trial_name = os.environ["TRIAL"]
        display_message = f"Query Information Saved To: ./gradio-tests/queries_{trial_name}.txt"
        gr.Info(display_message, duration=10)
    
    def build_layout(build_type):
        #change layout based on student selection
        if build_type == "Learning Path":
            #build topic textbox selection
            topic = gr.Textbox(
                label="What topic would you like you build your learning path for? i.e. Python, JavaScript, etc...",
                placeholder="Insert your learning topic here",
                interactive=True,
                visible=True
            )
            #build difficulty level selection
            difficulty = gr.Radio(
                ["Beginner", "Intermediate", "Hard", "Advanced"],
                value="Beginner",
                label="What would you say your current expertise level on the subject is at?",
                visible=True,
                interactive=True
            )
            #build chatbot interface
            chatbot = gr.Chatbot(type="messages")
            #build textbot for message input
            msg = gr.Textbox(visible=False)
        else:
            #build topic textbox selection
            topic = gr.Textbox(visible=False, value='')
            #build difficulty level selection
            difficulty = gr.Radio(visible=False)
            #build chatbot interface
            chatbot = gr.Chatbot(type="messages")
            #build textbox for message input
            msg = gr.Textbox(
                label="What question do you want to build a tutorial for?",
                placeholder="Insert what you wish to learn here",
                visible=True
            )
        return topic, difficulty, chatbot, msg
    
    #build layout for resource type selection
    def resource_selection(radio):
        radio = gr.Radio(
            ["Web Results", "Videos"],
            value="Web Results",
            label="What kind of resources would you like to receive?",
            visible=True
        )
        return radio
    
    #build layout for button functionality
    def buttons(clear_button, submit_button):
        clear_button = gr.Button("Clear", interactive=True)
        submit_button = gr.Button("Build Path", interactive=True)
        return clear_button, submit_button
    
    def check_input(build_type, topic, msg):
        if build_type == "Learning Path":
            #list possible learning paths
            possible_topics = ["python", "javascript"]
            #check to see if topic is note empty
            if not topic.strip():
                raise gr.Error("Make sure to include your topic!")
            if topic.lower() not in possible_topics:
                raise gr.Error("Did not recognize topic, make sure to include programming specific topics!")
        else:
            #check tutorial edge cases
            if not msg.strip():
                raise gr.Error("Make sure to input message!")

    def clear_all():
        #add build type component
        build_type = gr.Radio(
            ["Learning Path", "Tutorial"],
            label="What do you wish to build today?",
            value=None
        )

        #add learning path topic textbox
        topic = gr.Textbox(visible=False)

        #add difficulty selection component
        difficulty = gr.Radio(visible=False)

        #build selection gradio
        radio = gr.Radio(visible=False)

        #build chatbot interface
        chatbot = gr.Chatbot(type="messages")

        #build message textbox for chatbot
        msg = gr.Textbox(visible=False)

        #build button row section
        with gr.Row():
            clear_button = gr.Button("Clear", interactive=False)
            submit_button = gr.Button("Build Path", interactive=False)

        return build_type, topic, difficulty, radio, chatbot, msg, clear_button, submit_button
    
    # ---------- Actions ----------
    #handle build type selection
    build_type.select(
        build_layout, build_type, [topic, difficulty, chatbot, msg]
    ).then(
        resource_selection, radio, radio
    ).then(
        buttons, [clear_button, submit_button], [clear_button, submit_button]
    )

    #handle user click on clear button
    clear_button.click(
        clear_handle, chatbot, chatbot
    ).then(
        clear_all, None, [build_type, topic, difficulty, radio, chatbot, msg, clear_button, submit_button]
    )

    #handle user click on submit button
    submit_button.click(
        check_input, [build_type, topic, msg], None
    ).success(
        user, [build_type, topic, msg, chatbot], [msg, chatbot]
    ).then(
        bot, [build_type, difficulty, radio, chatbot], chatbot
    ).then(
        learning_path_info, None, None
    ).then(
        extracted_content_info, None, None
    ).then(
        query_info, None, None
    )

    #handle topic textbox submit
    topic.submit(
        check_input, [build_type, topic, msg], None
    ).success(
        user, [build_type, topic, msg, chatbot], [topic, chatbot]
    ).then(
        bot, [build_type, difficulty, radio, chatbot], chatbot
    ).then(
        learning_path_info, None, None
    ).then(
        extracted_content_info, None, None
    ).then(
        query_info, None, None
    )
    
    #handle user submit
    msg.submit(
        check_input, [build_type, topic, msg], None
    ).success(
        user, [build_type, topic, msg, chatbot], [msg, chatbot]
    ).then(
        bot, [build_type, difficulty, radio, chatbot], chatbot
    ).then(
        learning_path_info, None, None
    ).then(
        extracted_content_info, None, None
    ).then(
        query_info, None, None
    )

if __name__ == "__main__":
    demo.launch(show_error=True)