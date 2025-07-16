from fastapi import FastAPI
import asyncio
from fastapi.responses import StreamingResponse # for SSE data streaming incrementally line by line to the frontend.
from pydantic import BaseModel                  # for structured request or response models
from mcpOrchestrator import mcp_orchestrator    # BE
import uvicorn                                  # ASGI server to run FastAPI.

from fastapi.middleware.cors import CORSMiddleware

"""
This file serves as the server.
"""

app = FastAPI()                                 # create Web API

# Adds CORS middleware so a frontend (e.g., instance running on localhost:3000) can call the backend on localhost:8080
app.add_middleware(                             # allows the frontend to call the API across domains
    CORSMiddleware,
    allow_origins=["*"],                        # or ["http://localhost:3000"] - presently allows all origins, need to restrict it later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Defines a data model if we later want to POST queries as JSON. 
# Right now we are not using it (because we use GET with query params), but it’s set up for future flexibility
class QueryRequest(BaseModel):
    query : str

# First endpoint - root endpoint
@app.get("/")
async def root():
    return {"message" : " Movie Agent Server is running"}

# main streaming event
# for SSE events
# Receives a query and passes it on to the mcp_orchestrator(), waits for the result , returns JSON with the final answer
@app.get("/stream")
async def stream(query: str):
    async def event_generator():
        result = await mcp_orchestrator(query)

        # Stream user query
        # yield f"data: User Query: {result['user_query']}\n\n"   # SSE protocol format
        await asyncio.sleep(0.1)                                  # to avoid blocking

        # Stream final answer line by line
        final_answer = result['final_answer']
        for line in final_answer.split('\n'):                   # Split the final answer into lines
            preprocessed_line = line.strip()
            if preprocessed_line:                               # skip empty lines
                yield f"data: {preprocessed_line}\n\n"          # yield each line as an SSE message
            await asyncio.sleep(0.05)                           # to avoid blocking, give control back to the event loop
        
        # Indicates the end of stream
        yield "event: done\ndata: Done\n\n"                     # Send an SSE custom event called done → tells the frontend that the stream has finished
    
    # receive real-time streamed updates
    return StreamingResponse(event_generator(), media_type="text/event-stream") # Wraps event_generator() as an SSE (text/event-stream)

# Run the FastAPI app using uvicorn
if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8080, reload=True)