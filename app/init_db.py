from app.database import create_db_and_tables
import app.models  # noqa: F401  — registers all models

if __name__ == "__main__":
    create_db_and_tables()
    print("Tables created.")