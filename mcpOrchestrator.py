import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from agentRouter import movie_agent
from finalSummary_tool import summarize_final_answer



APP_NAME = "movie_app"
USER_ID = "user123"
SESSION_ID = "session123"


# In Google ADK, not all events are guaranteed to have: .content, .content.parts, .content.parts[0].text
# This occurs when:the response contains only non-text parts (like thought_signature or function_call) or 
# the ADK agent decides no response is needed or the API call partially fails but still yields an event
async def classify_query_with_adk(runner, user_query: str):
    content = types.Content(role="user", parts=[types.Part(text=user_query)])
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
        if event.is_final_response():
            if event.content and event.content.parts:
                # Extract only text parts
                text_parts = [
                    part.text for part in event.content.parts
                    if hasattr(part, "text") and part.text
                ]
                return "\n".join(text_parts) if text_parts else ""
            else:
                print("Warning: Final response has no content or parts.")
                return ""


# First Entry Point
async def mcp_orchestrator(user_query: str):
    print(f"\nUser Query: {user_query}")

    # Setup session + runner
    # https://google.github.io/adk-docs/tools/#example_1
    session_service = InMemorySessionService()
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=movie_agent, app_name=APP_NAME, session_service=session_service)

    # Run ADK agent → get tool response
    raw_tool_response = await classify_query_with_adk(runner, user_query)
    print(f" Raw Tool Response:\n{raw_tool_response}")                          # response from the first LLM call

    if not raw_tool_response:
        final_answer = "Sorry, no answer was generated."
    else:
        final_answer = await summarize_final_answer(user_query, raw_tool_response)    # 2nd LLM call

    print(f"\n Final Response to User:\n{final_answer}")                        # Display response to the user

    # Return values to FE
    return {
        "user_query": user_query,
        "tool_output": raw_tool_response,
        "final_answer": final_answer
    }  

"""if __name__ == "__main__":
    asyncio.run(mcp_orchestrator("Find movies like The Matrix with more emotion"))      # vector_search tool """


# Starting point
if __name__ == "__main__":
    queries = [
        "Who directed Inception and what is its runtime?",          # cypher_tool --> utilizing agent for cypher query creation 
        "Find movies like The Matrix with more emotion",            # vector_search_tool --> utilizing LLM for text embedding creation
        "What makes The Matrix a culturally significant film?"      # llm_reasoning_tool --> using LLM for open-ended, opinion-based, or conversational Q&A
    ]

    # Execute Queries
    for query in queries:
        print("\n In Main method, Executing Queries")
        asyncio.run(mcp_orchestrator(query))