from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from passlib.context import CryptContext


load_dotenv()  # Load .env file
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define User model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    balance = Column(Float, default=0.0)

Base.metadata.create_all(bind=engine)  # Create tables

app = FastAPI()

# Test DB connection
@app.get("/")
def read_root():
    return {"status": "Banking API Online"}

   
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/register")
def register(username: str, password: str):
    db = SessionLocal()
    hashed_password = pwd_context.hash(password)
    db_user = User(username=username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    return {"message": "User created"}

@app.get("/balance/{username}")
def get_balance(username: str):  # ← Aligned with @app
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"balance": user.balance}  


@app.post("/transfer")
def transfer(sender: str, receiver: str, amount: float):
    db = SessionLocal()
    # Atomic transaction
    sender_acc = db.query(User).filter(User.username == sender).first()
    receiver_acc = db.query(User).filter(User.username == receiver).first()
    if not sender_acc or not receiver_acc:
        raise HTTPException(status_code=404, detail="User not found")
    if sender_acc.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    sender_acc.balance -= amount
    receiver_acc.balance += amount
    db.commit()
    return {"message": "Transfer successful"}

    