import os
import time
import json
from dotenv import load_dotenv
from typing import Dict, Any, Union

from uagents_adapter import LangchainRegisterTool, cleanup_uagent

from workflow import get_vc_outreach_workflow, Startup, Founder, VCPartner

# Load environment variables
load_dotenv()

# Get API token for Agentverse
API_TOKEN = os.environ["FETCH_AI_API_KEY"]

if not API_TOKEN:
    raise ValueError("Please set FETCH_AI_API_KEY environment variable")

# Get the workflow graph
workflow = get_vc_outreach_workflow()


# Wrap workflow into a function for UAgent
async def workflow_agent_func(query: Union[Dict[str, Any], str]):
    # Handle input as string (from chat messages)
    if isinstance(query, str):
        try:
            # Try to extract JSON from the message
            # First, look for a JSON object in the string
            import re

            json_match = re.search(r"{.*}", query, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                query_data = json.loads(json_str)
            else:
                return "Invalid input format. Please provide startup and VC partner data in JSON format."
        except json.JSONDecodeError:
            return "Could not parse JSON data from message."

    # Handle input as dict (direct invocation)
    elif isinstance(query, dict):
        if "input" in query:
            # Handle the case where input is nested
            if isinstance(query["input"], str):
                try:
                    # Try to extract JSON from the input string
                    import re

                    json_match = re.search(r"{.*}", query["input"], re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        query_data = json.loads(json_str)
                    else:
                        return "Invalid input format. Please provide startup and VC partner data in JSON format."
                except json.JSONDecodeError:
                    return "Could not parse JSON data from message."
            else:
                query_data = query["input"]
        else:
            query_data = query
    else:
        return "Invalid input type. Expected dictionary or string."

    # Extract parameters from the query data
    startup_data = query_data.get("startup", {})
    vc_partner_data = query_data.get("vc_partner", {})
    mutual_connection = query_data.get("mutual_connection", "")

    # Create the workflow state
    state = {
        "messages": [],
        "startup": Startup(
            vision=startup_data.get("vision", ""),
            company_name=startup_data.get("company_name", ""),
            founders=[
                Founder(
                    name=founder.get("name", ""),
                    background=founder.get("background", ""),
                )
                for founder in startup_data.get("founders", [])
            ],
            product_description=startup_data.get("product_description", ""),
        ),
        "vc_partner": VCPartner(
            name=vc_partner_data.get("name", ""),
            fund_name=vc_partner_data.get("fund_name", ""),
            fund_website=vc_partner_data.get("fund_website", ""),
            linkedin_url=vc_partner_data.get("linkedin_url", ""),
        ),
        "mutual_connection": mutual_connection,
        "found_email": "",
        "generated_intro": "",
        "cold_email": "",
    }

    # Generate a unique thread_id
    thread_id = str(query_data.get("thread_id", time.time()))
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Run the workflow
        await workflow.ainvoke(state, config)

        # Get the final state
        final_state = workflow.get_state(config)
        state_dict = final_state[0] if isinstance(final_state, tuple) else final_state

        # Return the results as JSON string
        results = {
            "found_email": state_dict["found_email"],
            "generated_intro": state_dict["generated_intro"],
            "cold_email": state_dict["cold_email"],
        }
        return json.dumps(results)
    except Exception as e:
        return f"Error running workflow: {str(e)}"


# Register the LangGraph workflow via uAgent
tool = LangchainRegisterTool()
agent_info = tool.invoke(
    {
        "agent_obj": workflow_agent_func,
        "name": "vc_outreach_workflow_agent",
        "port": 8080,
        "description": "A LangGraph-based VC outreach workflow for startups",
        "api_token": API_TOKEN,
        "mailbox": True,
    }
)

print(f"✅ Registered VC Outreach workflow agent: {agent_info}")

# Keep the agent alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("🛑 Shutting down VC Outreach workflow agent...")
    cleanup_uagent("vc_outreach_workflow_agent")
    print("✅ Agent stopped.")
