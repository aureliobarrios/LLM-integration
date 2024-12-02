import os
import json
import uuid
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

#trial name to save test
trial_name = uuid.uuid4().hex[:5]

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
    
    def info_fn():
        display_message = f"File saved to: {trial_name}"
        gr.Info(display_message, duration=3)
    
    # ---------- Actions ----------

    #handle user submit
    msg.submit(
        user, [msg, chatbot], [msg, chatbot], queue=False
    ).then(
        bot, [chatbot, radio], chatbot
    ).then(
        info_fn, None, None
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
        info_fn, None, None
    )

if __name__ == "__main__":
    demo.launch(show_error=True)