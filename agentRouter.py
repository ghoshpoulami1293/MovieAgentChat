from google.adk.agents import LlmAgent
from google.adk import Agent
from google.adk.tools import FunctionTool
from google.genai import types
from movie_tools import cypher_tool, vector_search_tool, llm_reasoning_tool


MODEL_ID = "gemini-2.5-flash"

# Wrap tools as FunctionTool
#https://google.github.io/adk-docs/tools/#how-agents-use-tools
cypher_function_tool = FunctionTool(func=cypher_tool)
vector_function_tool = FunctionTool(func=vector_search_tool)
llm_function_tool = FunctionTool(func=llm_reasoning_tool)


# Define ADK Agent 
# https://google.github.io/adk-docs/agents/llm-agents/#guiding-the-agent-instructions-instruction
# The agent uses Google ADK + Gemini (gemini-2.5-flash) to route queries
# generate_content_config (Optional): Pass an instance of google.genai.types.GenerateContentConfig to control parameters like temperature (randomness), max_output_tokens (response length), top_p, top_k, and safety settings.
movie_agent = LlmAgent(
    model=MODEL_ID,
    name="movie_agent",
    description ="Answers user questions about movies",
    instruction="""
    You are a helpful assistant for answering movie-related questions.
    Use 'cypher_tool' to answer factual database queries (directors, actors, runtime, etc).
    Use 'vector_search_tool' for semantic or similarity recommendations.
    Use 'llm_reasoning_tool' for open-ended or conversational queries if you cannot answer the questions using the 'cypher_tool' or 'llm_reasoning_tool'.

    You are querying a Neo4j graph with the following structure:
    - Nodes:
        - Movie:
            - Properties: id, title, original_language, release_date, runtime, vote_average, vote_count, popularity, budget, revenue, status, overview, tagline, homepage, movie_embedding
        - Person:
            - Properties: id, name, gender, job
        - Genre:
            - Properties: name
        - Keyword:
            - Properties: name
        - Company:
            - Properties: name
        - Country:
            - Properties: iso_3166_1, name
        - Language:
            - Properties: iso_639_1, name

    - Relationships:
        - (:Movie)-[:IN_GENRE]->(:Genre)
        - (:Movie)-[:HAS_KEYWORD]->(:Keyword)
        - (:Movie)-[:PRODUCED_BY]->(:Company)
        - (:Movie)-[:RELEASED_IN_COUNTRY]->(:Country)
        - (:Movie)-[:SPOKEN_IN_LANGUAGE]->(:Language)
        - (:Person)-[:ACTED_IN]->(:Movie) with 'character' property
        - (:Person)-[:DIRECTED]->(:Movie)
        - (:Person)-[:CREW_ROLE]->(:Movie) with 'job' property
    """,
    tools=[cypher_function_tool, vector_function_tool, llm_function_tool],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2, # to get a more deterministic output
        max_output_tokens=1000
    )
)