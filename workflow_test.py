import asyncio
import logging
import os
import uuid

import dotenv
from pydantic_ai import RunContext

import log
from agent_introducer_finder.agent import (
    IntroducerFinderDeps,
    make_agent_introducer_finder,
)
from workflow import (
    Founder,
    Startup,
    VCPartner,
    get_vc_outreach_workflow,
    VCOutreachWorkflowState,
)

dotenv.load_dotenv()

logger = log.get_logger(__name__)


def get_thread_id():
    return str(uuid.uuid4())


def run_workflow():
    logger.info("Starting VC outreach workflow")

    thread_id = get_thread_id()
    config = {"configurable": {"thread_id": thread_id}}

    # Get credentials from environment variables
    founder_email = os.getenv("FOUNDER_EMAIL")
    founder_password = os.getenv("FOUNDER_PASSWORD")

    if not founder_email or not founder_password:
        logger.error(
            "Missing LinkedIn credentials! Set FOUNDER_EMAIL and FOUNDER_PASSWORD env variables."
        )
        return

    # Example startup and VC data
    state = VCOutreachWorkflowState(
        messages=[],
        startup=Startup(
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
        vc_partner=VCPartner(
            name="Doszhan Zhussupov",
            fund_name="Insight Ventures",
            fund_website="https://insightventures.com",
            linkedin_url="https://www.linkedin.com/in/doszhan-zhussupov/",
        ),
        founder_email=founder_email,
        founder_password=founder_password,
        mutual_connections=[],
        selected_mutual_connection=None,
        found_email="",
        generated_intro="",
        cold_email="",
    )

    workflow = get_vc_outreach_workflow()
    asyncio.run(workflow.ainvoke(state, config))

    final_state = workflow.get_state(config)

    # The get_state method returns a tuple, use the first element
    state_dict = final_state[0] if isinstance(final_state, tuple) else final_state

    # Print the final outputs
    print("\n===== WORKFLOW RESULTS =====")
    print(f"VC Email: {state_dict['found_email']}")

    if state_dict["selected_mutual_connection"]:
        print(
            f"\nSelected Mutual Connection: {state_dict['selected_mutual_connection']['name']}"
        )
        print(
            f"LinkedIn URL: {state_dict['selected_mutual_connection']['linkedin_url']}"
        )

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

    if not founder_email or not founder_password:
        logger.error(
            "Missing LinkedIn credentials! Set FOUNDER_EMAIL and FOUNDER_PASSWORD env variables."
        )
        return

    logger.info("Testing introducer finder agent...")

    # Create the dependencies
    deps = IntroducerFinderDeps(
        founder_email=founder_email,
        founder_password=founder_password,
        vc_linkedin_url=vc_linkedin_url,
    )

    # Create the agent
    agent = make_agent_introducer_finder()

    # Run the agent
    result = asyncio.run(agent.run(deps=deps))

    logger.info(f"Found {len(result.data)} mutual LinkedIn connections")
    for idx, connection in enumerate(result.data[:5]):  # Show first 5 connections
        logger.info(
            f"Connection {idx+1}: {connection['name']} - {connection['linkedin_url']}"
        )


if __name__ == "__main__":
    # Uncomment the function you want to test
    run_workflow()
    # test_introducer_finder()
