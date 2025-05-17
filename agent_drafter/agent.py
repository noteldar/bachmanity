import sys
import os
import logging
from typing import List

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from dataclasses import dataclass
from datetime import datetime
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
class Founder:
    name: str
    background: str


@dataclass
class Startup:
    vision: str
    company_name: str
    founders: List[Founder]
    product_description: str


@dataclass
class VCPartner:
    name: str
    fund_name: str
    fund_website: str
    linkedin_url: str


@dataclass
class DrafterDeps:
    startup: Startup
    vc_partner: VCPartner


def make_agent_email_drafter(provider_name="azure", model_name="o3-mini"):
    agent = Agent(
        get_openai_model(model_name),
        system_prompt="""
        You are an assistant that helps draft emails from founders to VCs.
        Make the email short but personalized, highlight the things about the startup that might interest the VC.
        """,
        deps_type=DrafterDeps,
        retries=3,
        result_type=str,
        tools=[tool_deep_research],
    )
    agent.system_prompt(add_context)
    return agent


def add_context(ctx: RunContext[DrafterDeps]) -> str:
    return f"""
    You have the following information about the startup:
    Startup name: {ctx.deps.startup.company_name}.
    Vision: {ctx.deps.startup.vision}.
    Product description: {ctx.deps.startup.product_description}.
    Founders: {ctx.deps.startup.founders}.

    You also have the following information about the VC partner:
    VC partner name: {ctx.deps.vc_partner.name}.
    VC partner fund name: {ctx.deps.vc_partner.fund_name}.
    VC partner fund website: {ctx.deps.vc_partner.fund_website}.
    VC partner linkedin url: {ctx.deps.vc_partner.linkedin_url}.
    """
