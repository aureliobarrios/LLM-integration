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
        #get the previous message
        prev_message = history[-1]["content"]
        #handle input based on different selections
        if build_type == "Learning Path":
            #get the topic
            topic = prev_message.split(":")[1].lower()
            #build test message
            message = f"Prompt Input: I want to learn {topic}"
            #add message to history
            history.append({"role": "assistant", "content": message})
        else:
            #build message
            message = f"Prompt Input: {prev_message}"
            #add streaming functionaility
            history.append({"role": "assistant", "content": message})
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