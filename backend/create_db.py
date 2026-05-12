from backend.db import engine, Base
import backend.models.db_models  # ensure models are registered


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


if __name__ == "__main__":
    create_tables()
