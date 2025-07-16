import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI

# Load environment variables from .env file.
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Neo4j credentials
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "student123"

# Connect to Neo4j database.
llm = OpenAI(api_key=OPENAI_API_KEY)

# Connects to OpenAI to request text embeddings.
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Function to create embedding
"""
Take a string text 
Send it to OpenAI to get a 1536-dimensional vector.
Returns the vector

"""
def get_embedding(text):
    if not text or text.strip() == "":
        return None
    try:
        response = llm.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding error for text: {text[:50]}... — {e}")
        return None


# Function to create vector index
"""
Create a vector index on the movie_embedding property
This will enable fast vector similarity search using the cosine distance

"""
def create_vector_index():
    with driver.session() as session:
        session.run("""
        CREATE VECTOR INDEX movieEmbeddingIndex
        FOR (m:Movie)
        ON (m.movie_embedding)
        OPTIONS {
            indexConfig: {
                `vector.dimensions`: 1536,
                `vector.similarity_function`: "cosine"
            }
        }
        """)
        print("Vector index created for movie_embedding using new syntax.")


# Process movies, create and store embeddings
"""
Fetches every Movie node ID, overview, and tagline from Neo4j
Join the overview and tagline into one concatenated string
Sends the concatenated string to OpenAI to get an embedding
Updates the Movie node by storing the embedding in a property called movie_embedding

"""
def process_movies():
    with driver.session() as session:
        result = session.run("""
            MATCH (m:Movie)
            RETURN m.id AS id, m.overview AS overview, m.tagline AS tagline
        """)
        
        for record in result:
            movie_id = record["id"]
            overview = record["overview"] or ""
            tagline = record["tagline"] or ""

            combined_text = f"Overview: {overview}\nTagline: {tagline}"
            embedding = get_embedding(combined_text)

            if embedding:
                session.run("""
                    MATCH (m:Movie {id: $id})
                    SET m.movie_embedding = $embedding
                """, {
                    "id": movie_id,
                    "embedding": embedding
                })
                print(f"Stored combined embedding for movie ID: {movie_id}")


# Execute the code
process_movies()
create_vector_index()
driver.close()
print("Combined embedding pipeline complete.")
