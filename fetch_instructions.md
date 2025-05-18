https://innovationlab.fetch.ai/resources/docs/examples/adapters/langgraph-adapter-example

===============================
LangGraph Adapter for uAgents
This example demonstrates how to integrate a LangGraph agent with the uAgents ecosystem using the uAgents Adapter package. LangGraph provides powerful orchestration capabilities for LLM applications through directed graphs.

Overview
The LangGraph adapter allows you to:

Wrap LangGraph agents as uAgents for seamless communication
Enable LangGraph agents to participate in the Agentverse ecosystem
Leverage advanced orchestration for complex reasoning while maintaining uAgent compatibility
Example Implementation
Create an agent with file name agent.py
agent.py
import os
import time
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import chat_agent_executor
from langchain_core.messages import HumanMessage

from uagents_adapter import LangchainRegisterTool, cleanup_uagent

# Load environment variables
load_dotenv()

# Set your API keys - for production, use environment variables instead of hardcoding
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]

# Get API token for Agentverse
API_TOKEN = os.environ["AGENTVERSE_API_KEY"]

if not API_TOKEN:
    raise ValueError("Please set AGENTVERSE_API_KEY environment variable")

# Set up tools and LLM
tools = [TavilySearchResults(max_results=3)]
model = ChatOpenAI(temperature=0)

# LangGraph-based executor
app = chat_agent_executor.create_tool_calling_executor(model, tools)

# Wrap LangGraph agent into a function for UAgent
def langgraph_agent_func(query):
    # Handle input if it's a dict with 'input' key
    if isinstance(query, dict) and 'input' in query:
        query = query['input']
    
    messages = {"messages": [HumanMessage(content=query)]}
    final = None
    for output in app.stream(messages):
        final = list(output.values())[0]  # Get latest
    return final["messages"][-1].content if final else "No response"

# Register the LangGraph agent via uAgent
tool = LangchainRegisterTool()
agent_info = tool.invoke(
    {
        "agent_obj": langgraph_agent_func,
        "name": "langgraph_tavily_agent",
        "port": 8080,
        "description": "A LangGraph-based Tavily-powered search agent",
        "api_token": API_TOKEN,
        "mailbox": True
    }
)

print(f"✅ Registered LangGraph agent: {agent_info}")

# Keep the agent alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("🛑 Shutting down LangGraph agent...")
    cleanup_uagent("langgraph_tavily_agent")
    print("✅ Agent stopped.")

Key Components
LangGraph Setup:

Creates a tool-calling executor using LangGraph's prebuilt components
Configures Tavily search as the tool for retrieving information
Uses OpenAI's ChatGPT for LLM capabilities
Function Wrapper:

Wraps the LangGraph app in a function that accepts queries
Handles input format conversion
Processes streaming output from LangGraph
uAgent Registration:

Uses UAgentRegisterTool to register the LangGraph function as a uAgent
Configures a port, description, and mailbox for persistence
Generates a unique address for agent communication
Sample requirements.txt
Here's a sample requirements.txt file you can use for this example:

uagents==0.22.3
uagents-adapter==0.2.1
langchain-openai==0.3.14
langchain-community==0.3.21
langgraph==0.3.31
dotenv==0.9.9

Interacting with the Agent
You can interact with this LangGraph agent through any uAgent using the chat protocol. Here's a client implementation:

agent_client.py
from datetime import datetime
from uuid import uuid4
from uagents import Agent, Protocol, Context

#import the necessary components from the chat protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)
# Initialise agent2
agent2 = Agent(name="client_agent",
               port = 8082,
               mailbox=True,
               seed="client agent testing seed"
               )

# Initialize the chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)

langgraph_agent_address = "agent1q0zyxrneyaury3f5c7aj67hfa5w65cykzplxkst5f5mnyf4y3em3kplxn4t" # Update with your Langgraph Agent's address

# Startup Handler - Print agent details
@agent2.on_event("startup")
async def startup_handler(ctx: Context):
    # Print agent details
    ctx.logger.info(f"My name is {ctx.agent.name} and my address is {ctx.agent.address}")

    # Send initial message to agent2
    initial_message = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text="I want to send query to tavily agent that Give me a list of latest agentic AI trends")]
    )
    await ctx.send(langgraph_agent_address, initial_message)

# Message Handler - Process received messages and send acknowledgements
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    for item in msg.content:
        if isinstance(item, TextContent):
            # Log received message
            ctx.logger.info(f"Received message from {sender}: {item.text}")
            
            # Send acknowledgment
            ack = ChatAcknowledgement(
                timestamp=datetime.utcnow(),
                acknowledged_msg_id=msg.msg_id
            )
            await ctx.send(sender, ack)
            

# Acknowledgement Handler - Process received acknowledgements
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")

# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
agent2.include(chat_proto, publish_manifest=True)

if __name__ == '__main__':
    agent2.run()


Why Use LangGraph with uAgents?
LangGraph offers several advantages when combined with uAgents:

Advanced Orchestration: Create complex reasoning flows using directed graphs
State Management: Handle complex multi-turn conversations with state persistence
Tool Integration: Easily connect to external services and APIs
Debugging Capabilities: Inspect and debug agent reasoning processes
By wrapping LangGraph with the uAgents adapter, you get the best of both worlds: sophisticated LLM orchestration with the decentralized communication capabilities of uAgents.

Getting Started
In a directory get both the agents above agent.py and agent_client.py.

Install required packages:

pip install uagents>=0.22.3 uagents-adapter>=0.2.1 langchain-openai>=0.3.14 langchain-community>=0.3.21 langgraph>=0.3.31  dotenv>=0.9.9


Set up your environment variables in .env file:

OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key  
AGENTVERSE_API_KEY=your_agentverse_key

Run the LangGraph agent:

python agent.py

In a separate terminal, run the client agent:

python agent_client.py
===============================
