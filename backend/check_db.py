
import os
from sqlalchemy import create_engine, text

# Assume the script is run from the 'backend' directory
# and the database is in the parent directory as per standard setup.
DATABASE_URL = "sqlite:///../bmad.db"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        print("Successfully connected to the database.")
        
        query = text("SELECT * FROM hitl_requests;")
        
        result = connection.execute(query)
        
        rows = result.fetchall()
        
        if not rows:
            print("No entries found in the hitl_requests table.")
        else:
            print(f"Found {len(rows)} entries in the hitl_requests table:")
            for row in rows:
                print(dict(row._mapping))

except Exception as e:
    print(f"An error occurred: {e}")
