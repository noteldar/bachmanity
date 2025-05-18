import asyncio
import logging
import os
import uuid

import dotenv

import log
from agent_introducer_finder.agent import tool_smart_linkedin_mutual_connections
from workflow import Founder, Startup, VCPartner, get_vc_outreach_workflow

dotenv.load_dotenv()

logger = log.get_logger(__name__)


def get_thread_id():
    return str(uuid.uuid4())


def run_workflow():
    logger.info("Starting VC outreach workflow")

    thread_id = get_thread_id()
    config = {"configurable": {"thread_id": thread_id}}

    # Example startup and VC data
    state = {
        "messages": [],
        "startup": Startup(
            vision="To revolutionize healthcare with AI-powered diagnostics",
            company_name="MediScan AI",
            founders=[
                Founder(name="Alex Johnson", background="PhD in ML, ex-Google Health"),
                Founder(
                    name="Sasha Lee",
                    background="Ex-CTO at HealthTech, MD from Stanford",
                ),
            ],
            product_description="An AI diagnostic tool that analyzes medical images with 98% accuracy, helping doctors detect diseases earlier and more reliably.",
        ),
        "vc_partner": VCPartner(
            name="Michael Chen",
            fund_name="Insight Ventures",
            fund_website="https://insightventures.com",
            linkedin_url="https://linkedin.com/in/michaelchen",
        ),
        "mutual_connection": "Dr. Rachel Wong, Chief Innovation Officer at Stanford Medicine",
        "found_email": "",
        "generated_intro": "",
        "cold_email": "",
    }

    workflow = get_vc_outreach_workflow()
    asyncio.run(workflow.ainvoke(state, config))

    final_state = workflow.get_state(config)

    # The get_state method returns a tuple, use the first element
    state_dict = final_state[0] if isinstance(final_state, tuple) else final_state

    # Print the final outputs
    print("\n===== WORKFLOW RESULTS =====")
    print(f"VC Email: {state_dict['found_email']}")
    print("\n----- WARM INTRODUCTION -----")
    print(state_dict["generated_intro"])
    print("\n----- COLD EMAIL -----")
    print(state_dict["cold_email"])


@log.add_logger(logger)
def test_introducer_finder():
    logger: logging.Logger = test_introducer_finder.logger
    founder_email = os.getenv("FOUNDER_EMAIL")
    founder_password = os.getenv("FOUNDER_PASSWORD")
    vc_linkedin_url = "https://www.linkedin.com/in/noteldar"
    logger.info("Testing introducer finder agent...")
    result = tool_smart_linkedin_mutual_connections(
        founder_email, founder_password, vc_linkedin_url
    )
    logger.info(f"Mutual LinkedIn connections: {result}")


if __name__ == "__main__":
    # run_workflow()
    test_introducer_finder()
