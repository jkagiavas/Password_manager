from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Password(Base):
    __tablename__ = "passwords"

    id = Column(Integer, primary_key=True)
    website = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)

engine = create_engine("sqlite:///passwords.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()