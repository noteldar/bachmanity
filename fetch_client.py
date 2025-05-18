from datetime import datetime
from uuid import uuid4
import json
from dotenv import load_dotenv
from uagents import Agent, Protocol, Context

# Import the necessary components from the chat protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

# Load environment variables
load_dotenv()

# Initialize client agent
client_agent = Agent(
    name="vc_outreach_client", port=8082, mailbox=True, seed="vc_outreach_client_seed"
)

# Initialize the chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)

# Replace with your workflow agent's address after running fetch_agent.py
workflow_agent_address = (
    "agent1qvwaclryk8uwxsjxh5dmwvmtfxurzaa49gzz8kw9gwtt0y28aupkgy4hzew"
)

# Example data for testing
test_query = {
    "startup": {
        "vision": "To revolutionize healthcare with AI-powered diagnostics",
        "company_name": "MediScan AI",
        "founders": [
            {"name": "Alex Johnson", "background": "PhD in ML, ex-Google Health"},
            {
                "name": "Sasha Lee",
                "background": "Ex-CTO at HealthTech, MD from Stanford",
            },
        ],
        "product_description": "An AI diagnostic tool that analyzes medical images with 98% accuracy, helping doctors detect diseases earlier and more reliably.",
    },
    "vc_partner": {
        "name": "Michael Chen",
        "fund_name": "Insight Ventures",
        "fund_website": "https://insightventures.com",
        "linkedin_url": "https://linkedin.com/in/michaelchen",
    },
    "mutual_connection": "Dr. Rachel Wong, Chief Innovation Officer at Stanford Medicine",
    "thread_id": str(uuid4()),
}


# Startup Handler - Print agent details and send initial message
@client_agent.on_event("startup")
async def startup_handler(ctx: Context):
    # Print agent details
    ctx.logger.info(
        f"My name is {ctx.agent.name} and my address is {ctx.agent.address}"
    )

    # Format the query as text for the message
    query_text = (
        f"I want to run a VC outreach workflow with this data: {json.dumps(test_query)}"
    )

    # Send initial message to workflow agent
    initial_message = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=query_text)],
    )

    ctx.logger.info(f"Sending request to workflow agent at {workflow_agent_address}")
    await ctx.send(workflow_agent_address, initial_message)
    ctx.logger.info("Request sent! Waiting for response...")


# Message Handler - Process received messages and send acknowledgements
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    for item in msg.content:
        if isinstance(item, TextContent):
            # Log received message
            ctx.logger.info(f"Received response from {sender}:")
            ctx.logger.info(f"{item.text}")

            # Parse the response if it's JSON
            try:
                response_data = json.loads(item.text)
                if isinstance(response_data, dict):
                    if "found_email" in response_data:
                        ctx.logger.info(
                            f"\n===== VC EMAIL =====\n{response_data['found_email']}"
                        )
                    if "generated_intro" in response_data:
                        ctx.logger.info(
                            f"\n===== WARM INTRODUCTION =====\n{response_data['generated_intro']}"
                        )
                    if "cold_email" in response_data:
                        ctx.logger.info(
                            f"\n===== COLD EMAIL =====\n{response_data['cold_email']}"
                        )
            except json.JSONDecodeError:
                # Not JSON, just display as is
                pass

            # Send acknowledgment
            ack = ChatAcknowledgement(
                timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id
            )
            await ctx.send(sender, ack)


# Acknowledgement Handler - Process received acknowledgements
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(
        f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}"
    )


# Include the protocol in the agent to enable the chat functionality
client_agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    client_agent.run()
