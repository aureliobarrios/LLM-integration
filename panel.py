import gradio as gr
from scipy.stats import norm
from math import sqrt, exp

with gr.Blocks() as demo:

    #build the confidence score function
    def confidence(ups, downs, confidence_score=0.90):
        #measure the total number of ratings
        n = ups + downs
        #what to do when there are no ratings
        if n == 0:
            return 0
        # finding the (1- confidence / 2) quantile of the standard normal distribution
        z = norm.ppf(1 - ((1 - confidence_score) / 2))
        #find the observed fraction of positive ratings
        p = ups / n
        #use Wilsons score interval to find the lower bound, essentially trying to answer
        # Given the ratings I have, there is a 80% chance (based on confidence score) that the
        # "real" fraction of positive ratings is at least what?
        #     we want the lower bound therefore only calculating that portion of formula
        #Calculate the left side of formula
        left_side = p + 1/(2*n)*z*z
        #Calculate the right side of formula
        right_side = z*sqrt(p*(1-p)/n + z*z/(4*n*n))
        #Calculate the bottom side of formula
        under = 1+1/n*z*z
        #return lower bound of score
        return (left_side - right_side) / under
    
    #build function that gets the current score
    def get_score(upvotes, downvotes, views, total_users, time, alpha, beta, delta):
        #get the reddit confidence score
        p = confidence(upvotes, downvotes)
        #calculate p^alpha
        confidence_score = p ** alpha
        #calculate the viewership portion
        engagement = (views / total_users) ** beta
        #calculate the seconds
        seconds = time * 86400
        #calculate time part
        time_decay = exp(-(10**(-delta))*seconds)
        #return the final score
        return confidence_score * engagement * time_decay


    def score(alpha_slider, beta_slider, lambda_slider, upvotes, downvotes, population, views, days, chatbot):
        #get the score for current scenario
        score = get_score(upvotes, downvotes, views, population, days, alpha_slider, beta_slider, lambda_slider)
        #start building message
        user_message = f"Alpha: {alpha_slider} -- Beta: {beta_slider} -- Time Decay: {lambda_slider}\nVotes: {upvotes}/{downvotes} -- Engagement: {views}/{population} -- Days: {days}"
        #append user message to chatbot
        chatbot.append({"role": "user", "content": user_message})
        #start building message
        message = f"Final Score For Your Scenario: {score}"
        #append message to chatbot
        chatbot.append({"role": "assistant", "content": message})
        return chatbot

    #build a the weights row section
    with gr.Row():
        #build alpha
        alpha_slider = gr.Slider(value=0.8, minimum=0.1, maximum=1.5, step=0.1, interactive=True, label="Alpha Weight", info="How much weight is put into Upvote/Downvote proportion")
        #build beta
        beta_slider = gr.Slider(value=0.05, minimum=0.01, maximum=1, step=0.01, interactive=True, label="Beta Weight", info="How much weight is put into Engagement (Percent of Population)")
        #build lambda
        lambda_slider = gr.Slider(value=7, minimum=5, maximum=10, step=1, interactive=True, label="Time Decay", info="How fast a resource will depreciate over time (Smaller equals Faster)")

    #build the reddit row section
    with gr.Row():
        #build the upvote section
        upvotes = gr.Number(value=10, minimum=0, interactive=True, label="Number of Upvotes")
        #build the downvote section
        downvotes = gr.Number(value=10, minimum=0, interactive=True, label="Number of Downvotes")

    #build the engagement section
    with gr.Row():
        #build the population section
        population = gr.Number(value=200, minimum=1, label="Total Population", interactive=True)
        #build the views section
        views = gr.Number(value=1, minimum=1, label="Views From Population", interactive=True)
        #build the days section
        days = gr.Number(value=1, minimum=0, label="Number of Days Since Post", interactive=True)

    #build clear and submit section
    with gr.Row():
        #buikd clear button section
        clear_button = gr.Button("Clear", interactive=True)
        #build submit button section
        score_button = gr.Button("Score", interactive=True)

    #build chatbot interface
    chatbot = gr.Chatbot(type="messages")

    #function to clear chatbot history
    def clear_handle(chatbot):
        #clear chatbot history
        chatbot = []
        return chatbot

    #handle clear button click
    clear_button.click(
        clear_handle, chatbot, chatbot
    )
    #handle score button click
    score_button.click(
        score, [alpha_slider, beta_slider, lambda_slider, upvotes, downvotes, population, views, days, chatbot], chatbot
    )


if __name__ == "__main__":
    demo.launch(show_error=True)