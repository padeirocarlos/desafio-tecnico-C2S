import asyncio
import gradio as gr
from agentic.nodes import WorkflowState
from agentic.graph import workflow_app, thread_id_genrater, message, reset

async def workflow(WorkflowState):
    config = {"configurable": {"thread_id": 1}}
    user = {"role": "user", "content": query, "query": query}
    
    # graph = await graph_builder()
    
    graph = await workflow_app()
    
    result = await graph.ainvoke(user, config=config)

async def message(query, history, thread):

    config = {"configurable": {"thread_id": thread}}
    user = {"role": "user", "content": query, "query": query}
    
    # graph = await graph_builder()
    
    graph = await workflow_app()
    
    result = await graph.ainvoke(user, config=config)
    
    content_ =list(result["result"][-1].additional_kwargs.values())
    
    content = " \n ----- \n ".join(content_)
    
    reply = {"role": "assistant", "content": content}
    
    return history + [user, reply]


async def chat(user_input: str, history):
    # initial_state = State(messages=[{"role": "user", "content": user_input}])
    config = {"configurable": {"thread_id": 1}}
    initial_state = WorkflowState()
    initial_state["original_query"] = user_input
    graph = await workflow_app()
    result = await graph.ainvoke(initial_state, config=config)
    print(result['final_response'])
    return result['final_response']

gr.ChatInterface(chat, type="messages").launch(share=True)


