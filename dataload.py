import pandas as pd
import json
from neo4j import GraphDatabase

# Configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "student123"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Load CSVs
movies_df = pd.read_csv("data/tmdb_5000_movies.csv")
credits_df = pd.read_csv("data/tmdb_5000_credits.csv")

# Safe JSON loader
def safe_json_load(text):
    try:
        if pd.isna(text):
            return []
        return json.loads(text.replace("'", '"'))
    except Exception:
        return []

# Create constraints and indexes
def create_constraints_and_indexes():
    with driver.session() as session:
        statements = [
            # Constraints
            "CREATE CONSTRAINT movie_id_unique IF NOT EXISTS FOR (m:Movie) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",

            # Indexes
            "CREATE INDEX genre_name_index IF NOT EXISTS FOR (g:Genre) ON (g.name)",
            "CREATE INDEX keyword_name_index IF NOT EXISTS FOR (k:Keyword) ON (k.name)",
            "CREATE INDEX company_name_index IF NOT EXISTS FOR (c:Company) ON (c.name)",
            "CREATE INDEX country_code_index IF NOT EXISTS FOR (c:Country) ON (c.iso_3166_1)",
            "CREATE INDEX language_code_index IF NOT EXISTS FOR (l:Language) ON (l.iso_639_1)"
        ]
        for stmt in statements:
            session.run(stmt)
        print("Indexes and constraints created.")

# Load data into Neo4j
def run_queries():
    with driver.session() as session:
        for _, row in movies_df.iterrows():
            movie = {
                "id": str(row["id"]),
                "title": row["title"],
                "original_language": row["original_language"],
                "release_date": row["release_date"],
                "runtime": float(row["runtime"]) if pd.notnull(row["runtime"]) else None,
                "vote_average": float(row["vote_average"]),
                "vote_count": int(row["vote_count"]),
                "popularity": float(row["popularity"]),
                "budget": float(row["budget"]),
                "revenue": float(row["revenue"]),
                "status": row["status"],
                "overview": row["overview"],
                "tagline": row["tagline"],
                "homepage": row["homepage"]
            }

            session.run("MERGE (m:Movie {id: $id}) SET m += $props", id=movie["id"], props=movie)

            for genre in safe_json_load(row["genres"]):
                session.run("MERGE (g:Genre {name: $name})", name=genre["name"])
                session.run("MATCH (m:Movie {id: $mid}), (g:Genre {name: $name}) MERGE (m)-[:IN_GENRE]->(g)", mid=movie["id"], name=genre["name"])

            for keyword in safe_json_load(row["keywords"]):
                session.run("MERGE (k:Keyword {name: $name})", name=keyword["name"])
                session.run("MATCH (m:Movie {id: $mid}), (k:Keyword {name: $name}) MERGE (m)-[:HAS_KEYWORD]->(k)", mid=movie["id"], name=keyword["name"])

            for company in safe_json_load(row["production_companies"]):
                session.run("MERGE (c:Company {name: $name})", name=company["name"])
                session.run("MATCH (m:Movie {id: $mid}), (c:Company {name: $name}) MERGE (m)-[:PRODUCED_BY]->(c)", mid=movie["id"], name=company["name"])

            for country in safe_json_load(row["production_countries"]):
                session.run("MERGE (c:Country {iso_3166_1: $code, name: $name})", code=country["iso_3166_1"], name=country["name"])
                session.run("MATCH (m:Movie {id: $mid}), (c:Country {iso_3166_1: $code}) MERGE (m)-[:RELEASED_IN_COUNTRY]->(c)", mid=movie["id"], code=country["iso_3166_1"])

            for lang in safe_json_load(row["spoken_languages"]):
                session.run("MERGE (l:Language {iso_639_1: $code, name: $name})", code=lang["iso_639_1"], name=lang["name"])
                session.run("MATCH (m:Movie {id: $mid}), (l:Language {iso_639_1: $code}) MERGE (m)-[:SPOKEN_IN_LANGUAGE]->(l)", mid=movie["id"], code=lang["iso_639_1"])

        for _, row in credits_df.iterrows():
            movie_id = str(row["movie_id"])

            for person in safe_json_load(row["cast"]):
                session.run("MERGE (p:Person {id: $id}) SET p.name = $name, p.gender = $gender", id=str(person["id"]), name=person["name"], gender=person["gender"])
                session.run("MATCH (p:Person {id: $pid}), (m:Movie {id: $mid}) MERGE (p)-[:ACTED_IN {character: $char}]->(m)", pid=str(person["id"]), mid=movie_id, char=person["character"])

            for person in safe_json_load(row["crew"]):
                session.run("MERGE (p:Person {id: $id}) SET p.name = $name, p.gender = $gender, p.job = $job", id=str(person["id"]), name=person["name"], gender=person["gender"], job=person["job"])
                if person["job"].lower() == "director":
                    session.run("MATCH (p:Person {id: $pid}), (m:Movie {id: $mid}) MERGE (p)-[:DIRECTED]->(m)", pid=str(person["id"]), mid=movie_id)
                else:
                    session.run("MATCH (p:Person {id: $pid}), (m:Movie {id: $mid}) MERGE (p)-[:CREW_ROLE {job: $job}]->(m)", pid=str(person["id"]), mid=movie_id, job=person["job"])

# Run everything
create_constraints_and_indexes()
run_queries()
driver.close()
print("All data loaded successfully into Neo4j.")
