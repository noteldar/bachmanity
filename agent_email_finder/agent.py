import sys
import os
import logging
from typing import List

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from dataclasses import dataclass
from pydantic_ai import RunContext

from firecrawl_tools import tool_deep_research
from pydantic_ai import Agent

from openai_model import get_openai_model
from dotenv import load_dotenv

load_dotenv()

# Set up basic logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)


@dataclass
class VCPartner:
    name: str
    fund_name: str
    fund_website: str
    linkedin_url: str


@dataclass
class EmailFinderDeps:
    vc_partner: VCPartner


def make_agent_email_finder(model_name="o3-mini"):
    agent = Agent(
        get_openai_model(model_name),
        system_prompt="""
        You are an assistant that helps find email addresses of VC partners.
        Use all available information about the VC partner to search for their professional email address.
        Only return the email address, nothing else.
        """,
        deps_type=EmailFinderDeps,
        retries=3,
        result_type=str,
        tools=[tool_deep_research],
    )
    agent.system_prompt(add_context)
    return agent


def add_context(ctx: RunContext[EmailFinderDeps]) -> str:
    return f"""
    You need to find the email address for the following VC partner:
    VC partner name: {ctx.deps.vc_partner.name}.
    VC partner fund name: {ctx.deps.vc_partner.fund_name}.
    VC partner fund website: {ctx.deps.vc_partner.fund_website}.
    VC partner LinkedIn URL: {ctx.deps.vc_partner.linkedin_url}.
    
    Use the deep_research tool to search for the email address.
    Try looking at their fund website, LinkedIn profiles, and any other professional sources.
    Return only the email address, with no additional text.
    """
