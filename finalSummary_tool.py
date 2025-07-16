import asyncio
import os
#from openai import OpenAI
from openai import AsyncOpenAI
from dotenv import load_dotenv
import json

"""
Functionality:

    This class is used to make the second call to the LLM after mcpOrchestrator.py receives the decision from the agent about tool choice and tool output
    Summarizes the final answer using OpenAI GPT-4 and returns a string to the mcpOrchestrator()
    
"""

load_dotenv()
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# The second LLM call happens in this method:
async def summarize_final_answer(user_query: str, tool_output) -> str:
    
    # Prepare the conversation messages for GPT-4
    messages = [
        {"role": "system", "content": "You are a helpful assistant that summarizes tool outputs into natural language answers for the user."},
        {"role": "user", "content": f"User query: {user_query} \n\n Tool output: {tool_output} \n\n Please utilize the tool output to answer the user query."}
    ]

    try:
        # Execute the second LLM call
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )

        # Extract and return summarized content
        if response.choices:
            final_summary = response.choices[0].message.content
            return final_summary
        else:
            final_summary = "Sorry, no response generated."
            return final_summary

    except Exception as e:
        print(f"Error during 2nd LLM call: {e}")
        return "Sorry, I was unable to generate a summarized answer at this time."


    