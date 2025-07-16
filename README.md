# Movie Agent Chat System

The Movie Agent Chat System is an intelligent conversational application that helps users explore movies through natural language queries.

It combines the power of a Neo4j graph database, OpenAI embeddings + GPT-4, Google ADK (Gemini-2.5) and MCP Orchestration pattern to answer:
    - Factual questions (e.g., directors, runtime, genres)
    - Recommendation queries (e.g., “find movies like The Matrix”)
    - Open-ended discussions (e.g., “why is The Matrix culturally significant?”)

The system is designed as an end-to-end pipeline with:
    - A frontend chat interface (HTML + JS)
    - A FastAPI backend that streams responses using SSE
    - A Google ADK agent that routes queries to specialized backend tools
    - Precomputed text embeddings + vector search for semantic recommendations
    - GPT-4 summarization to generate clear, human-readable answers

The system follows an MCP-style (Multi-Component Protocol) orchestration pattern, where an agent dynamically routes incoming user queries to one of several backend tools based on query type and intent, and then summarizes the output into a final user-facing answer.

The result is a seamless user experience where queries are intelligently understood, processed, and answered in real time thereby combining structured graph data with cutting-edge LLM capabilities.


## Key technologies:

1. Neo4j Graph Database + Vector Index
2. OpenAI Embeddings & GPT-4
3. Google ADK (Agent Development Kit) with Gemini
4. FastAPI backend with Server-Sent Events (SSE)
5. Lightweight frontend (HTML + JS)



## Flow Diagram:

User (Web Browser) ──▶ Frontend (HTML + JS - index.html)
                            │
                            ▼
                FastAPI Backend (server.py -> event_generator())
                            │
                            ▼
        mcp_orchestrator() [Runs the agent pipeline - mcpOrchestrator.py]  
                            │
                            ▼
            ┌───────────────────────────────────────────────┐
            │ Google ADK Runner + movie_agent (Gemini-2.5)  │
            └───────────────────────────────────────────────┘
                                │
         ┌──────────────────────┼───────────────────────────┐
         │                      │                           │
         ▼                      ▼                           ▼
 [Tool 1] cypher_tool    [Tool 2] vector_search_tool    [Tool 3] llm_reasoning_tool
        │                       │                           │
 Neo4j Async DB          OpenAI embedding + Neo4j     OpenAI GPT-4 (chat/completion)
  (Cypher query)           vector index search          (general reasoning)
                                │
                                ▼
          ───────────────────────────────────────────────
            Tool output (raw results, e.g., dict/json)
                            │
                            ▼
        summarize_final_answer() [Second OpenAI GPT-4 call - finalSummary_tool.py]
          (Summarizes tool outputs into natural language)
                            │
                            ▼
                Final summarized answer (string) [returned to event_generator() in server.py]
                            │
                            ▼
                FastAPI StreamingResponse (SSE) [FastAPI streams the final answer back to the frontend]
                            │
                            ▼
            Frontend displays agent responses line by line


## Request + Response Flow
1. User inputs query → in frontend (HTML + JS chat app).
2. Frontend sends GET request → FastAPI backend at (/stream?query=....)
3. FastAPI (server.py) triggers mcp_orchestrator(query).
4. mcp_orchestrator() flow:
        Initializes Google ADK session + runner.
        Calls Gemini (movie_agent) to analyze user query.
        Gemini agent selects and runs one of:
            cypher_tool → queries Neo4j (facts, graph data).
            vector_search_tool → gets OpenAI embedding, runs Neo4j vector search (recommendations).
            llm_reasoning_tool → queries OpenAI GPT-4 (open-ended reasoning).
5. Receives raw tool result (structured JSON/dict).
6. Passes result to summarize_final_answer() → uses GPT-4 to turn tool output + query into a natural-language answer.
7. Final summarized answer streamed back via FastAPI SSE (StreamingResponse), line by line.
8. Frontend receives and displays response in chat interface.


## List of Files and Their Functionalities:
1. dataload.py

    Purpose: Load dataset to the Neo4j Graph Database 

    Functions / Logic:
    - Reads tmdb_5000_movies.csv and tmdb_5000_credits.csv using pandas.
    - Parses nested JSON fields safely (genres, keywords, companies, etc.).
    - Inserts:
        - Movie nodes and properties.
        - Genre, Keyword, Company, Country, Language nodes.
        - Person nodes (cast, crew) and relationships like: ACTED_IN, DIRECTED, CREW_ROLE.
        - Creates constraints + indexes on key properties.

2. textEmbeddingGeneration.py

    Purpose: Precompute semantic embeddings for movies, enabling vector search later

    Functions / Logic:
    - get_embedding(text): Sends overview + tagline to OpenAI (text-embedding-ada-002), gets a 1536-dim embedding.
    - process_movies(): Loops through all movies in Neo4j, generates combined embeddings, and stores them as movie_embedding property.
    - create_vector_index(): Creates Neo4j vector index on movie_embedding for fast similarity search.

3. agentRouter.py

    Purpose: Define an agent and routes incoming queries to the right tool

    Functions / Logic:
    - movie_agent:
        - Google ADK LlmAgent using Gemini (gemini-2.5-flash).
        - Instruction-guided routing of queries to backend tools.
    - Wrapped tools:
        - cypher_function_tool → wraps cypher_tool().
        - vector_function_tool → wraps vector_search_tool().
        - llm_function_tool → wraps llm_reasoning_tool().

4. movie_tools.py

    Purpose: Contains the tool call implementations
    
    Functions / Logic:
    - cypher_tool(query): Runs Cypher query in Neo4j (async).
    - vector_search_tool(query, top_k): Gets query embedding (OpenAI), runs Neo4j vector similarity search, returns top matches.    
    - llm_reasoning_tool(query): Sends query to GPT-4 (OpenAI) for conversational or open-ended reasoning.

5. mcpOrchestrator.py

    Purpose: Runs the MCP pipeline

    Functions / Logic:
    - mcp_orchestrator(user_query):
        Sets up ADK session.
        Runs agent (movie_agent).
        Collects raw tool output.
        Calls summarize_final_answer() to generate summarized human-readable answer.
        Returns result.

6. finalSummary_tool.py

    Purpose: Make a second LLM call to present a domain specific formatted answer based on the raw output from the tool call

    Functions / Logic:
    - summarize_final_answer(user_query, tool_output):
    - Calls GPT-4 with system prompt + context.
    - Returns summarized final answer.

7. server.py

    Purpose: Create a Backend API

    Endpoints:
    - /: Root endpoint.
    - /stream: Receives query, calls mcp_orchestrator(), streams final answer line by line to frontend using Server-Sent Events (SSE).

8. index.html

    Purpose: Create a chat interface 

    Logic:
    - User input box + send button.
    - Connects to /stream SSE endpoint.
    - Receives and displays streaming lines from the backend.


## Instructions to run the Movie Agent System:
1. Clone Repository:
    git clone <your-repo-url>
    cd <your-repo-folder>

2. Install Python dependencies: 
    python -m venv venv
    on MAC: source venv/bin/activate   
    on Windows: venv\Scripts\activate
    pip install -r requirements.txt

3. Install Neo4j Desktop or run Neo4j locally:
    URI: bolt://localhost:7687
    Username: ****** (update in .env)
    Password: ********** (update in .env)
    Create an empty database called (for example :MoviesDataset)

4. Configure environment variables:
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=*****
    NEO4J_PASSWORD=******
    OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
    GOOGLE_API_KEY=************

5. Run this in the terminal:
    python dataload.py
    python textEmbeddingGeneration.py
    python server.py
        - This will start FastAPI on http://localhost:8080 and expose /stream endpoint with Server-Sent Events (SSE) for the frontend.
    python -m http.server 3000
        - This will start the FE on : http://localhost:3000/index.html

6. Try queries like:
    Who directed Inception and what is its runtime?
    Find movies like The Matrix with more emotion.
    What makes The Matrix a culturally significant film?