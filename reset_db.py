import sys
from src.core.database import Base, engine
from src.modules.security.models import *
from src.modules.actors.models import *
from src.modules.emergencies.models import *
from src.modules.operations.models import *
from src.modules.ai.models import *
def reset_db():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database reset complete.")

if __name__ == "__main__":
    reset_db()
