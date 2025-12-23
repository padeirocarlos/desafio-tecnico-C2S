import os
import time
import logging
import gradio as gr
from agentic.graph import process_message, VehicleChat

async def setup():
    vehicleChat = VehicleChat()
    await vehicleChat.setup()
    return vehicleChat

async def cleanup():
    new_vehicleChat = VehicleChat()
    await new_vehicleChat.setup()
    return "#### ℹ️ Your query and click Go!", None, None, new_vehicleChat, None

def free_resources(vehicleChat):
    print("Cleaning up")
    try:
        if vehicleChat:
            vehicleChat.setup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")
        
with gr.Blocks(theme=gr.themes.Default(primary_hue="emerald")) as demo:
    gr.Markdown("## Vehicle Seller Assistant Supporter ")
    vehicleChat = gr.State(delete_callback=free_resources)
    
    with gr.Row():
        chatbot = gr.Chatbot(label="Vehicle Seller Assistant AI", height=400, type="messages")
        
    with gr.Group():
        with gr.Row():
            chat_query_error_check = gr.Markdown(value="#### ℹ️ Your query and click Go!")
        with gr.Row():
            chat_query = gr.Textbox(show_label=False, placeholder="Your query to Vehicle Seller Assistant (VSA) AI system?")
            
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    demo.load(setup, [], [vehicleChat])
    
    chat_query.submit(process_message, [vehicleChat, chat_query, chatbot], [chat_query_error_check, chatbot, vehicleChat, chat_query])
    go_button.click(process_message, [vehicleChat, chat_query, chatbot], [chat_query_error_check, chatbot, vehicleChat, chat_query])
    reset_button.click(cleanup, [], [chat_query_error_check, chat_query, chatbot, vehicleChat, chat_query])
    
demo.launch(share=True, auth=None)