from typing import TypedDict, Annotated, List

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from dataclasses import dataclass
import logging

from agent_drafter.agent import (
    make_agent_email_drafter,
    DrafterDeps,
    Founder,
    Startup,
    VCPartner,
)
from agent_email_finder.agent import make_agent_email_finder, EmailFinderDeps
from agent_intro_generator.agent import make_agent_intro_generator, IntroGeneratorDeps

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class VCOutreachWorkflowState(TypedDict):
    messages: Annotated[List[bytes], lambda x, y: x + y]
    startup: Startup
    vc_partner: VCPartner
    mutual_connection: str
    found_email: str
    generated_intro: str
    cold_email: str


def get_vc_outreach_workflow(model_name="o3-mini"):
    agent_email_finder = make_agent_email_finder(model_name=model_name)
    agent_intro_generator = make_agent_intro_generator(model_name=model_name)
    agent_email_drafter = make_agent_email_drafter(model_name=model_name)

    async def node_email_finder(state: VCOutreachWorkflowState):
        logger.info("Running email finder node")

        deps = EmailFinderDeps(
            vc_partner=state["vc_partner"],
        )

        result = await agent_email_finder.run(deps=deps)
        found_email = result.data

        logger.info(f"Found VC email: {found_email}")

        return {"found_email": found_email}

    async def node_intro_generator(state: VCOutreachWorkflowState):
        logger.info("Running intro generator node")

        deps = IntroGeneratorDeps(
            startup=state["startup"],
            vc_partner=state["vc_partner"],
            mutual_connection=state["mutual_connection"],
        )

        result = await agent_intro_generator.run(deps=deps)
        generated_intro = result.data

        logger.info(f"Generated intro: {generated_intro[:100]}...")

        return {"generated_intro": generated_intro}

    async def node_email_drafter(state: VCOutreachWorkflowState):
        logger.info("Running email drafter node")

        # Update the VC partner with the found email if needed
        vc_partner = state["vc_partner"]

        deps = DrafterDeps(startup=state["startup"], vc_partner=vc_partner)

        result = await agent_email_drafter.run(deps=deps)
        cold_email = result.data

        logger.info(f"Drafted cold email: {cold_email[:100]}...")

        return {"cold_email": cold_email}

    async def node_finish(state: VCOutreachWorkflowState):
        logger.info("Finishing workflow")
        logger.info(
            f"VC Partner: {state['vc_partner'].name} from {state['vc_partner'].fund_name}"
        )
        logger.info(f"Email: {state['found_email']}")
        logger.info("-------- Warm Introduction --------")
        logger.info(state["generated_intro"])
        logger.info("-------- Cold Email --------")
        logger.info(state["cold_email"])

        return state

    builder = StateGraph(VCOutreachWorkflowState)

    # Add nodes
    builder.add_node("node_email_finder", node_email_finder)
    builder.add_node("node_intro_generator", node_intro_generator)
    builder.add_node("node_email_drafter", node_email_drafter)
    builder.add_node("node_finish", node_finish)

    # Add edges
    builder.add_edge(START, "node_email_finder")
    builder.add_edge("node_email_finder", "node_intro_generator")
    builder.add_edge("node_intro_generator", "node_email_drafter")
    builder.add_edge("node_email_drafter", "node_finish")
    builder.add_edge("node_finish", END)

    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)

    return graph


# Example usage:
# workflow = get_vc_outreach_workflow()
# config = VCOutreachWorkflowState(
#     messages=[],
#     startup=Startup(
#         vision="To revolutionize the way people interact with AI",
#         company_name="AI Innovations",
#         founders=[Founder(name="Jane Doe", background="Ex-Google AI researcher")],
#         product_description="An AI platform that learns from user behavior"
#     ),
#     vc_partner=VCPartner(
#         name="John Smith",
#         fund_name="Tech Ventures",
#         fund_website="https://techventures.com",
#         linkedin_url="https://linkedin.com/in/johnsmith"
#     ),
#     mutual_connection="Sarah Johnson, CTO at TechCorp",
#     found_email="",
#     generated_intro="",
#     cold_email=""
# )
# result = await workflow.invoke(config)
