import asyncio
import uuid
import os
from dotenv import load_dotenv
#from neo4j import GraphDatabase
from neo4j import AsyncGraphDatabase
#from openai import OpenAI
from openai import AsyncOpenAI

load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
# openai_client = OpenAI(api_key=OPENAI_API_KEY)

driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# https://google.github.io/adk-docs/tools/#example

# Function Tools: Functions/Methods: Define standard synchronous functions or methods in your code (e.g., Python def).
# Takes the query string passed by the agent , runs it using the Neo4j driver.session() and returns a dictionary
# for this tool --> a cypher tool is not necessary --> the agent converts the user query into the necessary cypher and passes it to the tool
async def cypher_tool(query: str) -> dict:
    print("cypher_tool has been selected by the agent")
    async with driver.session() as session:
        result = await session.run(query)
        records = [record async for record in result]
        return {"result": [record.data() for record in records]}

# Function Tools: Functions/Methods: Define standard synchronous functions or methods in your code (e.g., Python def).
async def vector_search_tool(query: str, top_k: int) -> dict:
    print("vector_search_tool has been selected by the agent")
    top_k = 5
    try:
        # Generate embedding for the user query
        embedding_response = await openai_client.embeddings.create(
            input=query, model="text-embedding-ada-002"
        )
        embedding = embedding_response.data[0].embedding
        if not embedding or len(embedding) != 1536:
            raise ValueError("Invalid embedding received from OpenAI")
        print(f"Generated embedding with {len(embedding)} dimensions")

        # Run vector search in Neo4j database
        async with driver.session() as session:
            cypher = """
            CALL db.index.vector.queryNodes('movieEmbeddingIndex', $top_k, $embedding)
            YIELD node, score
            RETURN node.title AS title, node.overview AS overview, score
            """
            result = await session.run(cypher, {"embedding": embedding, "top_k": top_k})

            records = [record.data() for record in result]
            if not records:
                return {
                    "status": "no_results",
                    "message": "No similar movies found"
                }

            return {
                "status": "success",
                "count": len(records),
                "result": records
            }

    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }

# Function Tools: Agents-as-Tools: Use another, potentially specialized, agent as a tool for a parent agent.
async def llm_reasoning_tool(query: str) -> dict:
    print("llm_reasoning_tool has been selected by the agent")
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": query}]
        )

        # Safely extract the first message content
        if response.choices and len(response.choices) > 0:
            message_content = response.choices[0].message.content.strip()
        else:
            message_content = ""

        return {
            "status": "success",
            "model": "gpt-4",
            "result": message_content
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }
