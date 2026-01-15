import asyncio
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp_use import MCPAgent, MCPClient

CONFIG_FILE = "browser_mcp.json"


async def force_json(llm, text, user_query):
    prompt = f"""
Convert the text below into VALID JSON only.

Rules:
- Output ONLY JSON
- No markdown
- No explanations

Schema:
{{
  "query": "{user_query}",
  "restaurants": [
    {{
      "name": "string",
      "location": "string",
      "matching_items": [],
      "notes": "string"
    }}
  ]
}}

Text:
{text}
"""
    result = llm.invoke(prompt)
    return result.content


async def run_query(query: str):
    load_dotenv()
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

    client = MCPClient.from_config_file(CONFIG_FILE)
    llm = ChatGroq(model="llama-3.1-8b-instant")

    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=15,
        memory_enabled=False
    )

    try:
        raw_response = await agent.run(query)
        json_response = await force_json(llm, raw_response, query)
        return json_response

    finally:
        if client and client.sessions:
            await client.close_all_sessions()
