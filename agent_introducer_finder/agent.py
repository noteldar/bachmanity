import logging
import os
import sys
from typing import List

from models import DrafterDeps

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import asyncio
import json
import re
import tempfile
import time

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic_ai import Agent, RunContext

import log
from firecrawl_tools import tool_deep_research
from openai_model import get_openai_model

load_dotenv()

# Set up basic logger
logger = log.get_logger(__name__)


async def get_linkedin_mutual_connections(
    founder_email: str, founder_password: str, vc_linkedin_url: str
) -> list:
    server_params = StdioServerParameters(
        command="npx", args=["@playwright/mcp@latest", "--headless"]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # 1. Go to LinkedIn login
            await session.call_tool(
                "browser_navigate", {"url": "https://www.linkedin.com/login"}
            )
            # 2. Type email
            await session.call_tool(
                "browser_type", {"element": "Email or Phone", "text": founder_email}
            )
            # 3. Type password
            await session.call_tool(
                "browser_type",
                {"element": "Password", "text": founder_password, "submit": True},
            )
            # 4. Wait for homepage
            await session.call_tool("browser_wait_for", {"text": "Home"})
            # 5. Go to VC profile
            await session.call_tool("browser_navigate", {"url": vc_linkedin_url})
            # 6. Try to click Connections
            try:
                await session.call_tool("browser_click", {"element": "Connections"})
            except Exception:
                # Fallback: click mutual connections
                await session.call_tool(
                    "browser_click", {"element": "mutual connections"}
                )
            await session.call_tool("browser_wait_for", {"text": "Mutual Connections"})
            # 7. Get snapshot and extract names (simplified)
            snapshot = await session.call_tool("browser_snapshot")
            # This is a placeholder: in practice, parse snapshot.content[0].text for names
            return [snapshot.content[0].text]


def tool_linkedin_mutual_connections(
    founder_email: str, founder_password: str, vc_linkedin_url: str
) -> list:
    return asyncio.run(
        get_linkedin_mutual_connections(
            founder_email, founder_password, vc_linkedin_url
        )
    )


@log.add_logger(logger)
async def smart_linkedin_mutual_connections(
    founder_email: str, founder_password: str, vc_linkedin_url: str, agent, max_steps=30
) -> list:
    logger: logging.Logger = smart_linkedin_mutual_connections.logger
    with tempfile.TemporaryDirectory() as user_data_dir:
        server_params = StdioServerParameters(
            command="npx",
            args=[
                "@playwright/mcp@latest",
                "--headless",
                "--user-data-dir",
                user_data_dir,
            ],
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                # Start at LinkedIn login
                logger.info("Navigating to LinkedIn login page...")
                result = await session.call_tool(
                    "browser_navigate", {"url": "https://www.linkedin.com/login"}
                )
                # Take a fresh snapshot after navigation
                snapshot = await session.call_tool("browser_snapshot")
                snapshot_text = snapshot.content[0].text

                def extract_ref(snapshot_text, label):
                    # Find all lines with [ref=...]
                    for line in snapshot_text.splitlines():
                        if label in line and "[ref=" in line:
                            m = re.search(r"\[ref=(e\d+)\]", line)
                            if m:
                                return m.group(1)
                    return None

                email_ref = extract_ref(snapshot_text, 'textbox "Email or phone"')
                password_ref = extract_ref(snapshot_text, 'textbox "Password"')
                signin_ref = extract_ref(snapshot_text, 'button "Sign in"')
                logger.info(
                    f"Extracted refs: {email_ref}, {password_ref}, {signin_ref}"
                )

                # Focus email field
                await session.call_tool(
                    "browser_click",
                    {"element": "textbox 'Email or phone'", "ref": email_ref},
                )
                # Fill email
                logger.info("Filling email field...")
                result = await session.call_tool(
                    "browser_type",
                    {
                        "element": "textbox 'Email or phone'",
                        "ref": email_ref,
                        "text": founder_email,
                    },
                )
                # Focus password field
                await session.call_tool(
                    "browser_click",
                    {"element": "textbox 'Password'", "ref": password_ref},
                )
                # Fill password
                logger.info("Filling password field...")
                result = await session.call_tool(
                    "browser_type",
                    {
                        "element": "textbox 'Password'",
                        "ref": password_ref,
                        "text": founder_password,
                    },
                )
                # Click submit
                logger.info("Clicking sign in button...")
                result = await session.call_tool(
                    "browser_click", {"element": "button 'Sign in'", "ref": signin_ref}
                )
                # Wait for home page to load
                logger.info("Waiting for home page to load...")
                await session.call_tool("browser_wait_for", {"text": "Home"})
                # Navigate to VC partner's LinkedIn page
                logger.info(f"Navigating to VC partner's page: {vc_linkedin_url}")
                result = await session.call_tool(
                    "browser_navigate", {"url": vc_linkedin_url}
                )
                # Wait for VC partner's profile to load (look for 'Connect' button or similar)
                logger.info("Waiting for VC partner's profile to load...")
                await session.call_tool("browser_wait_for", {"text": "Connect"})

                # Take a snapshot and try to find the mutual connection link
                snapshot = await session.call_tool("browser_snapshot")
                snapshot_text = snapshot.content[0].text
                logger.info("Snapshot on VC profile page taken.")

                # Find a link whose label contains 'mutual connection' (case-insensitive)
                mutual_ref = None
                mutual_label = None
                for line in snapshot_text.splitlines():
                    if (
                        "link" in line.lower()
                        and "mutual connection" in line.lower()
                        and "[ref=" in line
                    ):
                        m = re.search(r"\[ref=(e\d+)\]", line)
                        label_match = re.search(r'link "([^"]+)"', line)
                        if m:
                            mutual_ref = m.group(1)
                        if label_match:
                            mutual_label = label_match.group(1)
                        if mutual_ref and mutual_label:
                            logger.info(
                                f"Found mutual connection link with ref: {mutual_ref} and label: {mutual_label}"
                            )
                            break
                if mutual_ref and mutual_label:
                    logger.info("Clicking mutual connection link...")
                    result = await session.call_tool(
                        "browser_click",
                        {"element": f"link '{mutual_label}'", "ref": mutual_ref},
                    )
                    logger.info(f"browser_click (mutual connection) result: {result}")
                    snapshot = await session.call_tool("browser_snapshot")
                    snapshot_text = snapshot.content[0].text

                    def extract_mutual_connections(snapshot_text):
                        lines = snapshot_text.splitlines()
                        connections = []
                        for i, line in enumerate(lines):
                            m = re.search(
                                r'- link "([^"]+)" \[ref=[^\]]+\] \[cursor=pointer\]:',
                                line,
                            )
                            if m:
                                raw_name = m.group(1)
                                # Clean up the name: take up to first comma, or remove ' Status is reachable' etc.
                                name = raw_name.split(",")[0].strip()
                                # Remove common status suffixes if present
                                for suffix in [
                                    "Status is reachable",
                                    "Status is online",
                                ]:
                                    if name.endswith(suffix):
                                        name = name[: -len(suffix)].strip()
                                url = None
                                for j in range(i + 1, min(i + 5, len(lines))):
                                    url_match = re.search(
                                        r"/url: (https://www\.linkedin\.com/in/[^\s]+)",
                                        lines[j],
                                    )
                                    if url_match:
                                        url = url_match.group(1)
                                        break
                                if name and url:
                                    connections.append(
                                        {"name": name, "linkedin_url": url}
                                    )
                        return connections[:10]

                    mutual_connections = extract_mutual_connections(snapshot_text)
                    return mutual_connections
                else:
                    logger.info("No mutual connection link found on the page.")
                    return []


def tool_smart_linkedin_mutual_connections(
    founder_email: str, founder_password: str, vc_linkedin_url: str
) -> list:
    agent = make_agent_introducer_finder()
    return asyncio.run(
        smart_linkedin_mutual_connections(
            founder_email, founder_password, vc_linkedin_url, agent
        )
    )


def make_agent_introducer_finder(model_name="o3-mini"):
    agent = Agent(
        get_openai_model(model_name),
        system_prompt="""
        You are an agent that helps find introductions for founders to VCs.
        Your goal is to log in to LinkedIn using the founder's credentials, open the VC partner's LinkedIn page using the provided URL, go to their connections (or mutual friends if connections is not clickable), and extract the list of mutual connections.

        When logging in, use the following sequence:
        1. Use browser_type with {\"element\": \"textbox 'Email or phone'\", \"text\": <founder_email>}.
        2. Use browser_type with {\"element\": \"textbox 'Password'\", \"text\": <founder_password>}.
        3. Use browser_click with {\"element\": \"button 'Sign in'\"}.
        4. Use browser_wait_for with {\"text\": \"Home\"} or another indicator of successful login.

        If you see a CAPTCHA or error, reply with {done: true, result: 'CAPTCHA or login error encountered'}.

        After each action, you will see a snapshot of the page and must decide the next best action using the available Playwright MCP tools (browser_navigate, browser_type, browser_click, browser_wait_for, browser_snapshot, browser_screen_capture, etc.).
        Always reason about what you see in the snapshot. If you reach the goal, reply with {done: true, result: ...}.
        """,
        deps_type=DrafterDeps,
        retries=3,
        result_type=str,
        tools=[tool_deep_research, tool_smart_linkedin_mutual_connections],
    )
    return agent
