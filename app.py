import asyncio
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp_use import MCPAgent, MCPClient

import logging
logging.basicConfig(level=logging.DEBUG) 

os.environ["LANGCHAIN_VERBOSE"] = "true" # THIS IS KEY FOR DEBUGGING AGENT THOUGHTS
async def run_memory_chat():
    # Load environment variables
    load_dotenv()
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
    config_file= "browser_mcp.json"
    print(".............")
    client = MCPClient.from_config_file(config_file)
    llm = ChatGroq(model="llama-3.3-70b-versatile")
    agent = MCPAgent(llm=llm, client=client,max_steps=15,memory_enabled=True,)
    print("chat")
    print("type 'quit' to exit")
    print("clear")
    print(".............")
    try:
        while True:
            user_input = input("You: ")
            if user_input.lower() == "quit":
                break
            elif user_input.lower() == "clear":
                print(".............")
                continue
            print("Assistant:  ", end="  ",flush=True)
            response = await agent.run(user_input)
            print(f"{response}")
    finally:
        if client and client.sessions:
            await client.close_all_sessions()
if __name__ == "__main__":
    asyncio.run(run_memory_chat())
    
