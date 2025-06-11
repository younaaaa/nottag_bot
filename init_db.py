from database import engine, Base
# Import all models from the models package to ensure they are registered with Base.metadata
# The __init__.py in the models directory should handle making them available.
import models # This will trigger models/__init__.py

def initialize_database():
    print("Initializing database...")
    # Create all tables in the database engine.
    # This will only create tables that do not already exist.
    Base.metadata.create_all(engine)
    print("Database initialized successfully (tables created if they didn't exist).")

if __name__ == "__main__":
    # This allows running the script directly to initialize the database.
    # Make sure your .env file is set up with DB_URL before running this.
    # You might need to run this from a context where PYTHONPATH is set correctly
    # if you have issues with imports, e.g., python -m init_db

    # Load environment variables, especially DB_URL from .env
    # This is important if running this script standalone.
    from dotenv import load_dotenv
    load_dotenv()

    initialize_database()
