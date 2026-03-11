from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# Base is the foundation class that all database models inherit from
# It keeps track of all tables we define
Base = declarative_base()

class Password(Base):
    # This class represents a single table in the database called "passwords"
    # Each attribute with Column() becomes a column in the table
    __tablename__ = "passwords"

    id = Column(Integer, primary_key=True)  # Auto-incremented unique ID for each row
    website = Column(String, nullable=False)  # Website name - cannot be empty
    email = Column(String, nullable=False)    # Email/username - cannot be empty
    password = Column(String, nullable=False) # Encrypted password - cannot be empty

# create_engine() sets up the connection to the database
# sqlite:///passwords.db means a local SQLite file called passwords.db
engine = create_engine("sqlite:///passwords.db")

# create_all() creates the actual tables in the database if they don't exist yet
# Safe to run every time - it won't overwrite existing tables
Base.metadata.create_all(engine)

# Session is the interface we use to add, query, and commit data
# Think of it like a staging area between your code and the database
Session = sessionmaker(bind=engine)
session = Session()