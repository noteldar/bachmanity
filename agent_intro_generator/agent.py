import sys
import os
import logging
from typing import List

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from dataclasses import dataclass
from pydantic_ai import RunContext

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
class IntroGeneratorDeps:
    startup: Startup
    vc_partner: VCPartner
    mutual_connection: str


def make_agent_intro_generator(model_name="o3-mini"):
    agent = Agent(
        get_openai_model(model_name),
        system_prompt="""
        You are an assistant that creates personalized introductions for warm connections between startup founders and VCs.
        Your task is to draft a brief, personalized message from a mutual connection introducing the startup founders to the VC.
        The intro should be concise, professional, and highlight why this connection would be valuable for both parties.
        """,
        deps_type=IntroGeneratorDeps,
        retries=3,
        result_type=str,
    )
    agent.system_prompt(add_context)
    return agent


def add_context(ctx: RunContext[IntroGeneratorDeps]) -> str:
    return f"""
    You need to draft a warm introduction from a mutual connection.
    
    Startup information:
    Startup name: {ctx.deps.startup.company_name}
    Vision: {ctx.deps.startup.vision}
    Product description: {ctx.deps.startup.product_description}
    Founders: {ctx.deps.startup.founders}

    VC partner information:
    VC partner name: {ctx.deps.vc_partner.name}
    VC partner fund name: {ctx.deps.vc_partner.fund_name}
    VC partner fund website: {ctx.deps.vc_partner.fund_website}
    
    Mutual connection: {ctx.deps.mutual_connection}
    
    Create a brief, personalized email introduction from the mutual connection's perspective that:
    1. Greets both parties by name
    2. Explains why you're making the introduction
    3. Introduces the startup founders and highlights their key strengths
    4. Mentions why this connection would be valuable for both parties
    5. Offers a polite closing that encourages further discussion

    Format the email as if it were being sent from the mutual connection to both parties.
    """
