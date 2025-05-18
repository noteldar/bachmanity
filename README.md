# VC Outreach Workflow on Fetch.ai

This project deploys a LangGraph-based VC outreach workflow on Fetch.ai's uAgents ecosystem.

## Overview

The workflow helps startups connect with VC partners by:
1. Finding the VC partner's email
2. Generating a warm introduction using a mutual connection
3. Drafting a cold email as a fallback

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_key
   FETCH_AI_API_KEY=your_fetch_ai_api_key
   ```

## Deployment

1. Run the agent to deploy the workflow:
   ```
   python fetch_agent.py
   ```
2. Note the agent address printed in the console output - you'll need this for the client.

## Interacting with the Workflow

1. Update the `workflow_agent_address` in `fetch_client.py` with the address from the previous step
2. Run the client:
   ```
   python fetch_client.py
   ```
3. The client will send a test request to the workflow agent and display the results.

## Custom Requests

To send custom requests, modify the `test_query` object in `fetch_client.py` with your startup and VC partner information.

## Local Testing

You can also run the workflow locally (without Fetch.ai) using:
```
python workflow_test.py
```
