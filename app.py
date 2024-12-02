import os
import json
import gradio as gr
from groq import Groq
from googlesearch import search
from dotenv import load_dotenv

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

# -------------------- Environment Variables --------------------

INPUT_TOKENS = 0 #prompt tokens
OUTPUT_TOKENS = 0 #completion tokens

#load environment variables and build client
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(
    api_key=GROQ_API_KEY
)

with gr.Blocks() as demo:
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
        bot_message = "You typed: " + history[-1]["content"] +  ", and selected: " + radio

        #include link
        bot_message = bot_message + "\nHere is your link: https://www.youtube.com/watch?v=kWo3iPDsVWU"

        history.append({"role": "assistant", "content": bot_message})
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
    
    # ---------- Actions ----------

    #handle user submit
    msg.submit(
        user, [msg, chatbot], [msg, chatbot], queue=False
    ).then(
        bot, [chatbot, radio], chatbot
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
    )

if __name__ == "__main__":
    demo.launch()