import gradio as gr

with gr.Blocks() as demo:
    #build a the weights row section
    with gr.Row():
        #build alpha
        alpha_slider = gr.Slider(value=0.8, minimum=0.1, maximum=1.9, step=0.1, interactive=True, label="Alpha Weight", info="How much weight is put into Upvote/Downvote proportion")
        #build beta
        beta_slider = gr.Slider(value=0.05, minimum=0.01, maximum=0.10, step=0.01, interactive=True, label="Beta Weight", info="How much weight is put into Engagement (Percent of Population)")
        #build lambda
        lambda_slider = gr.Slider(value=7, minimum=5, maximum=10, step=1, interactive=True, label="Time Decay", info="How fast a resource will depreciate over time")

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
        views = gr.Number(value=0, minimum=0, maximum=population.value, label="Views From Population", interactive=True)
        #build the days section
        days = gr.Number(value=1, minimum=0, label="Number of Days Since Post", interactive=True)

if __name__ == "__main__":
    demo.launch(show_error=True)